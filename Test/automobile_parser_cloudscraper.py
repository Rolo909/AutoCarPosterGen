"""
Парсер automobile-catalog.com с обходом Cloudflare
Использует cloudscraper - не требует Selenium!
"""

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    import requests

from bs4 import BeautifulSoup
import json
import re
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import time


@dataclass
class CarSpecs:
    """Характеристики автомобиля"""
    brand: str
    model: str
    year: int
    version: str
    url: str
    
    # Все характеристики в виде словаря
    specifications: Dict[str, str]
    
    # Основные поля для быстрого доступа
    engine_power: Optional[str] = None
    engine_displacement: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    acceleration_0_100: Optional[str] = None
    top_speed: Optional[str] = None


class CloudscraperParser:
    """Парсер с обходом Cloudflare через cloudscraper"""
    
    BASE_URL = "https://www.automobile-catalog.com"
    
    def __init__(self):
        """Инициализация парсера"""
        if CLOUDSCRAPER_AVAILABLE:
            print("✅ Используется cloudscraper для обхода Cloudflare")
            self.scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
        else:
            print("⚠️ cloudscraper не установлен, используется requests")
            print("   Установите: pip install cloudscraper")
            self.scraper = requests.Session()
            self.scraper.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
    
    def get_car_url(self, brand: str, model: str, year: int, car_id: str) -> str:
        """
        Получить URL автомобиля
        
        Args:
            brand: Марка (BMW)
            model: Модель (M5 F90)
            year: Год (2019)
            car_id: ID автомобиля на сайте
        
        Returns:
            URL страницы
        """
        # Нормализуем названия
        brand_slug = brand.lower().replace(' ', '-').replace('_', '-')
        model_slug = model.lower().replace(' ', '_').replace('-', '_')
        
        return f"{self.BASE_URL}/car/{year}/{car_id}/{brand_slug}_{model_slug}.html"
    
    def search_car_id(self, brand: str, model: str, year: int) -> Optional[str]:
        """
        Поиск car_id через Google
        
        Args:
            brand: Марка
            model: Модель
            year: Год
            
        Returns:
            car_id или None
        """
        print(f"🔍 Поиск car_id для {year} {brand} {model}...")
        
        # Пробуем поискать через Google
        search_query = f"site:automobile-catalog.com {year} {brand} {model}"
        google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        try:
            response = self.scraper.get(google_url, timeout=10)
            
            if response.status_code == 200:
                # Ищем ссылки на automobile-catalog.com
                pattern = r'automobile-catalog\.com/car/(\d{4})/(\d+)/'
                matches = re.findall(pattern, response.text)
                
                if matches:
                    car_id = matches[0][1]
                    print(f"✅ Найден car_id: {car_id}")
                    return car_id
        except Exception as e:
            print(f"⚠️ Не удалось выполнить поиск: {e}")
        
        print("❌ car_id не найден. Укажите вручную.")
        return None
    
    def parse_direct_url(self, url: str) -> Optional[CarSpecs]:
        """
        Парсинг по прямому URL
        
        Args:
            url: Полный URL страницы автомобиля
        
        Returns:
            Объект CarSpecs с характеристиками
        """
        print(f"📄 Парсинг: {url}")
        
        try:
            # Делаем запрос
            response = self.scraper.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ Ошибка {response.status_code}")
                return None
            
            # Проверяем, не Cloudflare ли это
            if 'cloudflare' in response.text.lower() and 'checking your browser' in response.text.lower():
                print("❌ Cloudflare блокирует запрос!")
                print("💡 Установите cloudscraper: pip install cloudscraper")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлекаем данные
            specs = self._parse_page(soup, url)
            
            if specs:
                print(f"✅ Успешно извлечено {len(specs.specifications)} характеристик")
            
            return specs
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None
    
    def parse_car(self, brand: str, model: str, year: int, car_id: Optional[str] = None) -> Optional[CarSpecs]:
        """
        Полный цикл парсинга
        
        Args:
            brand: Марка
            model: Модель
            year: Год
            car_id: ID на сайте (если известен)
        
        Returns:
            Объект CarSpecs
        """
        # Если car_id не указан, пробуем найти
        if not car_id:
            car_id = self.search_car_id(brand, model, year)
            
            if not car_id:
                print("❌ Не удалось найти автомобиль")
                print("💡 Укажите car_id вручную или найдите его на сайте")
                return None
        
        # Формируем URL
        url = self.get_car_url(brand, model, year, car_id)
        
        # Парсим
        return self.parse_direct_url(url)
    
    def _parse_page(self, soup: BeautifulSoup, url: str) -> Optional[CarSpecs]:
        """Парсинг HTML страницы"""
        
        # Извлекаем заголовок
        h1 = soup.find('h1')
        if not h1:
            return None
        
        version = h1.get_text(strip=True)
        
        # Парсим версию
        match = re.match(r'(\d{4})\s+([A-Za-z\-]+)\s+(.+?)(?:\s*\(|$)', version)
        
        if match:
            year = int(match.group(1))
            brand = match.group(2)
            model = match.group(3).strip()
        else:
            # Из URL
            parts = url.split('/')
            year = int(parts[4])
            car_name = parts[6].replace('.html', '').split('_')
            brand = car_name[0].upper()
            model = '_'.join(car_name[1:])
        
        # Извлекаем все характеристики
        specifications = {}
        
        # Ищем таблицы
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if key and value and key != value:
                        specifications[key] = value
        
        # Создаем объект
        specs = CarSpecs(
            brand=brand,
            model=model,
            year=year,
            version=version,
            url=url,
            specifications=specifications
        )
        
        # Извлекаем ключевые характеристики
        specs = self._extract_key_specs(specs)
        
        return specs
    
    def _extract_key_specs(self, specs: CarSpecs) -> CarSpecs:
        """Извлечь ключевые характеристики из общего словаря"""
        
        for key, value in specs.specifications.items():
            key_lower = key.lower()
            
            # Мощность
            if 'power' in key_lower and ('hp' in key_lower or 'horsepower' in key_lower):
                specs.engine_power = value
            
            # Объем
            elif 'displacement' in key_lower or 'engine size' in key_lower:
                specs.engine_displacement = value
            
            # КПП
            elif 'transmission' in key_lower or 'gearbox' in key_lower:
                specs.transmission = value
            
            # Кузов
            elif 'body type' in key_lower:
                specs.body_type = value
            
            # Разгон
            elif '0-100' in key_lower and 'km/h' in key_lower:
                specs.acceleration_0_100 = value
            elif '0-60' in key_lower and 'mph' in key_lower:
                # Конвертируем в 0-100 км/ч приблизительно
                if not specs.acceleration_0_100:
                    specs.acceleration_0_100 = value + " (0-60 mph)"
            
            # Скорость
            elif 'top speed' in key_lower or 'maximum speed' in key_lower:
                specs.top_speed = value
        
        return specs
    
    def save_to_json(self, specs: CarSpecs, filename: str):
        """Сохранить в JSON"""
        data = asdict(specs)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Сохранено: {filename}")
    
    def print_specs(self, specs: CarSpecs):
        """Вывести характеристики"""
        
        print("\n" + "=" * 80)
        print(f"📊 {specs.version}")
        print("=" * 80)
        
        print(f"\n🚗 Основное:")
        print(f"  Марка: {specs.brand}")
        print(f"  Модель: {specs.model}")
        print(f"  Год: {specs.year}")
        
        if specs.body_type:
            print(f"  Кузов: {specs.body_type}")
        
        print(f"\n⚙️ Характеристики:")
        if specs.engine_power:
            print(f"  Мощность: {specs.engine_power}")
        if specs.engine_displacement:
            print(f"  Объем: {specs.engine_displacement}")
        if specs.transmission:
            print(f"  КПП: {specs.transmission}")
        if specs.acceleration_0_100:
            print(f"  0-100 км/ч: {specs.acceleration_0_100}")
        if specs.top_speed:
            print(f"  Макс. скорость: {specs.top_speed}")
        
        print(f"\n📋 Всего характеристик: {len(specs.specifications)}")
        
        print(f"\n🔗 URL: {specs.url}")
        print("=" * 80 + "\n")


