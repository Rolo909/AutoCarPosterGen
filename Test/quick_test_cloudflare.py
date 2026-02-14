"""
QUICK START DEMO
Быстрый тест обхода Cloudflare на automobile-catalog.com
"""

from playwright.sync_api import sync_playwright
import time

def test_cloudflare_bypass():
    """Простой тест обхода Cloudflare"""
    
    print("\n" + "="*80)
    print("🧪 ТЕСТ ОБХОДА CLOUDFLARE")
    print("="*80 + "\n")
    
    with sync_playwright() as p:
        print("🚀 Запуск браузера...")
        
        # Запускаем браузер (НЕ headless!)
        browser = p.chromium.launch(
            headless=False,  # КРИТИЧНО для обхода CF
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--window-size=1920,1080',
            ]
        )
        
        # Контекст с реалистичными параметрами
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        )
        
        # Убираем navigator.webdriver
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()
        
        # Тестовые URL
        test_urls = [
            "https://www.automobile-catalog.com/",
            "https://www.automobile-catalog.com/model/bmw/3-series_f30_f31.html"
        ]
        
        for url in test_urls:
            print(f"\n📄 Тест: {url}")
            
            try:
                # Переход
                page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # Ждем 5 секунд (Cloudflare проверка обычно занимает 3-5 сек)
                print("⏳ Ожидание Cloudflare (5 сек)...")
                time.sleep(5)
                
                # Проверяем загрузку
                page.wait_for_load_state('networkidle', timeout=10000)
                
                # Получаем контент
                html = page.content()
                
                # Проверяем результат
                if 'cloudflare' in html.lower() and 'challenge' in html.lower():
                    print("❌ ПРОВАЛ: Cloudflare блокирует")
                elif '403' in html or 'Access Denied' in html:
                    print("❌ ПРОВАЛ: Доступ запрещен (403)")
                elif '<h1>' in html and ('BMW' in html or 'catalog' in html.lower()):
                    print("✅ УСПЕХ: Страница загружена!")
                    print(f"   Размер HTML: {len(html)} байт")
                    
                    # Показываем заголовок
                    try:
                        title = page.title()
                        print(f"   Заголовок: {title}")
                    except:
                        pass
                else:
                    print("⚠️ НЕИЗВЕСТНО: Страница загружена, но контент неожиданный")
                    print(f"   Размер HTML: {len(html)} байт")
                
            except Exception as e:
                print(f"❌ ОШИБКА: {e}")
            
            print("-" * 80)
        
        # Финальная проверка: тест anti-bot детекта
        print("\n🔍 ФИНАЛЬНАЯ ПРОВЕРКА АНТИБОТА:")
        
        try:
            # Проверяем webdriver
            webdriver_value = page.evaluate('navigator.webdriver')
            print(f"   navigator.webdriver = {webdriver_value}")
            
            if webdriver_value is None or webdriver_value == 'undefined':
                print("   ✅ webdriver скрыт")
            else:
                print("   ❌ webdriver обнаружен!")
            
            # Проверяем plugins
            plugins = page.evaluate('navigator.plugins.length')
            print(f"   navigator.plugins.length = {plugins}")
            
            if plugins > 0:
                print("   ✅ Плагины присутствуют")
            else:
                print("   ⚠️ Плагины отсутствуют (подозрительно)")
            
            # Проверяем языки
            languages = page.evaluate('navigator.languages')
            print(f"   navigator.languages = {languages}")
            
        except Exception as e:
            print(f"   ⚠️ Ошибка проверки: {e}")
        
        print("\n" + "="*80)
        print("Браузер остается открытым для ручной проверки...")
        print("Нажмите Ctrl+C чтобы закрыть")
        print("="*80 + "\n")
        
        # Держим браузер открытым для визуальной проверки
        try:
            input("Нажмите Enter чтобы закрыть браузер...")
        except KeyboardInterrupt:
            pass
        
        browser.close()
        
        print("\n✅ Тест завершен")


if __name__ == "__main__":
    test_cloudflare_bypass()
