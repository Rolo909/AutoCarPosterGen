import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv
import google.generativeai as genai
from pathlib import Path
import base64

load_dotenv()

class CarPosterGenerator:
    
    def __init__(self, reference_image_path, output_format='png'):
        self.reference_path = reference_image_path
        self.output_format = output_format.lower()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY не найден в .env файле!")
        
        genai.configure(api_key=api_key)
        self.text_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.image_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        self.canvas_width = 604
        self.canvas_height = 854
        self.car_image_height = 400
        
        self.reference_image = Image.open(reference_image_path)
        
    def search_car_specifications(self, make, model, year=None, trim=None):
        print(f"🔍 Поиск характеристик: {make} {model}...")
        
        query = f"{make} {model}"
        if year:
            query += f" {year}"
        if trim:
            query += f" {trim}"
            
        prompt = f"""
Ты автомобильный эксперт. Найди точные технические характеристики автомобиля: {query}

Верни информацию СТРОГО в JSON формате (без markdown, без дополнительного текста):
{{
    "make": "Марка автомобиля",
    "model": "Модель",
    "year_range": "Диапазон годов или конкретный год (например: 2016-2023 или 2020)",
    "engine": "Двигатель (формат: 2.5L TFSI)",
    "power": "Мощность (формат: 394 HP)",
    "torque": "Крутящий момент (формат: 480 Nm)",
    "weight": "Масса (формат: 1450 kg)",
    "acceleration": "Разгон 0-100 км/ч (формат: 3.7 s)",
    "top_speed": "Максимальная скорость (формат: 250 km/h)",
    "country_code": "Двухбуквенный код страны производителя (DE, US, JP, IT, GB, FR, KR, SE, CZ и т.д.)"
}}

Используй официальные данные производителя. Если точных данных нет, используй типичные характеристики для этой модели и года.
"""
        
        try:
            response = self.text_model.generate_content(prompt)
            specs_text = response.text.strip()
            specs_text = specs_text.replace('```json', '').replace('```', '').strip()
            specs = json.loads(specs_text)
            print("✅ Характеристики найдены успешно")
            return specs
            
        except Exception as e:
            print(f"⚠️ Ошибка поиска: {e}")
            print("📋 Использую базовые характеристики...")
            return self._get_default_specs(make, model, year)
    
    def _get_default_specs(self, make, model, year):
        return {
            "make": make,
            "model": model,
            "year_range": str(year) if year else "2020-2024",
            "engine": "2.0L Turbo",
            "power": "300 HP",
            "torque": "400 Nm",
            "weight": "1500 kg",
            "acceleration": "4.5 s",
            "top_speed": "250 km/h",
            "country_code": "DE"
        }
    
    def generate_car_image_prompt(self, make, model, year, color):
        color_desc = f"{color} " if color else "темный элегантный "
        year_desc = f"{year} " if year else ""
        
        prompt = f"""
Профессиональная автомобильная фотография {year_desc}{make} {model} в {color_desc}цвете.

ТРЕБОВАНИЯ К СТИЛЮ:
- Студийное освещение с мягким, равномерным светом
- Чистый белый/светло-серый градиентный фон
- Угол съемки три четверти спереди, показывающий профиль и переднюю часть автомобиля
- Эстетика профессиональной продуктовой фотографии
- Резкая фокусировка на всем автомобиле
- Тонкие тени под автомобилем для глубины
- Стиль высококачественного автомобильного маркетинга

ПРЕЗЕНТАЦИЯ АВТОМОБИЛЯ:
- {color_desc}{year_desc}{make} {model}
- Современный, элегантный внешний вид
- Все детали видны и четкие
- Колеса слегка повернуты для динамичного вида
- Качество профессионального шоу-рума

ТЕХНИЧЕСКИЕ ХАРАКТЕРИСТИКИ:
- Высокое разрешение, фотореалистично
- Студийное освещение (софтбоксы)
- Без водяных знаков, без текста, без логотипов
- Чистая композиция с автомобилем в центре
- Лучшие практики автомобильной фотографии

РЕЗУЛЬТАТ: Только один автомобиль, профессиональный продуктовый снимок, маркетинговое качество, студийная среда.
"""
        return prompt
    
    def analyze_reference_style(self):
        print("🎨 Анализ стиля референса...")
        
        try:
            prompt = """
Проанализируй стиль этого автомобильного постера. Опиши кратко:
1. Стиль освещения
2. Угол съемки автомобиля
3. Фон и его характеристики

Ответь в 2-3 предложениях на русском языке.
"""
            response = self.image_model.generate_content([prompt, self.reference_image])
            analysis = response.text.strip()
            print(f"✅ Анализ завершен")
            return analysis
            
        except Exception as e:
            print(f"⚠️ Ошибка анализа: {e}")
            return "Студийное освещение, вид три четверти, чистый градиентный фон, минималистичный современный стиль"
    
    def generate_car_image(self, make, model, year=None, color=None):
        print(f"🎨 Генерация изображения автомобиля через Gemini Imagen...")
        
        style_analysis = self.analyze_reference_style()
        prompt = self.generate_car_image_prompt(make, model, year, color)
        
        print(f"📝 Промпт для генерации:")
        print(f"{prompt[:200]}...")
        
        try:
            print("⏳ Отправка запроса к Gemini API...")
            
            response = self.image_model.generate_content(
                [prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                )
            )
            
            print(f"📥 Получен ответ от API")
            
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if hasattr(part, 'inline_data'):
                        image_data = part.inline_data.data
                        img = Image.open(BytesIO(image_data))
                        img = img.resize((self.canvas_width - 80, self.car_image_height), Image.Resampling.LANCZOS)
                        print("✅ Изображение сгенерировано успешно")
                        return img
            
            print("⚠️ Не удалось извлечь изображение из ответа")
            return self._create_placeholder_image(make, model)
            
        except Exception as e:
            print(f"⚠️ Ошибка генерации изображения: {e}")
            print(f"Детали ошибки: {type(e).__name__}")
            print("📋 Создаю заглушку...")
            return self._create_placeholder_image(make, model)
    
    def _create_placeholder_image(self, make, model):
        print("🖼️ Создание изображения-заглушки...")
        img = Image.new('RGB', (self.canvas_width - 80, self.car_image_height), color='#E8E8E8')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        text = f"{make}\n{model}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        position = ((img.width - text_width) // 2, (img.height - text_height) // 2)
        draw.text(position, text, fill='#666666', font=font, align='center')
        
        return img
    
    def get_country_flag_emoji(self, country_code):
        if not country_code or len(country_code) != 2:
            return "🏁"
        
        code = country_code.upper()
        flag = ''.join(chr(127397 + ord(char)) for char in code)
        return flag
    
    def create_poster(self, make, model, year=None, trim=None, color=None, output_path=None):
        print(f"\n{'='*60}")
        print(f"🚗 Генерация постера: {make} {model}")
        print(f"{'='*60}\n")
        
        specs = self.search_car_specifications(make, model, year, trim)
        
        car_image = self.generate_car_image(
            make, 
            model, 
            year or specs.get('year_range', '').split('-')[0], 
            color
        )
        
        print("🖼️ Создание композиции...")
        canvas = Image.new('RGB', (self.canvas_width, self.canvas_height), color='#F5F5F5')
        draw = ImageDraw.Draw(canvas)
        
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_model = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
            font_value = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            font_flag = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 24)
        except:
            print("⚠️ Использую стандартные шрифты")
            font_title = ImageFont.load_default()
            font_model = font_label = font_value = font_flag = font_title
        
        draw.text((40, 40), specs['make'].upper(), fill='#333333', font=font_title)
        draw.text((40, 95), specs['model'].upper(), fill='#000000', font=font_model)
        
        car_y_position = 180
        canvas.paste(car_image, (40, car_y_position))
        
        specs_y_start = car_y_position + self.car_image_height + 40
        
        draw.text((40, specs_y_start), "YEAR", fill='#000000', font=font_label)
        
        col1_x = 140
        col2_x = 280
        col3_x = 420
        
        draw.text((col1_x, specs_y_start), "Engine", fill='#666666', font=font_label)
        draw.text((col1_x, specs_y_start + 20), specs.get('engine', 'N/A'), fill='#000000', font=font_value)
        
        draw.text((col1_x, specs_y_start + 45), "Power", fill='#666666', font=font_label)
        draw.text((col1_x, specs_y_start + 65), specs.get('power', 'N/A'), fill='#000000', font=font_value)
        
        draw.text((col1_x, specs_y_start + 90), "Torque", fill='#666666', font=font_label)
        draw.text((col1_x, specs_y_start + 110), specs.get('torque', 'N/A'), fill='#000000', font=font_value)
        
        draw.text((col1_x, specs_y_start + 135), "Weight", fill='#666666', font=font_label)
        draw.text((col1_x, specs_y_start + 155), specs.get('weight', 'N/A'), fill='#000000', font=font_value)
        
        draw.text((col2_x, specs_y_start), "0-100 km/h", fill='#666666', font=font_label)
        draw.text((col2_x, specs_y_start + 20), specs.get('acceleration', 'N/A'), fill='#000000', font=font_value)
        
        draw.text((col2_x, specs_y_start + 45), "Top speed", fill='#666666', font=font_label)
        draw.text((col2_x, specs_y_start + 65), specs.get('top_speed', 'N/A'), fill='#000000', font=font_value)
        
        year_display = specs.get('year_range', 'N/A')
        draw.text((40, specs_y_start + 20), year_display, fill='#000000', font=font_value)
        
        flag_emoji = self.get_country_flag_emoji(specs.get('country_code', 'DE'))
        draw.text((self.canvas_width - 80, specs_y_start + 140), flag_emoji, font=font_flag, embedded_color=True)
        
        if not output_path:
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            filename = f"{make}_{model}_{year or 'latest'}.{self.output_format}"
            output_path = output_dir / filename
        
        if self.output_format == 'jpg':
            canvas = canvas.convert('RGB')
            canvas.save(output_path, 'JPEG', quality=95, optimize=True)
        else:
            canvas.save(output_path, 'PNG', optimize=True)
        
        print(f"\n✅ Постер создан: {output_path}")
        print(f"{'='*60}\n")
        
        return str(output_path)


def main():
    reference_image = "/AutoCarPosterGen/photo_2026-02-13_02-02-39.jpg"
    
    generator = CarPosterGenerator(
        reference_image_path=reference_image,
        output_format='png'
    )
    
    examples = [
        {
            "make": "BMW",
            "model": "M4",
            "year": 2023,
            "color": "Alpine White"
        },
        {
            "make": "Porsche",
            "model": "911 GT3",
            "year": 2024,
            "trim": "RS",
            "color": "Racing Yellow"
        },
        {
            "make": "Mercedes-AMG",
            "model": "GT R",
            "year": 2022,
            "color": "AMG Green Hell Magno"
        }
    ]
    
    result = generator.create_poster(**examples[0])
    print(f"Создан файл: {result}")


if __name__ == "__main__":
    main()