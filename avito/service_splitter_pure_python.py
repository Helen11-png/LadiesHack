import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set
import math


class TextCleaner:
    """Очистка текста объявлений"""

    @staticmethod
    def clean_text(text: str) -> str:
        if not isinstance(text, str):
            return ""

        text = text.lower()
        text = re.sub(r'[^а-яёa-z\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        words = text.split()
        words = [w for w in words if len(w) >= 3]

        return ' '.join(words)


class SimpleServiceSplitter:
    """Простое решение на чистых правилах без ML"""

    def __init__(self):
        self.cleaner = TextCleaner()

        # Маркеры самостоятельности
        self.independence_markers = [
            r'отдельн[а-я]+',
            r'также\s+(?:выполняем|делаем|предлагаем|могу)',
            r'можно\s+заказать\s+отдельно',
            r'(?:выполняем|делаем)\s+[^.]*?\s+отдельно',
        ]

        # Маркеры комплексности
        self.complex_markers = [
            r'в\s+том\s+числе',
            r'включая',
            r'в\s+состав[а-я]+',
            r'комплексн[а-я]+',
            r'под\s+ключ',
            r'всё\s+виды',
            r'полный\s+спектр',
        ]

        # Ключевые слова для разных услуг (можно расширять)
        self.service_keywords = {
            'сантехника': ['сантехник', 'водопровод', 'трубы', 'унитаз', 'смеситель', 'раковина'],
            'электрика': ['электрик', 'проводка', 'розетки', 'щиток', 'свет', 'кабель'],
            'плитка': ['плитка', 'плиточник', 'укладка плитки', 'керамогранит'],
            'потолки': ['потолок', 'натяжной', 'гипсокартон', 'потолочный'],
            'стены': ['стены', 'штукатурка', 'шпаклевка', 'обои', 'покраска'],
            'полы': ['пол', 'ламинат', 'паркет', 'стяжка', 'наливной'],
            'отделка': ['отделка', 'косметический', 'чистовая', 'черновая'],
            'дизайн': ['дизайн', 'проект', 'планировка', 'интерьер'],
        }

    def extract_keywords(self, text: str) -> Dict[str, List[str]]:
        """Извлечение ключевых слов из текста"""
        text_lower = text.lower()
        found_services = {}

        for service, keywords in self.service_keywords.items():
            matches = []
            for kw in keywords:
                if kw in text_lower:
                    matches.append(kw)

            if matches:
                found_services[service] = matches

        return found_services

    def calculate_tfidf_similarity(self, text1: str, text2: str) -> float:
        """Простая оценка схожести текстов через пересечение слов"""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def cluster_simple(self, texts: List[str], threshold: float = 0.3) -> List[int]:
        """
        Простая кластеризация на основе схожести текстов
        """
        n = len(texts)
        if n < 2:
            return [0] * n

        labels = [-1] * n
        cluster_id = 0

        for i in range(n):
            if labels[i] != -1:
                continue

            # Начинаем новый кластер
            labels[i] = cluster_id
            cluster_texts = [texts[i]]

            # Ищем похожие тексты
            for j in range(i + 1, n):
                if labels[j] != -1:
                    continue

                # Сравниваем с центроидом кластера
                max_sim = max(self.calculate_tfidf_similarity(texts[j], ct)
                              for ct in cluster_texts)

                if max_sim >= threshold:
                    labels[j] = cluster_id
                    cluster_texts.append(texts[j])

            cluster_id += 1

        return labels

    def check_independence(self, text: str) -> Tuple[bool, float]:
        """Проверка маркеров самостоятельности"""
        if not text:
            return False, 0.0

        text_lower = text.lower()
        score = 0.0

        # Проверяем маркеры
        ind_count = sum(1 for m in self.independence_markers if re.search(m, text_lower))
        comp_count = sum(1 for m in self.complex_markers if re.search(m, text_lower))

        if ind_count > 0:
            score += 0.4 * ind_count

        if comp_count > 0:
            score -= 0.3 * comp_count

        score = max(0.0, min(1.0, 0.5 + score))

        return score >= 0.6, score

    def process_ad(self, ad: Dict) -> Dict:
        """Обработка одного объявления"""
        description = ad.get('description', '')
        clean_text = self.cleaner.clean_text(description)

        # Извлекаем ключевые слова
        services = self.extract_keywords(clean_text)

        # Проверяем самостоятельность
        is_independent, confidence = self.check_independence(description)

        # Определяем, нужно ли разделять
        should_split = is_independent and len(services) >= 2

        # Создаем черновики если нужно
        drafts = []
        if should_split:
            for service, keywords in services.items():
                if service != ad.get('sourceMcTitle', '').lower():
                    draft_text = f"Выполняю отдельно: {service}. {description[:200]}"
                    drafts.append({
                        'mcId': None,
                        'mcTitle': service.capitalize(),
                        'text': draft_text[:500]
                    })

        return {
            'itemId': ad.get('itemId'),
            'detectedMcIds': list(services.keys()),
            'shouldSplit': should_split,
            'drafts': drafts,
            'confidence': confidence,
            'found_services': services
        }

    def process_dataset(self, ads_data: List[Dict]) -> Dict:
        """Обработка всего датасета с группировкой по категориям"""
        print("\n" + "=" * 60)
        print("ОБРАБОТКА ДАТАСЕТА")
        print("=" * 60)

        # Группируем по sourceMcTitle
        grouped = defaultdict(list)
        for ad in ads_data:
            grouped[ad.get('sourceMcTitle', 'unknown')].append(ad)

        print(f"📊 Найдено {len(grouped)} категорий")

        all_results = []
        stats = {
            'total': len(ads_data),
            'split': 0,
            'no_split': 0,
            'categories_processed': 0
        }

        for mcTitle, group in grouped.items():
            if len(group) < 5:  # Пропускаем маленькие группы
                continue

            print(f"\n🔍 Категория: {mcTitle} ({len(group)} объявлений)")

            # Очищаем тексты
            clean_texts = [self.cleaner.clean_text(ad.get('description', '')) for ad in group]
            clean_texts = [t for t in clean_texts if len(t) > 10]

            if len(clean_texts) < 5:
                print(f"   ⏭️ Пропущено (мало качественных текстов)")
                continue

            # Кластеризуем
            labels = self.cluster_simple(clean_texts, threshold=0.25)
            unique_labels = set(labels)
            n_clusters = len(unique_labels)

            print(f"   Найдено кластеров: {n_clusters}")

            # Анализируем каждый кластер
            for cluster_id in unique_labels:
                cluster_indices = [i for i, l in enumerate(labels) if l == cluster_id]

                if len(cluster_indices) < 3:
                    continue

                # Собираем объявления кластера
                cluster_ads = [group[i] for i in cluster_indices if i < len(group)]

                # Проверяем, нужно ли разделять для этого кластера
                split_count = 0
                for ad in cluster_ads:
                    result = self.process_ad(ad)

                    # Групповое решение: разделяем если большинство объявлений в кластере это поддерживают
                    if result['shouldSplit']:
                        split_count += 1

                    all_results.append(result)

                # Статистика по кластеру
                cluster_split_ratio = split_count / len(cluster_ads)
                print(f"   Кластер {cluster_id}: {len(cluster_ads)} объявлений, "
                      f"доля разделения: {cluster_split_ratio:.1%}")

                if cluster_split_ratio > 0.5:
                    stats['split'] += len(cluster_ads)
                else:
                    stats['no_split'] += len(cluster_ads)

            stats['categories_processed'] += 1

        print("\n" + "=" * 60)
        print("ИТОГИ")
        print("=" * 60)
        print(f"Всего объявлений: {stats['total']}")
        print(f"Требуют разделения: {stats['split']} ({stats['split'] / max(1, stats['total']) * 100:.1f}%)")
        print(f"Не требуют разделения: {stats['no_split']} ({stats['no_split'] / max(1, stats['total']) * 100:.1f}%)")
        print(f"Обработано категорий: {stats['categories_processed']}")

        return {
            'results': all_results,
            'stats': stats
        }


def load_dataset(filename: str) -> List[Dict]:
    """Загрузка датасета"""
    print(f"📂 Загрузка {filename}...")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'items' in data:
            return data['items']
        else:
            return [data]

    except json.JSONDecodeError:
        # Пробуем как CSV
        import csv
        data = []
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        return data

    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return []


def main():
    print("=" * 60)
    print("СИСТЕМА АНАЛИЗА ОБЪЯВЛЕНИЙ (Чистый Python)")
    print("=" * 60)

    filename = input("\nВведите имя файла с датасетом: ").strip()
    if not filename:
        filename = 'rnc_dataset.json'

    ads_data = load_dataset(filename)

    if not ads_data:
        print("❌ Не удалось загрузить данные")
        return

    print(f"✓ Загружено {len(ads_data)} объявлений")

    splitter = SimpleServiceSplitter()

    # Обработка
    output = splitter.process_dataset(ads_data)

    # Сохранение
    output_file = 'results_simple.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Результаты сохранены в {output_file}")

    # Показываем примеры
    print("\n" + "=" * 60)
    print("ПРИМЕРЫ ОБРАБОТАННЫХ ОБЪЯВЛЕНИЙ")
    print("=" * 60)

    for i, result in enumerate(output['results'][:3]):
        print(f"\n📝 Объявление {i + 1}:")
        print(f"   ID: {result['itemId']}")
        print(f"   Найдено услуг: {result['found_services']}")
        print(f"   Разделять: {'ДА' if result['shouldSplit'] else 'НЕТ'}")
        print(f"   Уверенность: {result['confidence']:.2f}")


if __name__ == "__main__":
    main()