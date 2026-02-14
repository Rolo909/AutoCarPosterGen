from car_poster_generator import CarPosterGenerator
import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def quick_generate():
    print("🚗 Car Poster Generator - AI Edition")
    print("Полная AI-генерация постера через Gemini\n")
    print("="*60)
    
    make = input("Введите марку автомобиля (например, BMW): ").strip()
    if not make:
        print("❌ Марка автомобиля обязательна!")
        sys.exit(1)
    
    model = input("Введите модель (например, M4 Competition): ").strip()
    if not model:
        print("❌ Модель автомобиля обязательна!")
        sys.exit(1)
    
    year_input = input("Введите год (опционально, Enter для пропуска): ").strip()
    year = int(year_input) if year_input else None
    
    trim = input("Введите комплектацию (опционально, Enter для пропуска): ").strip() or None
    color = input("Введите цвет (опционально, Enter для пропуска): ").strip() or None
    
    format_input = input("Выберите формат (png/jpg, по умолчанию из .env): ").strip().lower()
    output_format = format_input if format_input in ['png', 'jpg'] else None
    
    print("\n" + "="*60)
    print("🔄 Начинаю AI-генерацию постера...")
    print("="*60 + "\n")
    
    try:
        # Все настройки берутся из .env
        generator = CarPosterGenerator(output_format=output_format)
        
        result = generator.generate_poster(
            make=make,
            model=model,
            year=year,
            trim=trim,
            color=color
        )
        
        print(f"\n✅ УСПЕХ! Постер создан: {result}")
        print(f"🎨 Постер полностью сгенерирован через Gemini AI")
        
    except ValueError as e:
        print(f"\n❌ ОШИБКА КОНФИГУРАЦИИ: {e}")
        print("💡 Проверьте настройки в файле .env")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    quick_generate()