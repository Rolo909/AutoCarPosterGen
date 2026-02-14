"""
Парсер характеристик автомобилей с сайта automobile-catalog.com
Версия с Selenium для обхода Cloudflare и других защит
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import re
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


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
    engine_code: Optional[str] = None
    displacement: Optional[str] = None
    displacement_liters: Optional[str] = None
    cylinders: Optional[str] = None
    configuration: Optional[str] = None
    power_kw: Optional[str] = None
    power_hp: Optional[str] = None
    power_ps: Optional[str] = None
    torque_nm: Optional[str] = None
    torque_lbft: Optional[str] = None
    aspiration: Optional[str] = None
    fuel_system: Optional[str] = None
    
    # Трансмиссия
    transmission: Optional[str] = None
    transmission_type: Optional[str] = None
    gears: Optional[str] = None
    drive_type: Optional[str] = None
    
    # Производительность
    acceleration_0_60_mph: Optional[str] = None
    acceleration_0_100_kmh: Optional[str] = None
    acceleration_0_200_kmh: Optional[str] = None
    top_speed_kmh: Optional[str] = None
    top_speed_mph: Optional[str] = None
    quarter_mile_time: Optional[str] = None
    quarter_mile_speed: Optional[str] = None
    
    # Расход топлива
    fuel_consumption_urban_l: Optional[str] = None
    fuel_consumption_extra_urban_l: Optional[str] = None
    fuel_consumption_combined_l: Optional[str] = None
    fuel_consumption_urban_mpg: Optional[str] = None
    fuel_consumption_extra_urban_mpg: Optional[str] = None
    fuel_consumption_combined_mpg: Optional[str] = None
    fuel_type: Optional[str] = None
    fuel_tank_capacity: Optional[str] = None
    co2_emissions: Optional[str] = None
    
    # Размеры и вес
    length: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    wheelbase: Optional[str] = None
    front_track: Optional[str] = None
    rear_track: Optional[str] = None
    curb_weight: Optional[str] = None
    gross_weight: Optional[str] = None
    max_load: Optional[str] = None
    trunk_space: Optional[str] = None
    
    # Кузов
    body_type: Optional[str] = None
    doors: Optional[str] = None
    seats: Optional[str] = None
    
    # Шасси
    front_suspension: Optional[str] = None
    rear_suspension: Optional[str] = None
    front_brakes: Optional[str] = None
    rear_brakes: Optional[str] = None
    
    # Колеса
    tire_size_front: Optional[str] = None
    tire_size_rear: Optional[str] = None
    wheel_size_front: Optional[str] = None
    wheel_size_rear: Optional[str] = None
    
    # Дополнительно
    production_period: Optional[str] = None
    platform: Optional[str] = None
    generation: Optional[str] = None
    
    # Все остальные характеристики
    raw_specs: Optional[Dict] = None


class AutomobileCatalogSeleniumParser:
    """Парсер для automobile-catalog.com с использованием Selenium"""
    
    BASE_URL = "https://www.automobile-catalog.com"
    
    def __init__(self, headless: bool = True):
        """
        Инициализация парсера
        
        Args:
            headless: Запускать браузер в фоновом режиме
        """
        self.headless = headless
        self.driver = None
        
    def _init_driver(self):
        """Инициализировать Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            # Опции для обхода детектирования автоматизации
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Инициализация драйвера
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Удаляем webdriver флаг
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
    def _close_driver(self):
        """Закрыть WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def construct_url(self, brand: str, model: str, year: int, car_id: str = None) -> str:
        """
        Сконструировать URL для автомобиля
        
        Args:
            brand: Марка (BMW)
            model: Модель (320i)
            year: Год (2019)
            car_id: ID автомобиля на сайте (опционально)
        
        Returns:
            URL страницы
        """
        # Нормализуем имена
        brand_slug = brand.lower().replace(' ', '_').replace('-', '_')
        model_slug = model.lower().replace(' ', '_').replace('-', '_')
        
        if car_id:
            return f"{self.BASE_URL}/car/{year}/{car_id}/{brand_slug}_{model_slug}.html"
        else:
            # Пробуем угадать ID через поиск
            return self._search_car_url(brand, model, year)
    
    def _search_car_url(self, brand: str, model: str, year: int) -> Optional[str]:
        """
        Найти URL автомобиля через внутренний поиск на сайте
        
        Returns:
            URL или None
        """
        self._init_driver()
        
        try:
            # Идем на главную
            self.driver.get(self.BASE_URL)
            time.sleep(2)
            
            # Формируем поисковый запрос
            search_query = f"{year} {brand} {model}"
            
            # Ищем поле поиска (адаптируйте селектор под реальную структуру)
            search_selectors = [
                'input[name="search"]',
                'input[type="search"]',
                'input.gsc-input',
                '#gsc-i-id1',
                '#gsc-i-id2'
            ]
            
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    search_box.clear()
                    search_box.send_keys(search_query)
                    time.sleep(1)
                    
                    # Ищем кнопку поиска
                    search_button = self.driver.find_element(By.CSS_SELECTOR, 'button.gsc-search-button')
                    search_button.click()
                    time.sleep(3)
                    
                    # Ищем результаты
                    results = self.driver.find_elements(By.CSS_SELECTOR, 'div.gsc-result a')
                    
                    for result in results:
                        href = result.get_attribute('href')
                        if href and '/car/' in href and brand.lower() in href.lower():
                            return href
                    
                    break
                except:
                    continue
            
        except Exception as e:
            print(f"⚠️ Ошибка поиска: {e}")
        
        return None
    
    def parse_car_page(self, url: str) -> Optional[CarSpecs]:
        """
        Парсинг страницы автомобиля
        
        Args:
            url: URL страницы
            
        Returns:
            Объект CarSpecs с характеристиками
        """
        self._init_driver()
        
        print(f"📄 Загрузка страницы: {url}")
        
        try:
            self.driver.get(url)
            
            # Ждем загрузки контента
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            
            # Получаем HTML
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # Извлекаем базовую информацию
            specs = self._extract_basic_info(url, soup)
            
            # Извлекаем характеристики
            specs = self._extract_all_specs(soup, specs)
            
            print(f"✅ Характеристики извлечены")
            
            return specs
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_basic_info(self, url: str, soup: BeautifulSoup) -> CarSpecs:
        """Извлечь базовую информацию"""
        
        # Из URL
        parts = url.split('/')
        year = int(parts[4]) if len(parts) > 4 else 0
        
        # Из заголовка
        h1 = soup.find('h1')
        version = h1.get_text(strip=True) if h1 else ""
        
        # Парсим версию для извлечения марки и модели
        # Пример: "2019 BMW 320i (aut. 8)"
        match = re.match(r'(\d{4})\s+([A-Za-z\-]+)\s+([A-Za-z0-9\-]+)', version)
        
        if match:
            year = int(match.group(1))
            brand = match.group(2)
            model = match.group(3)
        else:
            # Пробуем из URL
            car_name = parts[6].replace('.html', '').split('_') if len(parts) > 6 else ['', '']
            brand = car_name[0].upper()
            model = '_'.join(car_name[1:]) if len(car_name) > 1 else ''
        
        return CarSpecs(
            brand=brand,
            model=model,
            year=year,
            version=version,
            url=url,
            raw_specs={}
        )
    
    def _extract_all_specs(self, soup: BeautifulSoup, specs: CarSpecs) -> CarSpecs:
        """Извлечь все характеристики со страницы"""
        
        # Ищем все таблицы с характеристиками
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if key and value:
                        # Сохраняем в raw_specs
                        specs.raw_specs[key] = value
                        
                        # Маппим на конкретные поля
                        self._map_spec(key.lower(), value, specs)
        
        # Ищем дополнительные данные в div-элементах
        spec_divs = soup.find_all('div', class_=re.compile('spec|data|info'))
        
        for div in spec_divs:
            text = div.get_text()
            self._extract_from_text(text, specs)
        
        return specs
    
    def _map_spec(self, key: str, value: str, specs: CarSpecs):
        """Сопоставить ключ со значением"""
        
        # Двигатель
        if 'engine type' in key or 'engine layout' in key:
            specs.engine_type = value
        elif 'engine code' in key:
            specs.engine_code = value
        elif 'displacement' in key or 'engine size' in key:
            specs.displacement = value
            # Извлекаем литры
            match = re.search(r'([\d.]+)\s*l', value, re.IGNORECASE)
            if match:
                specs.displacement_liters = match.group(1)
        elif 'cylinders' in key or 'number of cylinders' in key:
            specs.cylinders = value
        elif 'configuration' in key:
            specs.configuration = value
        elif 'aspiration' in key or 'forced induction' in key:
            specs.aspiration = value
        elif 'fuel system' in key:
            specs.fuel_system = value
        
        # Мощность
        elif 'power' in key:
            if 'kw' in key or 'kilowatt' in key:
                specs.power_kw = value
            elif 'hp' in key or 'horsepower' in key:
                specs.power_hp = value
            elif 'ps' in key:
                specs.power_ps = value
            else:
                # Пробуем извлечь все варианты
                kw_match = re.search(r'([\d.]+)\s*kw', value, re.IGNORECASE)
                hp_match = re.search(r'([\d.]+)\s*hp', value, re.IGNORECASE)
                ps_match = re.search(r'([\d.]+)\s*ps', value, re.IGNORECASE)
                
                if kw_match:
                    specs.power_kw = kw_match.group(1) + ' kW'
                if hp_match:
                    specs.power_hp = hp_match.group(1) + ' hp'
                if ps_match:
                    specs.power_ps = ps_match.group(1) + ' PS'
        
        # Крутящий момент
        elif 'torque' in key:
            if 'nm' in key or 'newton' in key:
                specs.torque_nm = value
            elif 'lb' in key or 'ft' in key:
                specs.torque_lbft = value
            else:
                nm_match = re.search(r'([\d.]+)\s*nm', value, re.IGNORECASE)
                lb_match = re.search(r'([\d.]+)\s*lb', value, re.IGNORECASE)
                
                if nm_match:
                    specs.torque_nm = nm_match.group(1) + ' Nm'
                if lb_match:
                    specs.torque_lbft = lb_match.group(1) + ' lb-ft'
        
        # Трансмиссия
        elif 'transmission' in key or 'gearbox' in key:
            specs.transmission = value
            # Извлекаем тип
            if 'automatic' in value.lower():
                specs.transmission_type = 'Automatic'
            elif 'manual' in value.lower():
                specs.transmission_type = 'Manual'
            # Извлекаем количество передач
            gears_match = re.search(r'(\d+)[-\s]?speed', value, re.IGNORECASE)
            if gears_match:
                specs.gears = gears_match.group(1)
        elif 'drive' in key or 'drivetrain' in key:
            specs.drive_type = value
        
        # Производительность
        elif '0-60' in key and 'mph' in key:
            specs.acceleration_0_60_mph = value
        elif '0-100' in key and 'km' in key:
            specs.acceleration_0_100_kmh = value
        elif '0-200' in key:
            specs.acceleration_0_200_kmh = value
        elif 'top speed' in key:
            if 'km' in value:
                specs.top_speed_kmh = value
            elif 'mph' in value:
                specs.top_speed_mph = value
            else:
                specs.top_speed_kmh = value
        elif 'quarter mile' in key or '1/4 mile' in key:
            specs.quarter_mile_time = value
        
        # Топливо
        elif 'fuel type' in key:
            specs.fuel_type = value
        elif 'fuel tank' in key:
            specs.fuel_tank_capacity = value
        elif 'co2' in key or 'emission' in key:
            specs.co2_emissions = value
        elif 'urban' in key and ('consumption' in key or 'fuel' in key):
            if 'l/' in value or 'liters' in value:
                specs.fuel_consumption_urban_l = value
            elif 'mpg' in value:
                specs.fuel_consumption_urban_mpg = value
        elif ('extra-urban' in key or 'highway' in key) and 'fuel' in key:
            if 'l/' in value or 'liters' in value:
                specs.fuel_consumption_extra_urban_l = value
            elif 'mpg' in value:
                specs.fuel_consumption_extra_urban_mpg = value
        elif 'combined' in key and 'fuel' in key:
            if 'l/' in value or 'liters' in value:
                specs.fuel_consumption_combined_l = value
            elif 'mpg' in value:
                specs.fuel_consumption_combined_mpg = value
        
        # Размеры
        elif key == 'length' or 'overall length' in key:
            specs.length = value
        elif key == 'width' or 'overall width' in key:
            specs.width = value
        elif key == 'height' or 'overall height' in key:
            specs.height = value
        elif 'wheelbase' in key:
            specs.wheelbase = value
        elif 'front track' in key:
            specs.front_track = value
        elif 'rear track' in key:
            specs.rear_track = value
        
        # Вес
        elif 'curb weight' in key or 'kerb weight' in key:
            specs.curb_weight = value
        elif 'gross weight' in key or 'gvwr' in key:
            specs.gross_weight = value
        elif 'max load' in key or 'payload' in key:
            specs.max_load = value
        elif 'trunk' in key or 'boot' in key or 'cargo' in key:
            specs.trunk_space = value
        
        # Кузов
        elif 'body type' in key or 'body style' in key:
            specs.body_type = value
        elif key == 'doors' or 'number of doors' in key:
            specs.doors = value
        elif key == 'seats' or 'seating capacity' in key:
            specs.seats = value
        
        # Подвеска
        elif 'front suspension' in key:
            specs.front_suspension = value
        elif 'rear suspension' in key:
            specs.rear_suspension = value
        
        # Тормоза
        elif 'front brake' in key:
            specs.front_brakes = value
        elif 'rear brake' in key:
            specs.rear_brakes = value
        
        # Колеса
        elif 'front tire' in key or 'front tyre' in key:
            specs.tire_size_front = value
        elif 'rear tire' in key or 'rear tyre' in key:
            specs.tire_size_rear = value
        elif 'front wheel' in key or 'front rim' in key:
            specs.wheel_size_front = value
        elif 'rear wheel' in key or 'rear rim' in key:
            specs.wheel_size_rear = value
        
        # Прочее
        elif 'production' in key or 'years of production' in key:
            specs.production_period = value
        elif 'platform' in key:
            specs.platform = value
        elif 'generation' in key:
            specs.generation = value
    
    def _extract_from_text(self, text: str, specs: CarSpecs):
        """Извлечь данные из текстовых блоков"""
        
        # 0-60 mph
        match = re.search(r'0\s*-?\s*60\s+mph[:\s]*([\d.]+)\s*sec', text, re.IGNORECASE)
        if match and not specs.acceleration_0_60_mph:
            specs.acceleration_0_60_mph = match.group(1) + ' sec'
        
        # 0-100 km/h
        match = re.search(r'0\s*-?\s*100\s+km/h[:\s]*([\d.]+)\s*sec', text, re.IGNORECASE)
        if match and not specs.acceleration_0_100_kmh:
            specs.acceleration_0_100_kmh = match.group(1) + ' sec'
        
        # Top speed
        match = re.search(r'top speed[:\s]*([\d]+)\s*km/h', text, re.IGNORECASE)
        if match and not specs.top_speed_kmh:
            specs.top_speed_kmh = match.group(1) + ' km/h'
    
    def parse_car(self, brand: str, model: str, year: int, car_id: str = None) -> Optional[CarSpecs]:
        """
        Полный цикл парсинга
        
        Args:
            brand: Марка
            model: Модель
            year: Год
            car_id: ID на сайте (опционально)
        
        Returns:
            Объект CarSpecs
        """
        try:
            # Конструируем URL
            url = self.construct_url(brand, model, year, car_id)
            
            if not url:
                print(f"❌ Не удалось найти URL для {year} {brand} {model}")
                return None
            
            # Парсим
            specs = self.parse_car_page(url)
            
            return specs
            
        finally:
            self._close_driver()
    
    def save_to_json(self, specs: CarSpecs, filename: str):
        """Сохранить в JSON"""
        data = asdict(specs)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Сохранено в {filename}")
    
    def print_specs(self, specs: CarSpecs):
        """Красиво вывести характеристики"""
        
        print("\n" + "=" * 80)
        print(f"📊 ХАРАКТЕРИСТИКИ: {specs.version}")
        print("=" * 80)
        
        print(f"\n🚗 ОСНОВНОЕ:")
        print(f"  Марка: {specs.brand}")
        print(f"  Модель: {specs.model}")
        print(f"  Год: {specs.year}")
        print(f"  Тип кузова: {specs.body_type or 'N/A'}")
        print(f"  Двери: {specs.doors or 'N/A'}")
        print(f"  Места: {specs.seats or 'N/A'}")
        
        print(f"\n⚙️ ДВИГАТЕЛЬ:")
        print(f"  Тип: {specs.engine_type or 'N/A'}")
        print(f"  Объем: {specs.displacement or 'N/A'}")
        print(f"  Цилиндры: {specs.cylinders or 'N/A'}")
        print(f"  Мощность: {specs.power_hp or specs.power_kw or specs.power_ps or 'N/A'}")
        print(f"  Крутящий момент: {specs.torque_nm or specs.torque_lbft or 'N/A'}")
        
        print(f"\n🔧 ТРАНСМИССИЯ:")
        print(f"  КПП: {specs.transmission or 'N/A'}")
        print(f"  Привод: {specs.drive_type or 'N/A'}")
        
        print(f"\n🏁 ПРОИЗВОДИТЕЛЬНОСТЬ:")
        print(f"  0-100 км/ч: {specs.acceleration_0_100_kmh or 'N/A'}")
        print(f"  Макс. скорость: {specs.top_speed_kmh or specs.top_speed_mph or 'N/A'}")
        print(f"  1/4 мили: {specs.quarter_mile_time or 'N/A'}")
        
        print(f"\n⛽ ТОПЛИВО:")
        print(f"  Тип: {specs.fuel_type or 'N/A'}")
        print(f"  Расход (город): {specs.fuel_consumption_urban_l or 'N/A'}")
        print(f"  Расход (трасса): {specs.fuel_consumption_extra_urban_l or 'N/A'}")
        print(f"  Расход (смеш.): {specs.fuel_consumption_combined_l or 'N/A'}")
        
        print(f"\n📏 РАЗМЕРЫ:")
        print(f"  Длина: {specs.length or 'N/A'}")
        print(f"  Ширина: {specs.width or 'N/A'}")
        print(f"  Высота: {specs.height or 'N/A'}")
        print(f"  Колесная база: {specs.wheelbase or 'N/A'}")
        print(f"  Снаряженная масса: {specs.curb_weight or 'N/A'}")
        
        print(f"\n🔗 URL: {specs.url}")
        print("=" * 80 + "\n")


def main():
    """Пример использования"""
    
    # Создаем парсер (headless=False для отладки, чтобы видеть браузер)
    parser = AutomobileCatalogSeleniumParser(headless=True)
    
    print("🚀 ПАРСЕР AUTOMOBILE-CATALOG.COM")
    print("=" * 80)
    
    # Пример 1: BMW 320i 2019
    print("\n📌 ПРИМЕР 1: BMW 320i 2019 (aut. 8)")
    
    # Если знаем car_id, можем указать его напрямую
    specs1 = parser.parse_car(
        brand="BMW",
        model="320i",
        year=2019,
        car_id="2877140"  # ID из примера в задании
    )
    
    if specs1:
        parser.print_specs(specs1)
        parser.save_to_json(specs1, 'bmw_320i_2019.json')
    
    # Пример 2: Без car_id (попытка поиска)
    print("\n📌 ПРИМЕР 2: Mercedes-Benz C300 2020")
    
    specs2 = parser.parse_car(
        brand="Mercedes-Benz",
        model="C300",
        year=2020
    )
    
    if specs2:
        parser.print_specs(specs2)
        parser.save_to_json(specs2, 'mercedes_c300_2020.json')
    
    print("\n✅ Парсинг завершен!")


if __name__ == "__main__":
    main()
