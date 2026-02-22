# 🚗 Car Poster Generator - AI Edition

**Полностью автоматический генератор автомобильных постеров через Gemini 3 Pro Image (Nano Banana Pro)**

Весь постер генерируется искусственным интеллектом:
- ✨ Фотореалистичное изображение автомобиля
- 📊 Технические характеристики (находятся автоматически)
- 🎨 Профессиональный дизайн по референсу
- 🌍 Флаг страны производителя

## 🎯 Особенности AI-версии

### Используемые модели:
1. **gemini-2.0-flash-exp** - для поиска характеристик авто (быстрая и дешевая)
2. **gemini-3-pro-image-preview** (Nano Banana Pro) - для генерации постера (премиум качество)

### Что делает AI:
1. **Находит характеристики** автомобиля (двигатель, мощность, разгон и т.д.)
2. **Генерирует изображение** автомобиля в нужном цвете
3. **Создает весь постер** с текстом, данными и оформлением
4. **Следует стилю** референсного изображения

### Преимущества:
- ✅ Не нужны шрифты
- ✅ Не нужна ручная верстка
- ✅ Точные характеристики из базы знаний AI
- ✅ Профессиональный результат одним кликом
- ✅ Использование передовой модели Gemini 3 Pro Image

## 📋 Требования

- **Python 3.8+**
- **Google AI Studio API ключ** (бесплатно)

## 🔧 Установка

### 1. Установите зависимости

```bash
pip install google-genai pillow python-dotenv
```

**ВАЖНО:** Используйте `google-genai` (новый SDK), а НЕ `google-generativeai` (устаревший)!

или используйте requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Получите API ключ Gemini

1. Перейдите на https://aistudio.google.com/apikey
2. Войдите через Google аккаунт
3. Нажмите **"Create API key"**
4. Скопируйте ключ

### 3. Настройте .env файл

Откройте файл `.env` и заполните:

```env
# Ваш API ключ Gemini
GEMINI_API_KEY=ваш_ключ_здесь

# Путь к референсному постеру
REFERENCE_IMAGE_PATH=/AutoCarPosterGen/reference.jpg

# Папка для сохранения (создается автоматически)
OUTPUT_DIRECTORY=output

# Формат (png или jpg)
DEFAULT_OUTPUT_FORMAT=png
```

## 🚀 Использование

### Быстрый старт (интерактивный режим)

```bash
python quick_start.py
```

**Программа спросит:**
```
Введите марку автомобиля: Audi
Введите модель: RS6 Avant
Введите год: 2025
Введите комплектацию: [Enter для пропуска]
Введите цвет: Red
Выберите формат: jpg
```

**Результат:** Готовый постер в папке `output/`

### Использование в коде

```python
from car_poster_generator import CarPosterGenerator

# Создаем генератор (настройки из .env)
generator = CarPosterGenerator()

# Генерируем постер
result = generator.generate_poster(
    make="Audi",
    model="RS6 Avant",
    year=2025,
    color="Red"
)

print(f"Постер создан: {result}")
```

## 🎨 Как это работает

### Процесс генерации:

```
1. gemini-2.0-flash-exp ищет характеристики авто
   ↓
2. Создается детальный промпт с референсом
   ↓
3. gemini-3-pro-image-preview генерирует ВЕСЬ постер
   ↓
4. Сохранение файла
```

### Что отправляется в AI:

1. **Референсное изображение** - образец стиля
2. **Детальный промпт** с:
   - Маркой и моделью автомобиля
   - Всеми техническими характеристиками
   - Требованиями к композиции
   - Цветовой схемой
   - Типографикой

## 🤖 Используемые модели

### Для поиска характеристик:
- **Модель:** `gemini-2.0-flash-exp`
- **Зачем:** Быстрый и дешевый поиск технических данных
- **Стоимость:** Минимальная

### Для генерации постера:
- **Модель:** `gemini-3-pro-image-preview` (Nano Banana Pro)
- **Зачем:** Премиум качество генерации изображений
- **Особенности:**
  - Высокое разрешение (1K, 2K, 4K)
  - Точная визуализация текста
  - Режим мышления для анализа сложных промптов
  - До 14 референсных изображений

## 🐛 Решение проблем

### ModuleNotFoundError: No module named 'google.genai'

```bash
pip install google-genai
```

**НЕ устанавливайте** старый пакет `google-generativeai`!

### FutureWarning о google.generativeai

Если видите это предупреждение, значит у вас установлен старый пакет. Удалите его:

```bash
pip uninstall google-generativeai
pip install google-genai
```

### 404 models/gemini-2.0-flash-exp is not found

Это означает, что используется старый SDK. Переустановите:

```bash
pip uninstall google-generativeai
pip install google-genai
```

### ValueError: GEMINI_API_KEY не найден

**Проверьте:**
1. ✅ Файл `.env` в той же папке, что и скрипты
2. ✅ Нет лишних пробелов: `GEMINI_API_KEY=ключ` (не `GEMINI_API_KEY = ключ`)
3. ✅ Ключ валидный (проверьте на https://aistudio.google.com/apikey)

### ValueError: REFERENCE_IMAGE_PATH не указан

**Проверьте:**
1. ✅ Путь в `.env` правильный
2. ✅ Файл существует
3. ✅ Используйте прямые слеши `/` даже в Windows:
   - ✅ Правильно: `/Projects/reference.jpg`
   - ❌ Неправильно: `\Projects\reference.jpg`

## 📁 Структура проекта

```
AutoCarPosterGen/
├── car_poster_generator.py  # Основной класс (AI-версия)
├── quick_start.py            # Интерактивный запуск
├── examples.py               # Примеры использования
├── .env                      # Конфигурация
├── requirements.txt          # Зависимости
├── reference.jpg             # Образец стиля
└── output/                   # Готовые постеры (создается автоматически)
```

## 🎯 Примеры

### Спортивные автомобили

```python
# BMW M4 Competition
generator.generate_poster(
    make="BMW",
    model="M4 Competition",
    year=2023,
    color="Alpine White"
)

# Porsche 911 GT3 RS
generator.generate_poster(
    make="Porsche",
    model="911 GT3",
    year=2024,
    trim="RS",
    color="Racing Yellow"
)
```

### Универсалы и седаны

```python
# Audi RS6 Avant
generator.generate_poster(
    make="Audi",
    model="RS6 Avant",
    year=2025,
    color="Nardo Grey"
)

# Mercedes-AMG E63 S
generator.generate_poster(
    make="Mercedes-AMG",
    model="E63 S",
    year=2024,
    color="Designo Diamond White"
)
```

## 💰 Стоимость использования

### Gemini 2.0 Flash (поиск характеристик):
- Бесплатные лимиты: 15 запросов в минуту
- Очень дешево

### Gemini 3 Pro Image (генерация постера):
- Вход (текст): $2 за 1M токенов
- Выход (изображение): $0.134 за изображение
- Бесплатные лимиты: доступны

**Примерная стоимость 1 постера:** ~$0.15-0.20
