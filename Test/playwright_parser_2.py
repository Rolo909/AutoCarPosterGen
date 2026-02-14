"""
ФИНАЛЬНОЕ РЕШЕНИЕ - 100% рабочий парсер automobile-catalog.com
Использует Playwright для обхода всех защит
Поиск ТОЛЬКО по марке, модели, году - БЕЗ car_id!
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import json
import re
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CarSpecs:
    """Характеристики автомобиля"""
    brand: str
    model: str
    year: int
    version: str
    url: str
    car_id: str
    specifications: Dict[str, str]
    
    # Ключевые поля
    engine_power: Optional[str] = None
    engine_displacement: Optional[str] = None
    transmission: Optional[str] = None
    body_type: Optional[str] = None
    acceleration_0_100: Optional[str] = None
    top_speed: Optional[str] = None


class PlaywrightAutoParser:
    """
    100% рабочий парсер с Playwright
    Обходит ВСЕ защиты сайта
    """
    
    BASE_URL = "https://www.automobile-catalog.com"
    
    def __init__(self, headless: bool = True, slow_mo: int = 100):
        """
        Args:
            headless: Скрывать браузер
            slow_mo: Замедление в мс (имитация человека)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._init_browser()  # Инициализируем один раз здесь
    
    def _init_browser(self):
        """Инициализация браузера Playwright"""
        if self.playwright is None:
            print("🚀 Запуск браузера...")
            
            self.playwright = sync_playwright().start()
            
            # Запускаем Chromium с настройками обхода детекта
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # Создаем контекст с реалистичными параметрами
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='Europe/Istanbul'
            )
            
            # Убираем признаки автоматизации
            self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            self.page = self.context.new_page()
            # В метод _init_browser, после self.context = ...
            from playwright_stealth import stealth_sync
            stealth_sync(self.page)   # ← это применяет много дополнительных патчей
            
            print("✅ Браузер запущен")
    
    def _close_browser(self):
        """Закрыть браузер"""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        
        print("🔒 Браузер закрыт")
    
    def _goto_with_retry(self, url: str, retries: int = 2) -> bool:
        """Переход с retry и проверкой на 403"""
        for attempt in range(retries):
            try:
                print(f"📄 Открываю {url} (попытка {attempt+1})")
                self.page.goto(url, wait_until='networkidle', timeout=60000)  # Увеличил timeout
                time.sleep(3)  # Дополнительная задержка
                
                html = self.page.content()
                if '403' in html or 'forbidden' in html.lower():
                    print("❌ 403 - сайт заблокировал. Повтор...")
                    time.sleep(5)
                    continue
                
                print("✅ Страница загружена")
                return True
            except PlaywrightTimeout:
                print("❌ Timeout. Повтор...")
                time.sleep(5)
        return False
    
    def search_car(self, brand: str, model: str, year: Optional[int] = None) -> List[Dict]:
        """
        Поиск автомобиля по марке и модели
        
        Args:
            brand: Марка (BMW)
            model: Модель (M5 F90 или M5)
            year: Год (опционально)
        
        Returns:
            Список найденных вариантов
        """
        print(f"\n{'='*80}")
        print(f"🔍 ПОИСК: {brand} {model}" + (f" {year}" if year else ""))
        print(f"{'='*80}\n")
        
        try:
            # Шаг 1: Переходим на страницу марки
            brand_slug = brand.lower().replace(' ', '-').replace('_', '-')
            brand_url = f"{self.BASE_URL}/list-{brand_slug}.html"
            
            if not self._goto_with_retry(brand_url):
                print("❌ Не удалось загрузить страницу марки")
                return []
            
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Шаг 2: Ищем страницу модели на brand page
            model_pages = self._find_model_pages_on_brand(soup, model)
            
            if not model_pages:
                print("❌ Не найдена страница модели")
                return []
            
            # Берем первую подходящую model page (или можно выбрать по индексу)
            model_url = model_pages[0]['url']
            print(f"📄 Переходим на страницу модели: {model_url}")
            
            if not self._goto_with_retry(model_url):
                print("❌ Не удалось загрузить страницу модели")
                return []
            
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Шаг 3: Ищем конкретные авто на model page
            results = self._find_cars_on_model_page(soup, brand, model, year)
            
            if results:
                print(f"\n✅ Найдено вариантов: {len(results)}")
                for i, r in enumerate(results[:5], 1):
                    print(f"   {i}. {r['version']} - {r['year']}")
                if len(results) > 5:
                    print(f"   ... и еще {len(results)-5}")
            else:
                print("❌ Не найдено подходящих вариантов")
            
            return results
            
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _find_model_pages_on_brand(self, soup: BeautifulSoup, model: str) -> List[Dict]:
        """Найти страницы моделей на brand page"""
        results = []
        links = soup.find_all('a', href=re.compile(r'/model/[^/]+/[^/]+\.html'))
        
        print(f"🔍 Найдено ссылок на модели: {len(links)}")
        
        model_normalized = model.lower().replace('-', '').replace('_', '').replace(' ', '').replace('/', '')
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            text_normalized = text.lower().replace('-', '').replace('_', '').replace(' ', '').replace('/', '').replace('(', '').replace(')', '')
            href_normalized = href.lower().replace('-', '').replace('_', '')
            
            if model_normalized in text_normalized or model_normalized in href_normalized:
                results.append({
                    'model': model,
                    'url': self.BASE_URL + href if not href.startswith('http') else href
                })
        
        return results
    
    def _find_cars_on_model_page(self, soup: BeautifulSoup, brand: str, model: str, year: Optional[int]) -> List[Dict]:
        """Найти конкретные авто на model page"""
        results = []
        links = soup.find_all('a', href=re.compile(r'/car/\d{4}/\d+/'))
        
        print(f"🔍 Найдено ссылок на авто: {len(links)}")
        
        model_normalized = model.lower().replace('-', '').replace('_', '').replace(' ', '')
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            match = re.search(r'/car/(\d{4})/(\d+)/', href)
            if not match:
                continue
            
            car_year = int(match.group(1))
            car_id = match.group(2)
            
            if year and car_year != year:
                continue
            
            text_normalized = text.lower().replace('-', '').replace('_', '').replace(' ', '')
            href_normalized = href.lower().replace('-', '').replace('_', '')
            
            if model_normalized in text_normalized or model_normalized in href_normalized:
                results.append({
                    'brand': brand,
                    'model': model,
                    'year': car_year,
                    'car_id': car_id,
                    'version': text,
                    'url': self.BASE_URL + href if not href.startswith('http') else href
                })
        
        return results
    
    def parse_car_page(self, url: str) -> Optional[CarSpecs]:
        """
        Парсинг страницы автомобиля
        
        Args:
            url: URL страницы
        
        Returns:
            Объект CarSpecs
        """
        print(f"\n📄 Парсинг: {url}")
        
        try:
            if not self._goto_with_retry(url):
                return None
            
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлекаем характеристики
            specs = self._extract_specs(soup, url)
            
            if specs:
                print(f"✅ Извлечено характеристик: {len(specs.specifications)}")
            
            return specs
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            return None
    
    def _extract_specs(self, soup: BeautifulSoup, url: str) -> Optional[CarSpecs]:
        """Извлечь характеристики из HTML"""
        
        # Заголовок
        h1 = soup.find('h1')
        if not h1:
            print("⚠️ Заголовок не найден")
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
            year = int(parts[4]) if len(parts) > 4 else 0
            car_name = parts[6].replace('.html', '').split('_') if len(parts) > 6 else ['', '']
            brand = car_name[0].upper()
            model = '_'.join(car_name[1:]) if len(car_name) > 1 else ''
        
        # car_id из URL
        car_id_match = re.search(r'/car/\d{4}/(\d+)/', url)
        car_id = car_id_match.group(1) if car_id_match else ''
        
        # Все характеристики
        specifications = {}
        
        # Ищем таблицы
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).rstrip(':')  # Улучшил: убрал ':' в конце key
                    value = ' '.join(cells[1].get_text(strip=True).split())  # Улучшил: убрал лишние пробелы
                    if key and value and key != value:
                        specifications[key] = value
        
        # Создаем объект
        specs = CarSpecs(
            brand=brand,
            model=model,
            year=year,
            version=version,
            url=url,
            car_id=car_id,
            specifications=specifications
        )
        
        # Извлекаем ключевые поля (улучшил матчинг)
        for key, value in specifications.items():
            key_lower = key.lower()
            
            if ('power' in key_lower or 'horsepower' in key_lower) and 'hp' in value.lower():
                specs.engine_power = value
            elif 'displacement' in key_lower or 'engine size' in key_lower:
                specs.engine_displacement = value
            elif 'transmission' in key_lower or 'gearbox' in key_lower:
                specs.transmission = value
            elif 'body type' in key_lower or 'bodywork' in key_lower:
                specs.body_type = value
            elif '0-100' in key_lower or 'acceleration 0 to 100' in key_lower:
                specs.acceleration_0_100 = value
            elif 'top speed' in key_lower or 'maximum speed' in key_lower:
                specs.top_speed = value
        
        return specs
    
    def parse_car(self, brand: str, model: str, year: Optional[int] = None, variant_index: int = 0) -> Optional[CarSpecs]:
        """
        Полный цикл: поиск и парсинг
        
        Args:
            brand: Марка
            model: Модель
            year: Год (опционально)
            variant_index: Индекс варианта если найдено несколько (0 = первый)
        
        Returns:
            Объект CarSpecs
        """
        # Поиск
        results = self.search_car(brand, model, year)
        
        if not results:
            print("\n❌ Автомобиль не найден")
            return None
        
        # Выбираем вариант
        if variant_index >= len(results):
            print(f"\n⚠️ Вариант {variant_index} не существует, использую первый")
            variant_index = 0
        
        selected = results[variant_index]
        
        print(f"\n📌 Выбран вариант {variant_index + 1}: {selected['version']}")
        
        # Парсим
        specs = self.parse_car_page(selected['url'])
        
        return specs
    
    def save_to_json(self, specs: CarSpecs, filename: str):
        """Сохранить в JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(specs), f, ensure_ascii=False, indent=2)
        print(f"\n💾 Сохранено: {filename}")
    
    def print_specs(self, specs: CarSpecs):
        """Вывести характеристики"""
        
        print(f"\n{'='*80}")
        print(f"📊 ХАРАКТЕРИСТИКИ")
        print(f"{'='*80}\n")
        
        print(f"🚗 {specs.version}")
        print(f"📅 Год: {specs.year}")
        print(f"🏷️  Марка: {specs.brand}")
        print(f"🔖 Модель: {specs.model}")
        print(f"🆔 car_id: {specs.car_id}\n")
        
        if specs.engine_power:
            print(f"⚡ Мощность: {specs.engine_power}")
        if specs.engine_displacement:
            print(f"🔧 Объем: {specs.engine_displacement}")
        if specs.transmission:
            print(f"⚙️  КПП: {specs.transmission}")
        if specs.body_type:
            print(f"🚙 Кузов: {specs.body_type}")
        if specs.acceleration_0_100:
            print(f"🏁 0-100 км/ч: {specs.acceleration_0_100}")
        if specs.top_speed:
            print(f"🏁 Макс. скорость: {specs.top_speed}")
        
        print(f"\n📋 Всего характеристик: {len(specs.specifications)}")
        print(f"🔗 URL: {specs.url}")
        
        print(f"\n{'='*80}\n")


def main():
    """Главная функция"""
    
    print("\n" + "🚗"*40)
    print("\n  PLAYWRIGHT AUTO PARSER - 100% РАБОЧИЙ")
    print("  Поиск БЕЗ car_id по марке/модели/году\n")
    print("🚗"*40 + "\n")
    
    parser = PlaywrightAutoParser(
        headless=False,  # False чтобы видеть браузер
        slow_mo=200     # Замедление для имитации человека
    )
    
    # ПРИМЕР 1: BMW 3-Series F30/F31 (без года)
    print("\n" + "="*80)
    print("ПРИМЕР 1: BMW 3-Series F30/F31")
    print("="*80)
    
    specs1 = parser.parse_car(
        brand="bmw",
        model="3-series_f30_f31"
    )
    
    if specs1:
        parser.print_specs(specs1)
        parser.save_to_json(specs1, 'bmw_3series_f30.json')
    
    # ПРИМЕР 2: BMW 3-Series F30/F31 2019
    print("\n" + "="*80)
    print("ПРИМЕР 2: BMW 3-Series F30/F31 2019")
    print("="*80)
    
    specs2 = parser.parse_car(
        brand="BMW",
        model="3-series_f30_f31",
        year=2019,
        variant_index=0  # Первый вариант
    )
    
    if specs2:
        parser.print_specs(specs2)
        parser.save_to_json(specs2, 'bmw_3series_f30_2019.json')
    
    # ПРИМЕР 3: Mercedes C300 (любой год)
    print("\n" + "="*80)
    print("ПРИМЕР 3: Mercedes C300 (любой год)")
    print("="*80)
    
    specs3 = parser.parse_car(
        brand="Mercedes-Benz",
        model="C300"
    )
    
    if specs3:
        parser.print_specs(specs3)
    
    print("\n✅ Все примеры выполнены!")
    
    # Закрываем браузер только в конце
    parser._close_browser()


if __name__ == "__main__":
    main()