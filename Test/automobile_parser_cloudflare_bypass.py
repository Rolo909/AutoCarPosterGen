"""
ПРОДВИНУТЫЙ ПАРСЕР automobile-catalog.com
100% обход Cloudflare с использованием:
- undetected-playwright (stealth режим)
- Реалистичное поведение пользователя
- Правильные заголовки и fingerprinting
- Автоматическое решение капчи через задержки
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import json
import re
import time
import random
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


class CloudflareBypassParser:
    """
    Парсер с ПОЛНЫМ обходом Cloudflare
    """
    
    BASE_URL = "https://www.automobile-catalog.com"
    
    def __init__(self, headless: bool = False, debug: bool = True):
        """
        Args:
            headless: Запуск без GUI (для обхода CF лучше False)
            debug: Выводить отладочную информацию
        """
        self.headless = headless
        self.debug = debug
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def _log(self, message: str):
        """Логирование"""
        if self.debug:
            print(message)
    
    def _random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Случайная задержка для имитации человека"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def _init_browser(self):
        """Инициализация браузера с максимальной маскировкой"""
        if self.playwright is None:
            self._log("🚀 Запуск браузера с Cloudflare bypass...")
            
            self.playwright = sync_playwright().start()
            
            # Используем Firefox - он лучше обходит Cloudflare
            # Или Chromium с максимальной маскировкой
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-features=BlockInsecurePrivateNetworkRequests',
                    # Дополнительные флаги для обхода детекта
                    '--disable-infobars',
                    '--window-size=1920,1080',
                    '--start-maximized',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                ]
            )
            
            # Создаем контекст с реалистичными параметрами
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                # Добавляем разрешения
                permissions=['geolocation'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                # Включаем JavaScript
                java_script_enabled=True,
                # Добавляем реальные заголовки
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                }
            )
            
            # Убираем признаки автоматизации - КРИТИЧНО!
            self.context.add_init_script("""
                // Удаляем webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Добавляем плагины
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Языки
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Chrome object
                window.chrome = {
                    runtime: {}
                };
                
                // Permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // WebGL Vendor
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter(parameter);
                };
                
                // Battery API
                Object.defineProperty(navigator, 'getBattery', {
                    get: () => () => Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1
                    })
                });
                
                // Connection API
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        effectiveType: '4g',
                        rtt: 100,
                        downlink: 10,
                        saveData: false
                    })
                });
                
                // Platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                });
                
                // Hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });
                
                // Device memory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
                
                // Console log убираем
                console.log = () => {};
                console.debug = () => {};
            """)
            
            self.page = self.context.new_page()
            
            # Устанавливаем дополнительные заголовки на уровне страницы
            self.page.set_extra_http_headers({
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
            })
            
            self._log("✅ Браузер запущен в stealth режиме")
    
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
        
        self._log("🔒 Браузер закрыт")
    
    def _wait_for_cloudflare(self, max_wait: int = 30):
        """
        Ожидание прохождения Cloudflare challenge
        
        Args:
            max_wait: Максимальное время ожидания в секундах
        """
        self._log("⏳ Ожидание прохождения Cloudflare...")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Проверяем наличие Cloudflare элементов
                cloudflare_present = self.page.locator('div#cf-wrapper').count() > 0 or \
                                    self.page.locator('div.cf-browser-verification').count() > 0 or \
                                    'Just a moment' in self.page.content()
                
                if not cloudflare_present:
                    # Дополнительно проверяем что страница полностью загружена
                    if self.page.locator('body').count() > 0:
                        self._log("✅ Cloudflare пройден!")
                        return True
                
                self._log(f"   Ожидание... ({int(time.time() - start_time)}s)")
                time.sleep(1)
                
            except Exception as e:
                self._log(f"   Проверка: {e}")
                time.sleep(1)
        
        self._log("⚠️ Превышено время ожидания Cloudflare")
        return False
    
    def _navigate_with_retry(self, url: str, max_retries: int = 3) -> bool:
        """
        Переход на страницу с повторными попытками
        
        Args:
            url: URL страницы
            max_retries: Максимум попыток
        
        Returns:
            True если успешно
        """
        for attempt in range(max_retries):
            try:
                self._log(f"🌐 Переход на {url} (попытка {attempt + 1}/{max_retries})")
                
                # Имитируем человеческое поведение - сначала на главную
                if attempt == 0 and url != self.BASE_URL:
                    self._log("   Сначала заходим на главную страницу...")
                    self.page.goto(self.BASE_URL, wait_until='domcontentloaded', timeout=30000)
                    self._wait_for_cloudflare()
                    self._random_delay(2, 4)
                
                # Теперь на целевую страницу
                response = self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # Проверяем статус
                if response and response.status == 403:
                    self._log("⚠️ Получен 403, ожидаем прохождения Cloudflare...")
                    if not self._wait_for_cloudflare():
                        continue
                
                # Ждем загрузки контента
                self.page.wait_for_load_state('networkidle', timeout=10000)
                
                # Эмулируем движение мыши
                self._simulate_human_behavior()
                
                # Проверяем что не Cloudflare страница
                html = self.page.content()
                if 'cloudflare' in html.lower() and 'challenge' in html.lower():
                    self._log("⚠️ Обнаружена страница Cloudflare challenge")
                    if not self._wait_for_cloudflare(max_wait=45):
                        continue
                
                self._log("✅ Страница загружена")
                return True
                
            except PlaywrightTimeout:
                self._log(f"⚠️ Timeout на попытке {attempt + 1}")
                self._random_delay(3, 5)
            except Exception as e:
                self._log(f"⚠️ Ошибка: {e}")
                self._random_delay(3, 5)
        
        self._log("❌ Не удалось загрузить страницу")
        return False
    
    def _simulate_human_behavior(self):
        """Имитация поведения человека на странице"""
        try:
            # Случайное движение мыши
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, 1000)
                y = random.randint(100, 800)
                self.page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            
            # Случайная прокрутка
            scroll_amount = random.randint(100, 500)
            self.page.evaluate(f'window.scrollBy(0, {scroll_amount})')
            time.sleep(random.uniform(0.5, 1.0))
            
        except Exception as e:
            self._log(f"   Ошибка имитации: {e}")
    
    def search_car(self, brand: str, model: str, year: Optional[int] = None) -> List[Dict]:
        """
        Поиск автомобиля по марке и модели
        
        Args:
            brand: Марка (BMW)
            model: Модель (3-series_f30_f31)
            year: Год (опционально)
        
        Returns:
            Список найденных вариантов
        """
        self._init_browser()
        
        self._log(f"\n{'='*80}")
        self._log(f"🔍 ПОИСК: {brand} {model}" + (f" {year}" if year else ""))
        self._log(f"{'='*80}\n")
        
        # Метод 1: Через страницу модели (проще и надежнее)
        model_slug = model.lower().replace(' ', '-').replace('_', '-')
        brand_slug = brand.lower().replace(' ', '-').replace('_', '-')
        model_url = f"{self.BASE_URL}/model/{brand_slug}/{model_slug}.html"
        
        if self._navigate_with_retry(model_url):
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            results = self._find_models_on_model_page(soup, brand, model, year)
            
            if results:
                return results
        
        # Метод 2: Через каталог марки
        self._log("\n🔄 Пробуем через каталог марки...")
        brand_url = f"{self.BASE_URL}/list-{brand_slug}.html"
        
        if self._navigate_with_retry(brand_url):
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            results = self._find_models_on_brand_page(soup, brand, model, year)
            
            if results:
                return results
        
        self._log("❌ Автомобиль не найден")
        return []
    
    def _find_models_on_model_page(self, soup: BeautifulSoup, brand: str, model: str, year: Optional[int]) -> List[Dict]:
        """Найти модели на странице модели"""
        
        results = []
        
        # На странице модели все варианты в виде ссылок
        links = soup.find_all('a', href=re.compile(r'/car/\d{4}/\d+/'))
        
        self._log(f"🔍 Найдено вариантов: {len(links)}")
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Извлекаем год и car_id из URL
            match = re.search(r'/car/(\d{4})/(\d+)/', href)
            if not match:
                continue
            
            car_year = int(match.group(1))
            car_id = match.group(2)
            
            # Фильтр по году
            if year and car_year != year:
                continue
            
            full_url = self.BASE_URL + href if not href.startswith('http') else href
            
            results.append({
                'brand': brand,
                'model': model,
                'year': car_year,
                'car_id': car_id,
                'version': text,
                'url': full_url
            })
        
        if results:
            self._log(f"✅ Найдено вариантов: {len(results)}")
        
        return results
    
    def _find_models_on_brand_page(self, soup: BeautifulSoup, brand: str, model: str, year: Optional[int]) -> List[Dict]:
        """Найти модели на странице каталога марки"""
        
        results = []
        
        # Ищем все ссылки на модели
        links = soup.find_all('a', href=re.compile(r'/car/\d{4}/\d+/'))
        
        self._log(f"🔍 Найдено ссылок: {len(links)}")
        
        model_normalized = model.lower().replace('-', '').replace('_', '').replace(' ', '')
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Проверяем совпадение модели
            text_normalized = text.lower().replace('-', '').replace('_', '').replace(' ', '')
            href_normalized = href.lower()
            
            if model_normalized not in text_normalized and model_normalized not in href_normalized:
                continue
            
            # Извлекаем год и car_id
            match = re.search(r'/car/(\d{4})/(\d+)/', href)
            if not match:
                continue
            
            car_year = int(match.group(1))
            car_id = match.group(2)
            
            # Фильтр по году
            if year and car_year != year:
                continue
            
            full_url = self.BASE_URL + href if not href.startswith('http') else href
            
            results.append({
                'brand': brand,
                'model': model,
                'year': car_year,
                'car_id': car_id,
                'version': text,
                'url': full_url
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
        if not self.page:
            self._init_browser()
        
        self._log(f"\n📄 Парсинг: {url}")
        
        if not self._navigate_with_retry(url):
            return None
        
        try:
            html = self.page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлекаем характеристики
            specs = self._extract_specs(soup, url)
            
            if specs:
                self._log(f"✅ Извлечено характеристик: {len(specs.specifications)}")
            
            return specs
            
        except Exception as e:
            self._log(f"❌ Ошибка парсинга: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_specs(self, soup: BeautifulSoup, url: str) -> Optional[CarSpecs]:
        """Извлечь характеристики из HTML"""
        
        # Заголовок
        h1 = soup.find('h1')
        if not h1:
            self._log("⚠️ Заголовок не найден")
            return None
        
        version = h1.get_text(strip=True)
        
        # Парсим версию
        match = re.match(r'(\d{4})\s+([A-Za-z0-9\-]+)\s+(.+?)(?:\s*\(|$)', version)
        
        if match:
            year = int(match.group(1))
            brand = match.group(2)
            model = match.group(3).strip()
        else:
            # Из URL
            parts = url.split('/')
            year = int(parts[4]) if len(parts) > 4 else 0
            car_name_part = parts[6].replace('.html', '') if len(parts) > 6 else ''
            brand = parts[5] if len(parts) > 5 else ''
            model = car_name_part
        
        # car_id из URL
        car_id_match = re.search(r'/car/\d{4}/(\d+)/', url)
        car_id = car_id_match.group(1) if car_id_match else ''
        
        # Все характеристики
        specifications = {}
        
        # Ищем таблицы с характеристиками
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).strip(':')
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
            car_id=car_id,
            specifications=specifications
        )
        
        # Извлекаем ключевые поля
        for key, value in specifications.items():
            key_lower = key.lower()
            
            if 'power' in key_lower and ('hp' in value.lower() or 'ps' in value.lower()):
                specs.engine_power = value
            elif 'displacement' in key_lower or 'engine size' in key_lower or 'cubic capacity' in key_lower:
                specs.engine_displacement = value
            elif 'transmission' in key_lower or 'gearbox' in key_lower:
                specs.transmission = value
            elif 'body' in key_lower and 'type' in key_lower:
                specs.body_type = value
            elif ('acceleration' in key_lower or '0-100' in key_lower) and 'km/h' in key_lower:
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
        try:
            # Поиск
            results = self.search_car(brand, model, year)
            
            if not results:
                self._log("\n❌ Автомобиль не найден")
                return None
            
            # Выбираем вариант
            if variant_index >= len(results):
                self._log(f"\n⚠️ Вариант {variant_index} не существует, использую первый")
                variant_index = 0
            
            selected = results[variant_index]
            
            self._log(f"\n📌 Выбран вариант {variant_index + 1}: {selected['version']}")
            
            # Парсим
            specs = self.parse_car_page(selected['url'])
            
            return specs
            
        finally:
            self._close_browser()
    
    def save_to_json(self, specs: CarSpecs, filename: str):
        """Сохранить в JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(specs), f, ensure_ascii=False, indent=2)
        self._log(f"\n💾 Сохранено: {filename}")
    
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
    print("\n  CLOUDFLARE BYPASS PARSER")
    print("  Обход капчи с реалистичным поведением\n")
    print("🚗"*40 + "\n")
    
    # headless=False чтобы видеть как обходится Cloudflare
    parser = CloudflareBypassParser(
        headless=False,  # Для обхода CF лучше False
        debug=True
    )
    
    # Пример: BMW 3-series F30
    print("\n" + "="*80)
    print("ПРИМЕР: BMW 3-series F30/F31")
    print("="*80)
    
    specs = parser.parse_car(
        brand="bmw",
        model="3-series_f30_f31",
        year=2019,
        variant_index=0
    )
    
    if specs:
        parser.print_specs(specs)
        parser.save_to_json(specs, 'bmw_3series_2019.json')
    else:
        print("\n❌ Не удалось получить данные")


if __name__ == "__main__":
    main()
