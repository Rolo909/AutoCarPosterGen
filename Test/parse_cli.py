#!/usr/bin/env python3
"""
Интерактивный парсер automobile-catalog.com
CLI интерфейс для удобной работы
"""

import sys
import os

# Проверяем наличие зависимостей
try:
    from automobile_parser_simple import SimpleAutoCatalogParser
    SIMPLE_AVAILABLE = True
except ImportError:
    SIMPLE_AVAILABLE = False

try:
    from automobile_parser_selenium import AutomobileCatalogSeleniumParser
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

import json
from typing import Optional


class Colors:
    """ANSI цвета для красивого вывода"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Вывести заголовок"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}")
    print(f"{text:^80}")
    print(f"{'=' * 80}{Colors.END}\n")


def print_success(text: str):
    """Вывести успех"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    """Вывести ошибку"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    """Вывести информацию"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def print_warning(text: str):
    """Вывести предупреждение"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def get_input(prompt: str, default: str = None) -> str:
    """Получить ввод от пользователя"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    value = input(f"{Colors.CYAN}{prompt}{Colors.END}").strip()
    
    return value if value else default


def select_parser() -> Optional[object]:
    """Выбрать парсер"""
    
    print_header("ВЫБОР ПАРСЕРА")
    
    parsers = []
    
    if SIMPLE_AVAILABLE:
        parsers.append(("Simple Parser", "Быстрый, требует car_id", "simple"))
    
    if SELENIUM_AVAILABLE:
        parsers.append(("Selenium Parser", "Надежный, обходит защиту", "selenium"))
    
    if not parsers:
        print_error("Не установлены зависимости!")
        print_info("Установите: pip install -r requirements.txt")
        return None
    
    print("Доступные парсеры:\n")
    
    for i, (name, desc, _) in enumerate(parsers, 1):
        print(f"{Colors.BOLD}{i}.{Colors.END} {Colors.GREEN}{name}{Colors.END}")
        print(f"   {desc}\n")
    
    choice = get_input(f"Выберите парсер (1-{len(parsers)})", "1")
    
    try:
        choice_idx = int(choice) - 1
        
        if 0 <= choice_idx < len(parsers):
            parser_type = parsers[choice_idx][2]
            
            if parser_type == "simple":
                print_success("Выбран Simple Parser")
                return SimpleAutoCatalogParser()
            
            elif parser_type == "selenium":
                headless = get_input("Headless режим? (y/n)", "y").lower() == 'y'
                print_success(f"Выбран Selenium Parser (headless={headless})")
                return AutomobileCatalogSeleniumParser(headless=headless)
        else:
            print_error("Неверный выбор")
            return None
    
    except ValueError:
        print_error("Неверный ввод")
        return None


def get_car_info():
    """Получить информацию об автомобиле от пользователя"""
    
    print_header("ИНФОРМАЦИЯ ОБ АВТОМОБИЛЕ")
    
    brand = get_input("Марка (например, BMW)")
    if not brand:
        print_error("Марка обязательна!")
        return None
    
    model = get_input("Модель (например, 320i)")
    if not model:
        print_error("Модель обязательна!")
        return None
    
    year = get_input("Год (например, 2019)")
    try:
        year = int(year)
    except:
        print_error("Год должен быть числом!")
        return None
    
    car_id = get_input("car_id (опционально, найдите на сайте)", None)
    
    return {
        'brand': brand,
        'model': model,
        'year': year,
        'car_id': car_id if car_id else None
    }


def get_direct_url():
    """Получить прямой URL"""
    
    print_header("ПРЯМОЙ URL")
    
    url = get_input("Введите полный URL автомобиля")
    
    if not url or not url.startswith('http'):
        print_error("Неверный URL!")
        return None
    
    return url


def save_results(specs, parser):
    """Сохранить результаты"""
    
    print_header("РЕЗУЛЬТАТЫ")
    
    # Выводим основную информацию
    print(f"{Colors.BOLD}Автомобиль:{Colors.END} {specs.version}")
    print(f"{Colors.BOLD}URL:{Colors.END} {specs.url}\n")
    
    if hasattr(specs, 'power_hp') and specs.power_hp:
        print(f"🔧 Мощность: {specs.power_hp}")
    
    if hasattr(specs, 'displacement') and specs.displacement:
        print(f"🔧 Объем: {specs.displacement}")
    
    if hasattr(specs, 'transmission') and specs.transmission:
        print(f"⚙️  КПП: {specs.transmission}")
    
    if hasattr(specs, 'acceleration_0_100_kmh') and specs.acceleration_0_100_kmh:
        print(f"🏁 0-100 км/ч: {specs.acceleration_0_100_kmh}")
    
    if hasattr(specs, 'top_speed_kmh') and specs.top_speed_kmh:
        print(f"🏁 Макс. скорость: {specs.top_speed_kmh}")
    
    # Спрашиваем о сохранении
    save = get_input("\nСохранить в файл? (y/n)", "y").lower() == 'y'
    
    if save:
        default_name = f"{specs.brand}_{specs.model}_{specs.year}.json"
        filename = get_input("Имя файла", default_name)
        
        try:
            parser.save_to_json(specs, filename)
            print_success(f"Сохранено в {filename}")
        except Exception as e:
            print_error(f"Ошибка сохранения: {e}")
    
    # Спрашиваем о полном выводе
    full = get_input("\nПоказать все характеристики? (y/n)", "n").lower() == 'y'
    
    if full:
        parser.print_specs(specs)


