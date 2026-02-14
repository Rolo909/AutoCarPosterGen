"""
Парсер характеристик автомобилей с сайта automobile-catalog.com
Использует современный стек: httpx, selectolax, fake-useragent
"""

import httpx
from selectolax.parser import HTMLParser
from fake_useragent import UserAgent
import json
import re
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from urllib.parse import quote


@dataclass
class CarSpecs:
    """Класс для хранения характеристик автомобиля"""
    # Основная информация
    brand: str
    model: str
    year: int
    version: str
    url: str
    
    # Двигатель
    engine_type: Optional[str] = None
    displacement: Optional[str] = None
    power_kw: Optional[str] = None
    power_hp: Optional[str] = None
    power_ps: Optional[str] = None
    torque_nm: Optional[str] = None
    torque_lbft: Optional[str] = None
    
    # Трансмиссия
    transmission: Optional[str] = None
    drive_type: Optional[str] = None
    
    # Производительность
    acceleration_0_60: Optional[str] = None
    acceleration_0_100: Optional[str] = None
    top_speed: Optional[str] = None
    quarter_mile: Optional[str] = None
    
    # Расход топлива
    fuel_consumption_urban: Optional[str] = None
    fuel_consumption_extra_urban: Optional[str] = None
    fuel_consumption_combined: Optional[str] = None
    fuel_type: Optional[str] = None
    
    # Размеры
    length: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    wheelbase: Optional[str] = None
    weight: Optional[str] = None
    
    # Другое
    body_type: Optional[str] = None
    doors: Optional[str] = None
    seats: Optional[str] = None
    
    # Дополнительные характеристики
    additional_specs: Optional[Dict] = None