def main():
    """Пример использования"""
    
    print("\n" + "🚗" * 40)
    print("\nCLOUDSCRAPER PARSER - Обход Cloudflare без Selenium\n")
    print("🚗" * 40 + "\n")
    
    parser = CloudscraperParser()
    
    # Пример 1: BMW M5 F90 2019 (поиск car_id)
    print("=" * 80)
    print("ПРИМЕР 1: BMW M5 F90 2019 (автоматический поиск car_id)")
    print("=" * 80 + "\n")
    
    specs1 = parser.parse_car(
        brand="BMW",
        model="M5 F90",
        year=2019
    )
    
    if specs1:
        parser.print_specs(specs1)
        parser.save_to_json(specs1, 'bmw_m5_f90_2019.json')
    
    # Пример 2: С известным car_id
    print("\n" + "=" * 80)
    print("ПРИМЕР 2: BMW 320i 2019 (с car_id)")
    print("=" * 80 + "\n")
    
    specs2 = parser.parse_car(
        brand="BMW",
        model="320i",
        year=2019,
        car_id="2877140"
    )
    
    if specs2:
        parser.print_specs(specs2)
        parser.save_to_json(specs2, 'bmw_320i_2019.json')
    
    # Пример 3: Прямой URL
    print("\n" + "=" * 80)
    print("ПРИМЕР 3: Прямой URL")
    print("=" * 80 + "\n")
    
    specs3 = parser.parse_direct_url(
        "https://www.automobile-catalog.com/car/2019/2877140/bmw_320i.html"
    )
    
    if specs3:
        print("✅ Успешно!")
    
    print("\n" + "=" * 80)
    print("✅ Готово!")
    print("=" * 80)


if __name__ == "__main__":
    main()
