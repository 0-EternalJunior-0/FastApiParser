import concurrent.futures
import re
import time
from typing import List
import logging
from urllib.parse import urljoin
import aiohttp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
from readability import Document
from data_processing import remove_unwanted_tags, should_ignore, replace_img_tags, clean_html_tags, remove_html_attributes
from utils import get_status_description, load_config
from config_chrome_options import chrome_options


# Налаштування логування
logging.basicConfig(level=logging.INFO, filename='parser.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
status_description = 'Помилка при обробці'
# Завантаження конфігурації
config = load_config('config.yaml')

async def Https_Parser(url: str) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        timeout_time = config.get('timeout_time', 15)
        timeout = aiohttp.ClientTimeout(total=timeout_time)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                status_code = response.status
                global status_description
                status_description = get_status_description(response.status)
                logging.info(status_description)

                if status_code == 200:
                    response_text = await response.text()
                    return response_text
                else:
                    logging.error(f"Помилка: не вдалося отримати доступ до сторінки {url} (Статус-код: {status_code})")
                    return ''

    except Exception as e:
        logging.error(f"Помилка при обробці URL {url}: {str(e)}")
        return ''

def Selenium_Parser(url: str) -> str:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options())
    try:
        driver.get(url)
        time.sleep(3)

        # Прокрутка сторінки
        scroll_duration = 6  # Тривалість прокрутки в секундах
        scroll_speed = 180  # Швидкість прокрутки (в пікселях за один крок)
        start_time = time.time()

        while time.time() - start_time < scroll_duration:
            driver.execute_script(f"window.scrollBy(0, {scroll_speed});")
            time.sleep(0.05)  # Інтервал між прокрутками

        # Отримання HTML сторінки
        time.sleep(1)
        page_source = driver.page_source
    except Exception as e:
        page_source=''
        logging.info('ERROR', e)
    finally:
        driver.close()
        driver.quit()
    return page_source

def process_url_with_selenium(url: str) -> str:
    try:
        return Selenium_Parser(url)
    except Exception as e:
        logging.error(f'Exception occurred in Selenium processing: {e}')
        return ''



async def extract_content(url: str, ignore_list: List[str], code_v: str='0', parser_type='parser_type'):
    """
    Витягує контент з вказаного URL і обробляє його.

    Args:
        url (str): URL для парсингу.
        ignore_list (List[str]): Список слів, які потрібно ігнорувати.
        code_v1 (bool): Флаг для визначення версії коду (специфічне оброблення контенту).

    Returns:
        dict: Словник з результатами парсингу, включаючи статус, ID, заголовок, контент, URL та код відповіді.
        :param parser_type:
        :param url:
        :param ignore_list:
        :param code_v:
    """
    if parser_type == 'https':
        page_source = await Https_Parser(url)
    elif parser_type == 'Selenium':
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            loop = asyncio.get_event_loop()
            page_source = loop.run_in_executor(executor, process_url_with_selenium, url)

    else:
        logging.error(f'Unknown parser type: {parser_type}')


    if page_source == '':
        logging.error(f'Неможливо обробити порожній контент для URL: {url}')
        return {
            'Status Parsing': 'НІ',
            'ID': '1.2.',
            'Title': 'No Title',
            'Content': '',
            'URL': url,
            'Код відповіді': status_description,
            'Image Url_original': '',
            'Image now Url': ''
        }
    try:
        soup = BeautifulSoup(page_source, 'html.parser')

        title_tag = soup.find('h1')
        title_html = title_tag.prettify() if title_tag else '<h1></h1>'
        title_text = title_tag.get_text(strip=True) if title_tag else 'No Title'

        content = []
        if code_v == '0':
            if title_tag:
                # Обходимо всі наступні елементи на тому ж рівні вкладеності дей h1
                content = parse_sibling_elements_after_h1(title_tag, ignore_list)
                content_html = f'{title_html}{''.join(content)}'
        elif code_v == '1':
            if title_tag:
                # Знайти всі елементи після h1
                content = parse_after_h1_remove_after_stopword(soup, ignore_list)
                content_html = f'{title_html}{content}'
        elif code_v == '2':
            content = parse_readability(soup, ignore_list)
            content_html = f'{title_html}{''.join(content)}'

        content_html = BeautifulSoup(content_html, 'html.parser')
        # Очищення та обробка HTML контенту

        content_html = clean_html_tags(content_html)
        content_html = remove_unwanted_tags(content_html)
        content_html = remove_html_attributes(content_html)

        images = content_html.find_all('img')
        image_urls_original = [urljoin(url, img.get('src')) for img in images if img.get('src')]

        images = content_html.find_all('img')
        content_html = replace_img_tags(content_html, url)
        image_urls = [urljoin(url, img.get('src')) for img in images if img.get('src')]
        return {
            'Status Parsing': 'ТАК',
            'ID': '1.2.',
            'Title': title_text,
            'Content': content_html,
            'URL': url,
            'Код відповіді': status_description,
            'Image Url_original': ' \n'.join(image_urls_original),
            'Image now Url': ' \n'.join(image_urls)
        }
    except Exception as e:
        logging.error(f"Помилка при обробці URL {url}: {str(e)}")
        return {
            'Status Parsing': 'НІ',
            'ID': '1.2.',
            'Title': 'No Title',
            'Content': '',
            'URL': url,
            'Код відповіді': status_description,
            'Image Url_original': '',
            'Image now Url': ''
        }

