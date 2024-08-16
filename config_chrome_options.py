from selenium.webdriver.chrome.options import Options

def chrome_options():
    # Налаштування ChromeOptions
    chrome_options = Options()

    # Запуск браузера в прихованому режимі
    # chrome_options.add_argument("--headless")  # Прихований режим
    chrome_options.add_argument("--disable-gpu")  # Вимкнути апаратне прискорення
    chrome_options.add_argument("--no-sandbox")  # Вимкнути пісочницю
    chrome_options.add_argument("--disable-dev-shm-usage")  # Вимкнути спільне використання пам'яті
    chrome_options.add_argument("--disable-extensions")  # Вимкнути розширення
    chrome_options.add_argument("--disable-popup-blocking")  # Вимкнути блокування спливаючих вікон

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")

    # Налаштування проксі (Якщо є )
    # chrome_options.add_argument('--proxy-server=http://your-proxy:port')
    return chrome_options

def setup_browser():
    chrome_opts = chrome_options()
    cookies = [
        {'name': 'cookie_name', 'value': 'cookie_value', 'domain': 'example.com'},
    ]
    ...
    pass
    ...