class AutomobileCatalogParser:
    """Парсер для сайта automobile-catalog.com"""
    
    BASE_URL = "https://www.automobile-catalog.com"
    
    def __init__(self, timeout: int = 30):
        """
        Инициализация парсера
        
        Args:
            timeout: Таймаут для запросов в секундах
        """
        self.ua = UserAgent()
        self.timeout = timeout
        self.session = None
        
    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки с случайным User-Agent"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
    
    def _init_session(self):
        """Инициализировать HTTP сессию"""
        if self.session is None:
            self.session = httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                http2=True,
                verify=False  # Отключаем проверку SSL для обхода блокировок
            )
    
    def _close_session(self):
        """Закрыть HTTP сессию"""
        if self.session:
            self.session.close()
            self.session = None
    
    def search_car(self, brand: str, model: str, year: int) -> List[Dict]:
        """
        Поиск автомобиля на сайте
        
        Args:
            brand: Марка автомобиля (например, BMW)
            model: Модель (например, 320i)
            year: Год (например, 2019)
            
        Returns:
            Список найденных вариантов автомобиля
        """
        self._init_session()
        
        # Формируем URL для поиска
        search_query = f"{year} {brand} {model}"
        print(f"🔍 Поиск: {search_query}")
        
        # Пробуем найти прямой URL по шаблону
        # Например: /car/2019/2877140/bmw_320i.html
        car_id = self._find_car_id(brand, model, year)
        
        if car_id:
            variants = self._get_car_variants(brand, model, year, car_id)
            return variants
        
        return []
    
    def _find_car_id(self, brand: str, model: str, year: int) -> Optional[str]:
        """
        Найти ID автомобиля через поиск по Google
        
        Returns:
            ID автомобиля или None
        """
        # Используем Google для поиска страницы
        search_url = f"https://www.google.com/search?q=site:automobile-catalog.com+{year}+{brand}+{model}"
        
        try:
            response = self.session.get(search_url, headers=self._get_headers())
            
            if response.status_code == 200:
                # Ищем ссылки на automobile-catalog.com
                pattern = r'automobile-catalog\.com/car/(\d{4})/(\d+)/' + re.escape(brand.lower()) + r'_' + re.escape(model.lower().replace(' ', '_'))
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                
                if matches:
                    return matches[0][1]  # Возвращаем car_id
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
        
        return None
    
    def _get_car_variants(self, brand: str, model: str, year: int, car_id: str) -> List[Dict]:
        """
        Получить список вариантов автомобиля
        
        Returns:
            Список словарей с информацией о вариантах
        """
        variants = []
        
        # Формируем базовый URL
        base_url = f"{self.BASE_URL}/car/{year}/{car_id}/{brand.lower()}_{model.lower().replace(' ', '_')}.html"
        
        variants.append({
            'brand': brand,
            'model': model,
            'year': year,
            'url': base_url,
            'version': f"{brand} {model}"
        })
        
        return variants
    
    def parse_car_page(self, url: str) -> Optional[CarSpecs]:
        """
        Парсинг страницы автомобиля
        
        Args:
            url: URL страницы автомобиля
            
        Returns:
            Объект CarSpecs с характеристиками или None
        """
        self._init_session()
        
        print(f"📄 Парсинг страницы: {url}")
        
        try:
            response = self.session.get(url, headers=self._get_headers())
            
            if response.status_code != 200:
                print(f"❌ Ошибка {response.status_code}: не удалось загрузить страницу")
                return None
            
            tree = HTMLParser(response.text)
            
            # Извлекаем базовую информацию из URL и заголовка
            specs = self._extract_basic_info(url, tree)
            
            # Извлекаем характеристики из таблиц
            specs = self._extract_specs_from_tables(tree, specs)
            
            # Извлекаем производительность
            specs = self._extract_performance(tree, specs)
            
            return specs
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_basic_info(self, url: str, tree: HTMLParser) -> CarSpecs:
        """Извлечь базовую информацию из URL и страницы"""
        # Парсим URL: /car/2019/2877140/bmw_320i.html
        url_parts = url.split('/')
        year = int(url_parts[4])
        car_name = url_parts[6].replace('.html', '').split('_')
        brand = car_name[0].upper()
        model = '_'.join(car_name[1:])
        
        # Ищем заголовок с версией
        h1 = tree.css_first('h1')
        version = h1.text().strip() if h1 else f"{brand} {model}"
        
        return CarSpecs(
            brand=brand,
            model=model,
            year=year,
            version=version,
            url=url
        )
    
    def _extract_specs_from_tables(self, tree: HTMLParser, specs: CarSpecs) -> CarSpecs:
        """Извлечь характеристики из таблиц на странице"""
        
        # Ищем все таблицы с данными
        tables = tree.css('table')
        
        for table in tables:
            rows = table.css('tr')
            
            for row in rows:
                cells = row.css('td')
                if len(cells) >= 2:
                    key = cells[0].text().strip().lower()
                    value = cells[1].text().strip()
                    
                    # Маппинг ключей на поля
                    self._map_spec_value(key, value, specs)
        
        return specs
    
    def _map_spec_value(self, key: str, value: str, specs: CarSpecs):
        """Сопоставить ключ с полем в CarSpecs"""
        
        # Двигатель
        if 'displacement' in key or 'engine size' in key:
            specs.displacement = value
        elif 'power' in key and 'kw' in key:
            specs.power_kw = value
        elif 'power' in key and ('hp' in key or 'horsepower' in key):
            specs.power_hp = value
        elif 'power' in key and 'ps' in key:
            specs.power_ps = value
        elif 'torque' in key and 'nm' in key:
            specs.torque_nm = value
        elif 'torque' in key and 'lb' in key:
            specs.torque_lbft = value
        elif 'engine type' in key or 'engine layout' in key:
            specs.engine_type = value
        
        # Трансмиссия
        elif 'transmission' in key or 'gearbox' in key:
            specs.transmission = value
        elif 'drive' in key or 'drivetrain' in key:
            specs.drive_type = value
        
        # Топливо
        elif 'fuel type' in key:
            specs.fuel_type = value
        elif 'urban' in key and 'fuel' in key:
            specs.fuel_consumption_urban = value
        elif 'extra-urban' in key or 'highway' in key:
            specs.fuel_consumption_extra_urban = value
        elif 'combined' in key and 'fuel' in key:
            specs.fuel_consumption_combined = value
        
        # Размеры
        elif 'length' in key:
            specs.length = value
        elif 'width' in key:
            specs.width = value
        elif 'height' in key:
            specs.height = value
        elif 'wheelbase' in key:
            specs.wheelbase = value
        elif 'weight' in key or 'curb weight' in key:
            specs.weight = value
        
        # Кузов
        elif 'body type' in key:
            specs.body_type = value
        elif 'doors' in key:
            specs.doors = value
        elif 'seats' in key:
            specs.seats = value
    
    def _extract_performance(self, tree: HTMLParser, specs: CarSpecs) -> CarSpecs:
        """Извлечь данные о производительности"""
        
        # Ищем секцию с производительностью
        performance_section = tree.css('div.performance, table.performance')
        
        for section in performance_section:
            text = section.text()
            
            # 0-60 mph
            match = re.search(r'0-60\s*mph[:\s]*([\d.]+)\s*sec', text, re.IGNORECASE)
            if match:
                specs.acceleration_0_60 = match.group(1) + ' sec'
            
            # 0-100 km/h
            match = re.search(r'0-100\s*km/h[:\s]*([\d.]+)\s*sec', text, re.IGNORECASE)
            if match:
                specs.acceleration_0_100 = match.group(1) + ' sec'
            
            # Top speed
            match = re.search(r'top speed[:\s]*([\d]+)\s*km/h', text, re.IGNORECASE)
            if match:
                specs.top_speed = match.group(1) + ' km/h'
            
            # Quarter mile
            match = re.search(r'quarter mile[:\s]*([\d.]+)\s*sec', text, re.IGNORECASE)
            if match:
                specs.quarter_mile = match.group(1) + ' sec'
        
        return specs
    
    def parse_car(self, brand: str, model: str, year: int) -> Optional[CarSpecs]:
        """
        Полный цикл: поиск и парсинг автомобиля
        
        Args:
            brand: Марка (например, BMW)
            model: Модель (например, 320i)
            year: Год (например, 2019)
            
        Returns:
            Объект CarSpecs с характеристиками
        """
        try:
            # Поиск автомобиля
            variants = self.search_car(brand, model, year)
            
            if not variants:
                print(f"❌ Автомобиль {year} {brand} {model} не найден")
                return None
            
            print(f"✅ Найдено вариантов: {len(variants)}")
            
            # Берем первый вариант
            first_variant = variants[0]
            
            # Парсим страницу
            specs = self.parse_car_page(first_variant['url'])
            
            return specs
            
        finally:
            self._close_session()
    
    def save_to_json(self, specs: CarSpecs, filename: str):
        """
        Сохранить характеристики в JSON файл
        
        Args:
            specs: Объект с характеристиками
            filename: Имя файла для сохранения
        """
        data = asdict(specs)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Данные сохранены в {filename}")