def parse_sibling_elements_after_h1(title_tag: BeautifulSoup, ignore_list: List[str]):
    """
    Обробляє всі наступні сусідні елементи після тега <h1> на тому ж рівні вкладеності.

    :param title_tag: Тег <h1> після якого потрібно обробити сусідні елементи.
    :param ignore_list: Список слів для ігнорування.
    :return: Список HTML-кодів оброблених елементів.
    """
    content = []
    if title_tag:
        elements_after_title = title_tag.find_next_siblings()
        for tag in elements_after_title:
            tag_text = tag.get_text(strip=True)
            if should_ignore(tag_text.lower(), ignore_list):
                break
            content.append(tag.prettify())
    return content

def parse_after_h1_remove_after_stopword(html: BeautifulSoup, ignore_list: List[str]) -> str:
    """
    Обробляє HTML-контент, знаходячи тег <h1>, забираючи все після нього,
    а також видаляючи контент після стоп-слова.

    :param html: Весь HTML-контент як один рядок.
    :param ignore_list: Список стоп-слів.
    :return: Відредагований HTML-контент.
    """
    # Знаходимо перший блок <h1> і все, що йде після нього
    h1_pattern = r'(<h1[^>]*>.*?</h1>)(.*)'
    match = re.search(h1_pattern, str(html), re.DOTALL)

    if match:
        # Все, що йде після <h1>
        after_h1_content = match.group(2)

        # Шукаємо перше стоп-слово і видаляємо все після нього
        for phrase in ignore_list:
            stopword_pattern = re.escape(phrase)
            after_h1_content = re.sub(rf'>*{stopword_pattern}.*', '', after_h1_content, flags=re.DOTALL)
            # Шукаємо перший закриваючий тег '>'
            closing_tag_match = re.search(r'<[^>]*>[^<]*$', after_h1_content, re.DOTALL)
            if closing_tag_match:
                closing_tag_index = closing_tag_match.start()
                # Обрізаємо текст після першого закриваючого тега
                after_h1_content = after_h1_content[:closing_tag_index]

        # Повертаємо об'єднану частину з <h1> і відредагований контент після нього
        html = after_h1_content

    return html


def parse_readability(html: BeautifulSoup, ignore_list: List[str]):
    """
    Парсить HTML-код за допомогою readability для отримання очищеного тексту та додає зображення.

    :param html: HTML-код статті як об'єкт BeautifulSoup.
    :param ignore_list: Список стоп слів, якщо є таке слово, то далі нічого не зберігаємо.
    :return: HTML-код з очищеним текстом та зображеннями.
    """
    html_text = str(html)  # Перетворюємо BeautifulSoup об'єкт в рядок

    # Використовуємо readability для отримання очищеного HTML
    doc = Document(html_text)
    article_html = doc.summary()  # Очищена розмітка тексту

    # Використовуємо BeautifulSoup для парсингу очищеного HTML
    soup = BeautifulSoup(article_html, 'html.parser')

    # Знаходимо всі зображення в оригінальному HTML
    original_soup = BeautifulSoup(html_text, 'html.parser')
    images = original_soup.find_all('img')

    # Додаємо зображення до основного контенту
    content = []
    skip = False
    for tag in soup.find_all(True):  # True знайде всі теги
        tag_text = tag.get_text(strip=True)
        if any(word in tag_text.lower() for word in ignore_list):
            skip = True
        if not skip:
            content.append(tag.prettify())

    # Додаємо зображення в кінець очищеного контенту
    for img in images:
        if img.parent in original_soup.find_all(['p', 'div', 'article', 'section', 'figure', 'header', 'aside']):
            img_tag = BeautifulSoup(str(img), 'html.parser')
            content.append(img_tag.prettify())

    # Форматування фінального HTML
    final_html = ''.join(content)
    return final_html