def main_menu():
    """Главное меню"""
    
    print_header("🚗 AUTOMOBILE-CATALOG PARSER")
    
    print(f"{Colors.YELLOW}Парсер характеристик автомобилей с automobile-catalog.com{Colors.END}\n")
    
    print("Режимы работы:\n")
    print(f"{Colors.BOLD}1.{Colors.END} Поиск по марке/модели/году")
    print(f"{Colors.BOLD}2.{Colors.END} Парсинг по прямому URL")
    print(f"{Colors.BOLD}3.{Colors.END} Пакетная обработка (batch)")
    print(f"{Colors.BOLD}4.{Colors.END} Выход\n")
    
    choice = get_input("Выберите режим (1-4)", "1")
    
    return choice


def batch_mode(parser):
    """Пакетная обработка"""
    
    print_header("ПАКЕТНАЯ ОБРАБОТКА")
    
    print_info("Введите автомобили в формате: марка,модель,год,car_id")
    print_info("Пример: BMW,320i,2019,2877140")
    print_info("Для завершения ввода нажмите Enter на пустой строке\n")
    
    cars = []
    
    while True:
        line = input(f"{Colors.CYAN}> {Colors.END}").strip()
        
        if not line:
            break
        
        parts = [p.strip() for p in line.split(',')]
        
        if len(parts) < 3:
            print_error("Минимум 3 параметра: марка,модель,год")
            continue
        
        try:
            car = {
                'brand': parts[0],
                'model': parts[1],
                'year': int(parts[2]),
                'car_id': parts[3] if len(parts) > 3 else None
            }
            cars.append(car)
            print_success(f"Добавлено: {car['brand']} {car['model']} {car['year']}")
        except:
            print_error("Ошибка парсинга строки")
    
    if not cars:
        print_warning("Не добавлено ни одного автомобиля")
        return
    
    print(f"\n{Colors.BOLD}Всего автомобилей: {len(cars)}{Colors.END}\n")
    
    results = []
    
    for i, car in enumerate(cars, 1):
        print(f"\n[{i}/{len(cars)}] Парсинг {car['brand']} {car['model']} {car['year']}...")
        
        try:
            if hasattr(parser, 'parse_car'):
                # Selenium parser
                specs = parser.parse_car(
                    car['brand'],
                    car['model'],
                    car['year'],
                    car['car_id']
                )
            else:
                # Simple parser
                url = parser.get_car_url(
                    car['brand'],
                    car['model'],
                    car['year'],
                    car['car_id']
                )
                specs = parser.parse_direct_url(url)
            
            if specs:
                results.append(specs)
                print_success("Успешно")
            else:
                print_error("Не удалось спарсить")
        
        except Exception as e:
            print_error(f"Ошибка: {e}")
        
        # Пауза между запросами
        if i < len(cars):
            import time
            time.sleep(2)
    
    # Сохраняем результаты
    if results:
        print_header("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
        
        filename = get_input("Имя файла для всех результатов", "batch_results.json")
        
        try:
            data = [vars(spec) for spec in results]
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print_success(f"Сохранено {len(results)} автомобилей в {filename}")
        except Exception as e:
            print_error(f"Ошибка сохранения: {e}")


def run():
    """Главная функция"""
    
    while True:
        choice = main_menu()
        
        if choice == "4":
            print_info("До свидания!")
            break
        
        # Выбираем парсер
        parser = select_parser()
        
        if not parser:
            continue
        
        try:
            if choice == "1":
                # Поиск по параметрам
                car_info = get_car_info()
                
                if not car_info:
                    continue
                
                print_header("ПАРСИНГ")
                
                if hasattr(parser, 'parse_car'):
                    # Selenium
                    specs = parser.parse_car(
                        car_info['brand'],
                        car_info['model'],
                        car_info['year'],
                        car_info['car_id']
                    )
                else:
                    # Simple
                    if not car_info['car_id']:
                        print_error("Simple parser требует car_id!")
                        continue
                    
                    url = parser.get_car_url(
                        car_info['brand'],
                        car_info['model'],
                        car_info['year'],
                        car_info['car_id']
                    )
                    specs = parser.parse_direct_url(url)
                
                if specs:
                    save_results(specs, parser)
                else:
                    print_error("Не удалось спарсить автомобиль")
            
            elif choice == "2":
                # Прямой URL
                url = get_direct_url()
                
                if not url:
                    continue
                
                print_header("ПАРСИНГ")
                
                if hasattr(parser, 'parse_car_page'):
                    specs = parser.parse_car_page(url)
                else:
                    specs = parser.parse_direct_url(url)
                
                if specs:
                    save_results(specs, parser)
                else:
                    print_error("Не удалось спарсить страницу")
            
            elif choice == "3":
                # Batch режим
                batch_mode(parser)
        
        except KeyboardInterrupt:
            print_warning("\n\nПрервано пользователем")
            break
        
        except Exception as e:
            print_error(f"Неожиданная ошибка: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Закрываем парсер
            if hasattr(parser, '_close_driver'):
                parser._close_driver()
            elif hasattr(parser, '_close_session'):
                parser._close_session()
        
        # Спрашиваем о продолжении
        if get_input("\nПродолжить? (y/n)", "y").lower() != 'y':
            break
    
    print_success("\nРабота завершена!")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print_warning("\n\nВыход...")
        sys.exit(0)
