from car_poster_generator import CarPosterGenerator
import sys

def quick_generate():
    print("🚗 Car Poster Generator - Быстрый старт\n")
    print("="*60)
    
    make = input("Введите марку автомобиля (например, BMW): ").strip()
    model = input("Введите модель (например, M4): ").strip()
    
    year_input = input("Введите год (опционально, Enter для пропуска): ").strip()
    year = int(year_input) if year_input else None
    
    trim = input("Введите комплектацию (опционально, Enter для пропуска): ").strip() or None
    color = input("Введите цвет (опционально, Enter для пропуска): ").strip() or None
    
    format_input = input("Выберите формат (png/jpg, по умолчанию png): ").strip().lower()
    output_format = format_input if format_input in ['png', 'jpg'] else 'png'
    
    print("\n" + "="*60)
    print("🔄 Начинаю генерацию...")
    print("="*60 + "\n")
    
    try:
        generator = CarPosterGenerator(
            reference_image_path="/AutoCarPosterGen/photo_2026-02-13_02-02-39.jpg",
            output_format=output_format
        )
        
        result = generator.create_poster(
            make=make,
            model=model,
            year=year,
            trim=trim,
            color=color
        )
        
        print(f"\n✅ УСПЕХ! Файл создан: {result}")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        sys.exit(1)

if __name__ == "__main__":
    quick_generate()