import json
import re
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from collections import defaultdict
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import StandardScaler
import hdbscan
import warnings

warnings.filterwarnings('ignore')


class TextCleaner:
    """Очистка текста"""

    @staticmethod
    def clean_text(text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = text.lower()
        text = re.sub(r'[^а-яёa-z\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        words = [w for w in text.split() if len(w) >= 3]
        return ' '.join(words)


class ServiceSplitterML:
    def __init__(self):
        print("🔄 Загрузка модели SentenceTransformer...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.scaler = StandardScaler()
        self.cleaner = TextCleaner()
        print("✓ Модель загружена")

        # Маркеры для определения самостоятельности
        self.independence_markers = [
            r'отдельн[а-я]+',
            r'также\s+(?:выполняем|делаем|предлагаем)',
            r'можно\s+заказать\s+отдельно',
            r'(?:выполняем|делаем)\s+[^.]*?\s+отдельно',
        ]

    def preprocess_data(self, ads_data: List[Dict]) -> pd.DataFrame:
        """Предобработка данных"""
        print("🔧 Предобработка...")
        df = pd.DataFrame(ads_data)
        df['clean_text'] = df['description'].apply(self.cleaner.clean_text)
        df = df[df['clean_text'].str.len() > 10].copy()
        print(f"✓ Осталось {len(df)} объявлений")
        return df

    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Создание эмбеддингов"""
        print(f"🧮 Создание эмбеддингов для {len(texts)} текстов...")
        return self.model.encode(texts, show_progress_bar=True)

    def cluster_texts(self, embeddings: np.ndarray, group_size: int) -> Tuple[np.ndarray, Dict]:
        """Кластеризация с рекомендованными параметрами"""
        normalized = self.scaler.fit_transform(embeddings)

        # Если группа маленькая - не кластеризуем
        if group_size < 25:
            return np.zeros(len(embeddings)), {'n_clusters': 1, 'noise_ratio': 0}

        # Параметры по рекомендациям
        min_cluster_size = max(8, min(40, round(0.03 * group_size)))
        min_samples = max(3, round(0.4 * min_cluster_size))

        print(f"   Параметры: min_cluster_size={min_cluster_size}, min_samples={min_samples}")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean',
            cluster_selection_epsilon=0.1
        )

        labels = clusterer.fit_predict(normalized)

        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_ratio = np.sum(labels == -1) / len(labels)

        return labels, {'n_clusters': n_clusters, 'noise_ratio': noise_ratio}

    def should_split(self, text: str, group_size: int, labels: np.ndarray, stats: Dict) -> bool:
        """Определение необходимости разделения"""
        n_clusters = stats['n_clusters']
        noise_ratio = stats['noise_ratio']

        # Базовое правило
        if group_size < 25:
            return False
        if n_clusters < 2:
            return False
        if noise_ratio > 0.55:
            return False

        # Проверяем маркеры в тексте
        text_lower = text.lower()
        has_independence = any(re.search(m, text_lower) for m in self.independence_markers)

        # Если есть маркеры самостоятельности - повышаем шанс разделения
        if has_independence:
            return True

        # Если нет явных маркеров, но кластеры четкие - тоже разделяем
        return (n_clusters >= 2 and noise_ratio <= 0.4)

    def process_dataset(self, ads_data: List[Dict]) -> List[Dict]:
        """Обработка всего датасета"""
        print("\n" + "=" * 60)
        print("ОБРАБОТКА ДАТАСЕТА (ML с эмбеддингами)")
        print("=" * 60)

        # Предобработка
        df = self.preprocess_data(ads_data)

        # Группируем по sourceMcTitle
        groups = df.groupby('sourceMcTitle')
        print(f"\n📊 Найдено {len(groups)} категорий")

        all_results = []

        for mcTitle, group_df in groups:
            print(f"\n🔍 Категория: {mcTitle} ({len(group_df)} объявлений)")

            # Создаем эмбеддинги
            texts = group_df['clean_text'].tolist()
            embeddings = self.create_embeddings(texts)

            # Кластеризуем
            labels, stats = self.cluster_texts(embeddings, len(group_df))
            group_df['cluster'] = labels

            print(f"   Найдено кластеров: {stats['n_clusters']}, шум: {stats['noise_ratio']:.1%}")

            # Анализируем каждый кластер
            for cluster_id in set(labels):
                if cluster_id == -1:
                    continue

                cluster_df = group_df[group_df['cluster'] == cluster_id]
                cluster_size = len(cluster_df)

                # Считаем долю объявлений с shouldSplit=True в этом кластере
                if 'shouldSplit' in cluster_df.columns:
                    split_ratio = cluster_df['shouldSplit'].mean()
                else:
                    split_ratio = 0

                # Показываем только кластеры с признаками разделения или размером > 10
                if split_ratio > 0 or cluster_size > 10:
                    print(f"   Кластер {cluster_id}: {cluster_size} объявлений, доля разделения: {split_ratio:.1%}")

            # Применяем shouldSplit к каждому объявлению
            for idx, row in group_df.iterrows():
                should_split = self.should_split(
                    row['description'],
                    len(group_df),
                    labels,
                    stats
                )

                result = {
                    'itemId': row['itemId'],
                    'sourceMcId': row['sourceMcId'],
                    'sourceMcTitle': row['sourceMcTitle'],
                    'description': row['description'],
                    'detectedMcIds': [],
                    'shouldSplit': should_split,
                    'drafts': [],
                    'cluster_id': int(row['cluster']) if row['cluster'] != -1 else -1
                }

                # Если нужно разделить - создаем черновик
                if should_split and row['cluster'] != -1:
                    # Находим другие mcId в этом кластере
                    cluster_df = group_df[group_df['cluster'] == row['cluster']]
                    other_mcIds = cluster_df[cluster_df['sourceMcId'] != row['sourceMcId']]['sourceMcId'].unique()

                    for other_mcId in other_mcIds[:2]:  # Не больше 2 черновиков
                        other_mcTitle = cluster_df[cluster_df['sourceMcId'] == other_mcId]['sourceMcTitle'].iloc[0]
                        result['detectedMcIds'].append(int(other_mcId))
                        result['drafts'].append({
                            'mcId': int(other_mcId),
                            'mcTitle': other_mcTitle,
                            'text': f"Выполняю отдельно: {other_mcTitle}. {row['description'][:200]}"
                        })

                all_results.append(result)

        return all_results

    def evaluate(self, predictions: List[Dict], ground_truth: List[Dict]) -> Dict:
        """Оценка качества"""
        gt_dict = {item['itemId']: item for item in ground_truth}

        correct = 0
        total = 0
        tp = fp = fn = 0

        for pred in predictions:
            itemId = str(pred['itemId'])
            if itemId in gt_dict:
                gt = gt_dict[itemId]
                total += 1

                pred_split = pred['shouldSplit']
                true_split = gt.get('shouldSplit', False)

                if pred_split == true_split:
                    correct += 1

                if pred_split and true_split:
                    tp += 1
                elif pred_split and not true_split:
                    fp += 1
                elif not pred_split and true_split:
                    fn += 1

        accuracy = correct / total if total > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp, 'fp': fp, 'fn': fn,
            'total': total
        }


def main():
    print("=" * 60)
    print("СИСТЕМА АНАЛИЗА ОБЪЯВЛЕНИЙ (ML с эмбеддингами)")
    print("=" * 60)

    filename = input("\nВведите имя файла с датасетом: ")

    # Загрузка
    with open(filename, 'r', encoding='utf-8') as f:
        ads_data = json.load(f)
    print(f"✓ Загружено {len(ads_data)} объявлений")

    # Обработка
    splitter = ServiceSplitterML()
    results = splitter.process_dataset(ads_data)

    # Сохранение
    with open('ml_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Результаты сохранены в ml_results.json")

    # Оценка
    metrics = splitter.evaluate(results, ads_data)
    print("\n" + "=" * 60)
    print("МЕТРИКИ КАЧЕСТВА")
    print("=" * 60)
    print(f"Accuracy:  {metrics['accuracy']:.2%}")
    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall:    {metrics['recall']:.2%}")
    print(f"F1-score:  {metrics['f1']:.2%}")
    print(f"\nTP: {metrics['tp']}, FP: {metrics['fp']}, FN: {metrics['fn']}")

    # Статистика
    split_count = sum(1 for r in results if r['shouldSplit'])
    print(f"\n📈 Предсказано разделений: {split_count} из {len(results)} ({split_count / len(results):.1%})")


if __name__ == "__main__":
    main()