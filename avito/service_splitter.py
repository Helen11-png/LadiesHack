import json
import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class MicroCategory:
    mcId: int
    mcTitle: str
    keyPhrases: List[str]


class ServiceSplitter:
    def __init__(self, categories_dict: List[Dict]):
        """Загружает ВСЕ категории из словаря"""
        self.categories = {}
        for cat in categories_dict:
            self.categories[cat['mcId']] = MicroCategory(
                mcId=cat['mcId'],
                mcTitle=cat['mcTitle'],
                keyPhrases=cat['keyPhrases']
            )

        print(f"✓ Загружено категорий: {len(self.categories)}")
        for cat in self.categories.values():
            print(f"  - {cat.mcTitle}")

        self.independence_markers = [
            r'отдельн[а-я]+',
            r'также\s+(?:выполняем|делаем|предлагаем|могу|занимаюсь|преподаю|чиню)',
            r'можем\s+(?:сделать|выполнить|починить)\s+(?:только|отдельно)',
            r'можно\s+заказать\s+отдельно',
            r'(?:выполняем|делаем|предлагаю|преподаю|чиню)\s+[^.]*?\s+отдельно',
        ]

        self.complex_markers = [
            r'в\s+том\s+числе',
            r'включая',
            r'в\s+состав[а-я]+',
            r'комплексн[а-я]+',
            r'в\s+одном\s+пакете',
            r'полный\s+образ',
        ]

    def fuzzy_match(self, text: str, phrase: str) -> bool:
        """Умный поиск - только если услуга ДЕЙСТВИТЕЛЬНО упоминается"""
        text_lower = text.lower()
        phrase_lower = phrase.lower()

        # 1. Точное совпадение
        if phrase_lower in text_lower:
            return True

        # 2. Ключевые слова из фразы (минимум 4 буквы)
        key_words = [w for w in phrase_lower.split() if len(w) >= 4]

        if key_words:
            # Ищем хотя бы одно ключевое слово
            for word in key_words:
                if word in text_lower:
                    return True

        # 3. Специфические термины для каждой категории
        specific_terms = {
            'репетитор': ['преподаю', 'егэ', 'огэ', 'уроки', 'обучение'],
            'готов': ['готовлю', 'повар', 'кухня', 'еда', 'торт', 'выпечка'],
            'убор': ['уборка', 'клининг', 'мою', 'чистота'],
            'строи': ['строю', 'крыша', 'фундамент', 'стены', 'ремонт квартир'],
            'ремонт': ['чиню', 'починка', 'ремонтирую', 'поломка'],
            'красот': ['маникюр', 'педикюр', 'макияж', 'прическа', 'ресницы', 'брови'],
            'фото': ['фотограф', 'съемка', 'видео', 'обработка'],
        }

        # Проверяем специфические термины
        for category, terms in specific_terms.items():
            if category in phrase_lower:
                for term in terms:
                    if term in text_lower:
                        return True

        return False

    def extract_services(self, text: str) -> Dict[int, Dict]:
        """Ищет совпадения по ВСЕМ категориям из словаря"""
        text_lower = text.lower()
        detected = {}

        for mcId, category in self.categories.items():
            matches = []
            for phrase in category.keyPhrases:
                if self.fuzzy_match(text, phrase):
                    matches.append(phrase)

            # Только если нашли реальные совпадения
            if matches:
                # Ограничиваем уверенность - не больше 3 совпадений учитываем
                confidence = min(1.0, len(matches) / 3)
                detected[mcId] = {
                    'matches': matches[:3],  # Берем только первые 3
                    'confidence': confidence,
                    'title': category.mcTitle
                }

        return detected

    def check_independence(self, text: str, mcId: int, matches: List[str]) -> float:
        text_lower = text.lower()
        score = 0.3  # Начинаем с низкого score

        # Проверяем каждое совпадение в контексте
        for match in matches[:2]:  # Проверяем только первые 2 совпадения
            match_pos = text_lower.find(match.lower())
            if match_pos != -1:
                # Смотрим контекст вокруг совпадения
                start = max(0, match_pos - 60)
                end = min(len(text_lower), match_pos + len(match) + 60)
                context = text_lower[start:end]

                # Если рядом есть маркеры самостоятельности
                if any(re.search(marker, context) for marker in self.independence_markers):
                    score += 0.3

                # Если рядом маркеры комплексности
                if any(re.search(marker, context) for marker in self.complex_markers):
                    score -= 0.2

        # Общие маркеры по всему тексту
        if any(re.search(marker, text_lower) for marker in self.independence_markers):
            score += 0.2

        return max(0.0, min(1.0, score))

    def should_split(self, text: str, detected_services: Dict[int, Dict]) -> Tuple[bool, List[int]]:
        if len(detected_services) <= 1:
            return False, []

        independent = []
        for mcId, info in detected_services.items():
            independence_score = self.check_independence(text, mcId, info['matches'])
            final_score = (info['confidence'] * 0.6 + independence_score * 0.4)

            # Более строгий порог
            if final_score >= 0.5:
                independent.append(mcId)

        # Разделяем только если нашли ХОТЯ БЫ 2 РАЗНЫЕ услуги
        should_split = len(independent) >= 2

        # Дополнительная проверка: услуги должны быть явно разные
        if should_split:
            categories_titles = [self.categories[mcId].mcTitle for mcId in independent]
            # Если это все вариации одной услуги - не разделяем
            if len(set(categories_titles)) < 2:
                should_split = False

        return should_split, independent if should_split else []

    def generate_draft(self, original_text: str, mcId: int, matches: List[str]) -> str:
        category = self.categories[mcId]

        # Ищем предложения с ключевыми словами
        sentences = re.split(r'[.!?]+', original_text)
        relevant = []

        for sentence in sentences:
            if any(self.fuzzy_match(sentence, m) for m in matches):
                relevant.append(sentence.strip())

        if relevant:
            base = ' '.join(relevant[:1])  # Берем только 1 релевантное предложение
            text = f"{base} Выполняю как отдельную услугу."
        else:
            # Создаем общий текст
            text = f"Оказываю услуги по направлению: {category.mcTitle.lower()}."

        return text[:500]

    def process(self, ad: Dict) -> Dict:
        print(f"\n🔍 Анализ текста...")

        detected = self.extract_services(ad['description'])
        print(f"📌 Найдено категорий: {[self.categories[mcId].mcTitle for mcId in detected.keys()]}")

        if detected:
            for mcId, info in detected.items():
                print(f"   - {info['title']}: найдено фраз - {len(info['matches'])}")

        should_split, independent_mcIds = self.should_split(ad['description'], detected)

        detected_mcIds = [mcId for mcId in detected.keys() if mcId != ad['mcId']]
        independent_mcIds = [mcId for mcId in independent_mcIds if mcId != ad['mcId']]

        drafts = []
        if should_split and independent_mcIds:
            for mcId in independent_mcIds:
                draft = {
                    'mcId': mcId,
                    'mcTitle': self.categories[mcId].mcTitle,
                    'text': self.generate_draft(ad['description'], mcId, detected[mcId]['matches'])
                }
                drafts.append(draft)

        return {
            'detectedMcIds': detected_mcIds,
            'shouldSplit': should_split,
            'drafts': drafts
        }


