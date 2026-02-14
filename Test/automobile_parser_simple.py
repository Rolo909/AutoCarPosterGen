"""
Упрощенная версия парсера automobile-catalog.com
Для работы требуется знать прямой URL или car_id автомобиля
"""

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


class SimpleAutoCatalogParser:
    """Простой парсер для automobile-catalog.com"""
    
    BASE_URL = "https://www.automobile-catalog.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_car_url(self, brand: str, model: str, year: int, car_id: str) -> str:
        """
        Получить URL автомобиля
        
        Args:
            brand: Марка (BMW)
            model: Модель (320i)
            year: Год (2019)
            car_id: ID автомобиля на сайте (2877140)
        
        Returns:
            URL страницы
        """
        brand_slug = brand.lower().replace(' ', '-')
        model_slug = model.lower().replace(' ', '_')
        
        return f"{self.BASE_URL}/car/{year}/{car_id}/{brand_slug}_{model_slug}.html"
    
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
            # Делаем запрос с задержкой
            time.sleep(1)
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ Ошибка {response.status_code}")
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
    
    def _parse_page(self, soup: BeautifulSoup, url: str) -> Optional[CarSpecs]:
        """Парсинг HTML страницы"""
        
        # Извлекаем заголовок
        h1 = soup.find('h1')
        if not h1:
            return None
        
        version = h1.get_text(strip=True)
        
        # Парсим версию
        match = re.match(r'(\d{4})\s+([A-Za-z\-]+)\s+([A-Za-z0-9\-]+)', version)
        
        if match:
            year = int(match.group(1))
            brand = match.group(2)
            model = match.group(3)
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
                    
                    if key and value:
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
            if 'power' in key_lower and 'hp' in key_lower:
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
            
            # Скорость
            elif 'top speed' in key_lower:
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
        
        print(f"\nОсновное:")
        print(f"  Марка: {specs.brand}")
        print(f"  Модель: {specs.model}")
        print(f"  Год: {specs.year}")
        
        if specs.engine_power:
            print(f"  Мощность: {specs.engine_power}")
        if specs.engine_displacement:
            print(f"  Объем: {specs.engine_displacement}")
        if specs.transmission:
            print(f"  КПП: {specs.transmission}")
        if specs.body_type:
            print(f"  Кузов: {specs.body_type}")
        if specs.acceleration_0_100:
            print(f"  0-100 км/ч: {specs.acceleration_0_100}")
        if specs.top_speed:
            print(f"  Макс. скорость: {specs.top_speed}")
        
        print(f"\nВсего характеристик: {len(specs.specifications)}")
        
        print(f"\nПолный список:")
        for key, value in specs.specifications.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 80)


def main():
    """Пример использования"""
    
    parser = SimpleAutoCatalogParser()
    
    print("🚀 ПРОСТОЙ ПАРСЕР AUTOMOBILE-CATALOG.COM")
    print("=" * 80)
    
    # ПРИМЕР 1: BMW 320i 2019 (известный car_id)
    print("\n📌 ПРИМЕР 1: BMW 320i 2019")
    
    url1 = parser.get_car_url(
        brand="BMW",
        model="320i",
        year=2019,
        car_id="2877140"
    )
    
    specs1 = parser.parse_direct_url(url1)
    
    if specs1:
        parser.print_specs(specs1)
        parser.save_to_json(specs1, 'bmw_320i_2019_simple.json')
    
    # ПРИМЕР 2: Прямой URL
    print("\n📌 ПРИМЕР 2: BMW 320d 2019 (прямой URL)")
    
    url2 = "https://www.automobile-catalog.com/car/2019/2765390/bmw_320d.html"
    
    specs2 = parser.parse_direct_url(url2)
    
    if specs2:
        parser.print_specs(specs2)
        parser.save_to_json(specs2, 'bmw_320d_2019_simple.json')
    
    print("\n✅ Готово!")


if __name__ == "__main__":
    main()