def main():
    """Пример использования парсера"""
    
    parser = AutomobileCatalogParser(timeout=30)
    
    # Пример 1: BMW 320i 2019
    print("=" * 60)
    print("ПРИМЕР 1: BMW 320i 2019")
    print("=" * 60)
    
    specs = parser.parse_car(
        brand="BMW",
        model="320i",
        year=2019
    )
    
    if specs:
        print("\n📊 ХАРАКТЕРИСТИКИ:")
        print(f"Марка: {specs.brand}")
        print(f"Модель: {specs.model}")
        print(f"Год: {specs.year}")
        print(f"Версия: {specs.version}")
        print(f"URL: {specs.url}")
        
        if specs.power_hp:
            print(f"Мощность: {specs.power_hp} HP")
        if specs.displacement:
            print(f"Объем: {specs.displacement}")
        if specs.transmission:
            print(f"КПП: {specs.transmission}")
        if specs.acceleration_0_100:
            print(f"0-100 км/ч: {specs.acceleration_0_100}")
        if specs.top_speed:
            print(f"Макс. скорость: {specs.top_speed}")
        
        # Сохраняем в JSON
        parser.save_to_json(specs, 'bmw_320i_2019.json')
    
    print("\n" + "=" * 60)
    
    # Пример 2: Mercedes-Benz C-Class
    print("\nПРИМЕР 2: Mercedes-Benz C300 2020")
    print("=" * 60)
    
    specs2 = parser.parse_car(
        brand="Mercedes-Benz",
        model="C300",
        year=2020
    )
    
    if specs2:
        print("\n📊 ХАРАКТЕРИСТИКИ:")
        print(f"Версия: {specs2.version}")
        print(f"Мощность: {specs2.power_hp} HP" if specs2.power_hp else "Мощность: N/A")
        
        parser.save_to_json(specs2, 'mercedes_c300_2020.json')


if __name__ == "__main__":
    main()