def load_categories(filename='microcategories.json'):
    """Загрузка словаря категорий"""
    while True:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Файл {filename} не найден!")
            filename = input("Введите путь к файлу с категориями: ")


def process_manual_input(splitter):
    """Ручной ввод текста"""
    print("\n" + "=" * 60)
    print("РУЧНОЙ ВВОД ОБЪЯВЛЕНИЯ")
    print("=" * 60)

    print("\nДоступные категории:")
    for mcId, cat in splitter.categories.items():
        print(f"  {mcId}: {cat.mcTitle}")

    while True:
        try:
            mcId = int(input("\nВведите ID основной категории: "))
            if mcId in splitter.categories:
                break
            print(f"❌ Категория с ID {mcId} не найдена!")
        except ValueError:
            print("❌ Введите число!")

    description = input("Введите текст объявления: ")

    ad = {
        "itemId": 999,
        "mcId": mcId,
        "mcTitle": splitter.categories[mcId].mcTitle,
        "description": description
    }

    result = splitter.process(ad)

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТ")
    print("=" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


def process_from_file(splitter):
    """Загрузка из файла"""
    print("\n" + "=" * 60)
    print("ЗАГРУЗКА ИЗ ФАЙЛА")
    print("=" * 60)

    filename = input("Введите имя файла с объявлениями (например, ads.json): ")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            ads = json.load(f)

        print(f"✓ Загружено {len(ads)} объявлений")

        results = []
        for i, ad in enumerate(ads, 1):
            print(f"  Обработка {i}/{len(ads)}...", end=" ")
            result = splitter.process(ad)
            results.append(result)
            print("✓")

        output_file = input("\nИмя файла для сохранения (или Enter для 'results.json'): ")
        if not output_file:
            output_file = 'results.json'

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n✓ Результаты сохранены в {output_file}")

        split_count = sum(1 for r in results if r['shouldSplit'])
        print(f"\nСтатистика:")
        print(f"  Всего объявлений: {len(results)}")
        print(f"  Требуют разделения: {split_count}")
        print(f"  Не требуют разделения: {len(results) - split_count}")

    except FileNotFoundError:
        print(f"❌ Файл {filename} не найден!")
    except json.JSONDecodeError:
        print(f"❌ Файл {filename} содержит некорректный JSON!")


def process_interactive(splitter):
    """Интерактивный режим - ввод нескольких объявлений"""
    print("\n" + "=" * 60)
    print("ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("=" * 60)
    print("Вводите объявления одно за другим. Для выхода введите 'exit'")

    results = []
    ad_count = 1

    print("\nДоступные категории:")
    for mcId, cat in splitter.categories.items():
        print(f"  {mcId}: {cat.mcTitle}")

    while True:
        print(f"\n--- Объявление #{ad_count} ---")

        mcId_input = input("ID категории (или 'exit' для выхода): ")
        if mcId_input.lower() == 'exit':
            break

        try:
            mcId = int(mcId_input)
            if mcId not in splitter.categories:
                print(f"❌ Категория {mcId} не найдена!")
                continue
        except ValueError:
            print("❌ Введите число!")
            continue

        description = input("Текст объявления: ")
        if description.lower() == 'exit':
            break

        ad = {
            "itemId": 1000 + ad_count,
            "mcId": mcId,
            "mcTitle": splitter.categories[mcId].mcTitle,
            "description": description
        }

        result = splitter.process(ad)
        results.append(result)

        print(f"  Найдено категорий: {result['detectedMcIds']}")
        print(f"  Разделять: {'ДА' if result['shouldSplit'] else 'НЕТ'}")
        if result['shouldSplit']:
            print(f"  Будет создано черновиков: {len(result['drafts'])}")

        ad_count += 1

    if results:
        save = input("\nСохранить результаты в файл? (y/n): ")
        if save.lower() == 'y':
            filename = input("Имя файла (или Enter для 'results.json'): ")
            if not filename:
                filename = 'results.json'

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"✓ Сохранено в {filename}")


def main():
    print("=" * 60)
    print("СИСТЕМА АНАЛИЗА ОБЪЯВЛЕНИЙ ДЛЯ АВИТО")
    print("=" * 60)

    categories = load_categories()
    splitter = ServiceSplitter(categories)

    while True:
        print("\n" + "=" * 60)
        print("ВЫБЕРИТЕ РЕЖИМ РАБОТЫ:")
        print("=" * 60)
        print("1. Ручной ввод одного объявления")
        print("2. Загрузка из файла")
        print("3. Интерактивный режим (несколько объявлений)")
        print("4. Выход")

        choice = input("\nВаш выбор (1-4): ")

        if choice == '1':
            process_manual_input(splitter)
        elif choice == '2':
            process_from_file(splitter)
        elif choice == '3':
            process_interactive(splitter)
        elif choice == '4':
            print("\nДо свидания!")
            break
        else:
            print("❌ Неверный выбор!")


if __name__ == "__main__":
    main()