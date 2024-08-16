"""
Цей модуль відповідає за парсинг HTML-контенту з наданих URL та обробку отриманих даних.

## Імпортовані бібліотеки

- `aiohttp`: Для асинхронних HTTP-запитів.
- `logging`: Для логування.
- `BeautifulSoup`: Для обробки HTML.
- `asyncio`: Для асинхронного програмування.
- `urljoin`: Для створення абсолютних URL.

## Налаштування

- **Логування**: Логи зберігаються у файлі `parser.log`.
- **Конфігурація**: Завантажується з `config.yaml`.

## Функції

### `extract_content(url: str, ignore_list: List[str], code_v1=False)`
Витягує контент з вказаного URL і обробляє його.

**Параметри**:
- `url` (str): URL для парсингу.
- `ignore_list` (List[str]): Список слів, які потрібно ігнорувати.
- `code_v1` (bool): Флаг для визначення версії коду (специфічне оброблення контенту).

**Повертає**:
- dict: Словник з результатами парсингу, включаючи статус, ID, заголовок, контент, URL та код відповіді.

### `parse_sibling_elements_after_h1(title_tag, ignore_list)`
Обробляє всі наступні сусідні елементи після тега `<h1>` на тому ж рівні вкладеності.

**Параметри**:
- `title_tag` (Tag): Тег `<h1>`, після якого потрібно обробити сусідні елементи.
- `ignore_list` (List[str]): Список слів для ігнорування.

**Повертає**:
- List[str]: Список HTML-кодів оброблених елементів.

### `parse_all_elements_after_h1(soup, ignore_list)`
Обробляє всі наступні елементи після тега `<h1>`, включаючи вкладені елементи.

**Параметри**:
- `soup` (BeautifulSoup): Об'єкт BeautifulSoup для HTML документа.
- `ignore_list` (List[str]): Список слів для ігнорування.

**Повертає**:
- List[str]: Список HTML-кодів оброблених елементів.
"""
from typing import List
import aiohttp
import logging
from bs4 import BeautifulSoup
import asyncio
from urllib.parse import urljoin

from data_processing import remove_unwanted_tags, should_ignore, replace_img_tags, clean_html_tags, remove_html_attributes
from utils import get_status_description, load_config

# Налаштування логування
logging.basicConfig(level=logging.INFO, filename='parser.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Завантаження конфігурації
config = load_config('config.yaml')

async def extract_content(url: str, ignore_list: List[str], code_v1=False):
    """
    Витягує контент з вказаного URL і обробляє його.

    Args:
        url (str): URL для парсингу.
        ignore_list (List[str]): Список слів, які потрібно ігнорувати.
        code_v1 (bool): Флаг для визначення версії коду (специфічне оброблення контенту).

    Returns:
        dict: Словник з результатами парсингу, включаючи статус, ID, заголовок, контент, URL та код відповіді.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z Safari/537.36'
    }
    try:
        timeout_time = config.get('timeout_time', 15)
        timeout = aiohttp.ClientTimeout(total=timeout_time)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                status_code = response.status
                status_description = get_status_description(response.status)
                logging.info(status_description)

                if status_code == 200:
                    response_text = await response.text()
                    soup = BeautifulSoup(response_text, 'html.parser')

                    soup = soup.find('body')
                    if soup is None:
                        logging.info('Тег <body> не знайдено, робота по всій сторінці')
                        soup = BeautifulSoup(response_text, 'html.parser')

                    title_tag = soup.find('h1')
                    title_html = title_tag.prettify() if title_tag else '<h1></h1>'
                    title_text = title_tag.get_text(strip=True) if title_tag else 'No Title'

                    content = []
                    if code_v1:
                        if title_tag:
                            # Обходимо всі наступні елементи на тому ж рівні вкладеності дей h1
                            content = await parse_sibling_elements_after_h1(title_tag, ignore_list)
                    else:
                        if title_tag:
                            # Знайти всі елементи після h1
                            content = await parse_all_elements_after_h1(soup, ignore_list)

                    content_html = f'{title_html}{''.join(content)}'

                    content_html = BeautifulSoup(content_html, 'html.parser')
                    # Очищення та обробка HTML контенту
                    content_html = clean_html_tags(content_html)
                    content_html = remove_unwanted_tags(content_html)
                    content_html = remove_html_attributes(content_html)
                    content_html = replace_img_tags(content_html, url)

                    return {
                        'Status Parsing': 'ТАК',
                        'ID': '1.2.',
                        'Title': title_text,
                        'Content': content_html,
                        'URL': url,
                        'Код відповіді': f"{status_description}"
                    }
                else:
                    logging.error(f"Помилка: не вдалося отримати доступ до сторінки {url} (Статус-код: {status_code})")
                    return {
                        'Status Parsing': 'НІ',
                        'ID': '1.2.',
                        'Title': 'No Title',
                        'Content': '',
                        'URL': url,
                        'Код відповіді': f"{status_description}"
                    }
    except asyncio.TimeoutError:
        logging.error(f"Тайм-аут при обробці URL {url}")
        return {
            'Status Parsing': 'НІ',
            'ID': '1.2.',
            'Title': 'No Title',
            'Content': '',
            'URL': url,
            'Код відповіді': 'Тайм-аут при обробці'
        }
    except Exception as e:
        logging.error(f"Помилка при обробці URL {url}: {str(e)}")
        return {
            'Status Parsing': 'НІ',
            'ID': '1.2.',
            'Title': 'No Title',
            'Content': '',
            'URL': url,
            'Код відповіді': 'Помилка при обробці'
        }


async def parse_sibling_elements_after_h1(title_tag, ignore_list):
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




async def parse_all_elements_after_h1(soup, ignore_list):
    """
    Обробляє всі наступні елементи після тега <h1>, включаючи вкладені елементи.

    :param soup: Об'єкт BeautifulSoup для HTML документа.
    :param ignore_list: Список слів для ігнорування.
    :return: Список HTML-кодів оброблених елементів.
    """
    content = []
    title_tag = soup.find('h1')
    if title_tag:
        elements_after_title = title_tag.find_all_next()
        for tag in elements_after_title:
            if tag == title_tag:
                continue
            tag_text = tag.get_text(strip=True)
            if should_ignore(tag_text.lower(), ignore_list):
                break
            content.append(tag.prettify())
    return content



