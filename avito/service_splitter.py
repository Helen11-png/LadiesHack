import json
import re
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import HDBSCAN
from collections import defaultdict
import warnings

warnings.filterwarnings('ignore')


class TextCleaner:
    """Очистка текста объявлений"""

    @staticmethod
    def clean_text(text: str) -> str:
        if not isinstance(text, str):
            return ""

        # Приводим к нижнему регистру
        text = text.lower()

        # Удаляем специальные символы и цифры (но оставляем буквы и пробелы)
        text = re.sub(r'[^а-яёa-z\s]', ' ', text)

        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()

        # Удаляем короткие слова (менее 3 букв)
        words = text.split()
        words = [w for w in words if len(w) >= 3]

        return ' '.join(words)


class ServiceSplitterML:
    """ML-подход с эмбеддингами и кластеризацией"""

    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """Инициализация модели"""
        print(f"🔄 Загрузка модели {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.scaler = StandardScaler()
        self.cleaner = TextCleaner()
        print("✓ Модель загружена")

        # Маркеры для shouldSplit
        self.independence_markers = [
            r'отдельн[а-я]+',
            r'также\s+(?:выполняем|делаем|предлагаем|могу)',
            r'можно\s+заказать\s+отдельно',
            r'(?:выполняем|делаем)\s+[^.]*?\s+отдельно',
        ]

        self.complex_markers = [
            r'в\s+том\s+числе',
            r'включая',
            r'в\s+состав[а-я]+',
            r'комплексн[а-я]+',
            r'под\s+ключ',
        ]

    def preprocess_data(self, ads_data: List[Dict]) -> pd.DataFrame:
        """Предобработка данных"""
        print("🔧 Предобработка данных...")

        df = pd.DataFrame(ads_data)

        # Очистка текста
        df['clean_text'] = df['description'].apply(self.cleaner.clean_text)

        # Удаляем пустые тексты
        df = df[df['clean_text'].str.len() > 10].copy()

        print(f"✓ Осталось {len(df)} объявлений после очистки")

        return df

    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Создание эмбеддингов"""
        print(f"🧮 Создание эмбеддингов для {len(texts)} текстов...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings

    def cluster_texts(self, embeddings: np.ndarray, group_size: int) -> Tuple[np.ndarray, Dict]:
        """
        Кластеризация текстов с рекомендованными параметрами
        """
        # Нормализация эмбеддингов
        normalized_embeddings = self.scaler.fit_transform(embeddings)

        # Расчет параметров кластеризации
        if group_size < 25:
            # Маленькие группы не делим
            return np.zeros(len(embeddings)), {'n_clusters': 1, 'noise_ratio': 0}

        min_cluster_size = max(8, min(40, round(0.03 * group_size)))
        min_samples = max(3, round(0.4 * min_cluster_size))

        print(f"   Параметры кластеризации: min_cluster_size={min_cluster_size}, min_samples={min_samples}")

        # Кластеризация
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean',
            cluster_selection_epsilon=0.1
        )

        labels = clusterer.fit_predict(normalized_embeddings)

        # Статистика кластеров
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_ratio = np.sum(labels == -1) / len(labels)

        stats = {
            'n_clusters': n_clusters,
            'noise_ratio': noise_ratio,
            'min_cluster_size': min_cluster_size,
            'min_samples': min_samples
        }

        return labels, stats

    def extract_microcategories_from_clusters(self, df_group: pd.DataFrame, labels: np.ndarray) -> Dict[int, List[int]]:
        """
        Извлечение микрокатегорий для каждого кластера
        """
        cluster_to_mcIds = defaultdict(set)

        for idx, label in enumerate(labels):
            if label != -1:  # Не шум
                mcId = df_group.iloc[idx]['sourceMcId']
                cluster_to_mcIds[label].add(mcId)

        return {k: list(v) for k, v in cluster_to_mcIds.items()}

    def check_independence_markers(self, text: str) -> float:
        """Проверка маркеров самостоятельности"""
        if not text:
            return 0.0

        text_lower = text.lower()
        score = 0.0

        # Проверяем маркеры самостоятельности
        if any(re.search(marker, text_lower) for marker in self.independence_markers):
            score += 0.3

        # Проверяем маркеры комплексности
        if any(re.search(marker, text_lower) for marker in self.complex_markers):
            score -= 0.2

        return max(0.0, min(1.0, score))

    def should_split_group(self, df_group: pd.DataFrame, labels: np.ndarray, stats: Dict) -> Tuple[bool, Dict]:
        """
        Определение необходимости разделения для группы
        """
        n_clusters = stats['n_clusters']
        noise_ratio = stats['noise_ratio']

        # Базовое правило: >= 2 кластера и шум <= 0.55
        should_split = (n_clusters >= 2) and (noise_ratio <= 0.55)

        result = {
            'should_split': should_split,
            'n_clusters': n_clusters,
            'noise_ratio': noise_ratio,
            'group_size': len(df_group),
            'reason': ''
        }

        if len(df_group) < 25:
            result['reason'] = 'Группа слишком маленькая (< 25)'
            result['should_split'] = False
        elif n_clusters < 2:
            result['reason'] = 'Недостаточно кластеров'
            result['should_split'] = False
        elif noise_ratio > 0.55:
            result['reason'] = f'Слишком много шума ({noise_ratio:.2f})'
            result['should_split'] = False
        elif should_split:
            result['reason'] = f'Найдено {n_clusters} кластеров'

        return should_split, result

    def generate_draft_for_cluster(self, df_cluster: pd.DataFrame, mcId: int, mcTitle: str) -> str:
        """
        Генерация текста черновика на основе кластера
        """
        # Берем самые репрезентативные тексты из кластера
        texts = df_cluster['description'].tolist()[:5]

        if texts:
            # Берем первое предложение из первого текста как основу
            first_text = texts[0]
            sentences = re.split(r'[.!?]+', first_text)
            base_text = sentences[0] if sentences else first_text[:100]

            return f"{base_text}. Выполняю как отдельную услугу: {mcTitle.lower()}."
        else:
            return f"Оказываю услуги по направлению: {mcTitle.lower()}."

    def process_dataset(self, ads_data: List[Dict]) -> List[Dict]:
        """
        Обработка всего датасета
        """
        print("\n" + "=" * 60)
        print("ОБРАБОТКА ДАТАСЕТА (ML-подход)")
        print("=" * 60)

        # 1. Предобработка
        df = self.preprocess_data(ads_data)

        # 2. Группировка по sourceMcTitle
        groups = df.groupby('sourceMcTitle')
        print(f"\n📊 Найдено {len(groups)} групп по категориям")

        all_results = []

        for mcTitle, group_df in groups:
            print(f"\n🔍 Обработка категории: {mcTitle} ({len(group_df)} объявлений)")

            # 3. Создание эмбеддингов
            texts = group_df['clean_text'].tolist()
            embeddings = self.create_embeddings(texts)

            # 4. Кластеризация
            labels, stats = self.cluster_texts(embeddings, len(group_df))

            # 5. Определение shouldSplit
            should_split, split_info = self.should_split_group(group_df, labels, stats)

            print(f"   Кластеров: {stats['n_clusters']}, шум: {stats['noise_ratio']:.2%}")
            print(f"   Решение: {'РАЗДЕЛЯТЬ' if should_split else 'НЕ РАЗДЕЛЯТЬ'} - {split_info['reason']}")

            # 6. Создание черновиков если нужно
            group_df['cluster'] = labels

            if should_split:
                # Получаем микрокатегории для каждого кластера
                cluster_mcIds = self.extract_microcategories_from_clusters(group_df, labels)

                for cluster_id, mcIds in cluster_mcIds.items():
                    if cluster_id != -1:  # Не шум
                        cluster_df = group_df[group_df['cluster'] == cluster_id]

                        # Для каждого mcId в кластере создаем черновик
                        for mcId in mcIds[:3]:  # Не более 3 черновиков на кластер
                            mcTitle = cluster_df[cluster_df['sourceMcId'] == mcId]['sourceMcTitle'].iloc[0]

                            draft = {
                                'sourceMcTitle': mcTitle,
                                'sourceMcId': mcId,
                                'cluster_id': int(cluster_id),
                                'cluster_size': len(cluster_df),
                                'draft_text': self.generate_draft_for_cluster(cluster_df, mcId, mcTitle)
                            }

                            # Добавляем информацию о каждом объявлении
                            for _, row in cluster_df.iterrows():
                                # Проверяем индивидуальные маркеры
                                independence_score = self.check_independence_markers(row['description'])

                                result = {
                                    'itemId': row['itemId'],
                                    'sourceMcId': row['sourceMcId'],
                                    'sourceMcTitle': row['sourceMcTitle'],
                                    'description': row['description'],
                                    'detectedMcIds': mcIds,
                                    'shouldSplit': True,
                                    'drafts': [{
                                        'mcId': mcId,
                                        'mcTitle': mcTitle,
                                        'text': draft['draft_text']
                                    }],
                                    'cluster_info': {
                                        'cluster_id': int(cluster_id),
                                        'independence_score': independence_score
                                    }
                                }
                                all_results.append(result)
            else:
                # Не разделяем - возвращаем пустые черновики
                for _, row in group_df.iterrows():
                    result = {
                        'itemId': row['itemId'],
                        'sourceMcId': row['sourceMcId'],
                        'sourceMcTitle': row['sourceMcTitle'],
                        'description': row['description'],
                        'detectedMcIds': [],
                        'shouldSplit': False,
                        'drafts': [],
                        'cluster_info': {
                            'cluster_id': int(row['cluster']) if row['cluster'] != -1 else -1,
                            'reason': split_info['reason']
                        }
                    }
                    all_results.append(result)

        return all_results

    def evaluate_results(self, predictions: List[Dict], ground_truth: List[Dict]) -> Dict:
        """
        Оценка качества предсказаний
        """
        print("\n" + "=" * 60)
        print("ОЦЕНКА КАЧЕСТВА")
        print("=" * 60)

        # Создаем словарь для быстрого доступа к эталону
        gt_dict = {item['itemId']: item for item in ground_truth}

        correct = 0
        total = 0
        tp = fp = fn = 0

        for pred in predictions:
            itemId = pred['itemId']
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

        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'total': total,
            'tp': tp,
            'fp': fp,
            'fn': fn
        }

        print(f"Accuracy:  {accuracy:.2%}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall:    {recall:.2%}")
        print(f"F1-score:  {f1:.2%}")
        print(f"\nTP: {tp}, FP: {fp}, FN: {fn}")

        return metrics


def load_dataset(filename: str) -> List[Dict]:
    """Загрузка датасета"""
    print(f"📂 Загрузка {filename}...")

    if filename.endswith('.json'):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    elif filename.endswith('.csv'):
        df = pd.read_csv(filename)
        return df.to_dict('records')
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {filename}")


def main():
    print("=" * 60)
    print("СИСТЕМА АНАЛИЗА ОБЪЯВЛЕНИЙ (ML с эмбеддингами)")
    print("=" * 60)

    # Загрузка данных
    filename = input("\nВведите имя файла с датасетом (JSON или CSV): ")
    if not filename:
        filename = 'dataset.json'

    try:
        ads_data = load_dataset(filename)
        print(f"✓ Загружено {len(ads_data)} объявлений")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return

    # Создаем ML-сплиттер
    splitter = ServiceSplitterML()

    # Обработка датасета
    results = splitter.process_dataset(ads_data)

    # Сохранение результатов
    output_file = input("\nИмя файла для сохранения (Enter для 'ml_results.json'): ")
    if not output_file:
        output_file = 'ml_results.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Результаты сохранены в {output_file}")

    # Оценка качества если есть эталон
    if 'shouldSplit' in ads_data[0]:
        metrics = splitter.evaluate_results(results, ads_data)

        # Сохраняем метрики
        with open('metrics.json', 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        print(f"📊 Метрики сохранены в metrics.json")

    # Статистика
    split_count = sum(1 for r in results if r['shouldSplit'])
    print(f"\n📈 Итоговая статистика:")
    print(f"   Всего объявлений: {len(results)}")
    print(f"   Требуют разделения: {split_count} ({split_count / len(results):.1%})")


if __name__ == "__main__":
    main()