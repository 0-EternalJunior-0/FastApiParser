"""Цей файл є початковим і був написаний у стилі спагеті-коду для тестування.
Рекомендується не використовувати цей код у продакшн-середовищі.
Для організації коду краще використовувати основну директорію проекту."""

import asyncio
import http
import time
from typing import List
import zipfile
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from bs4 import BeautifulSoup
import aiohttp
import pandas as pd
import logging
import os
import random
from urllib.parse import urljoin
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import re
import yaml
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


# Ініціалізація FastAPI додатка та шаблонів
app = FastAPI()
templates = Jinja2Templates(directory="../templates")

# Налаштування статичних файлів
static_dir = "static"
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Змінна для зберігання даних
parsed_data = None

# Налаштування логування
logging.basicConfig(level=logging.INFO, filename='parser.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Завантаження конфігурації
def load_config(config_file):
    with open(config_file, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

config = load_config('../config.yaml')


def should_ignore(text: str, ignore_list: List[str]) -> bool:
    """Перевіряє, чи текст містить будь-яке з стоп-слов."""

    # Розділити текст на речення
    sentences = re.split(r'[.!?]', text)

    # Перевірити кожне речення
    for sentence in sentences:
        for phrase in ignore_list:
            # Перевіряємо, чи фраза є у реченні
            if phrase.lower() in sentence.lower():
                print(f"Stopping because phrase '{phrase}' found in sentence: '{sentence.strip()}'")
                return True

    return False


def remove_attributes(tag):
    """Функція для видалення атрибутів з HTML тегів."""
    for attr in list(tag.attrs):
        del tag.attrs[attr]
    return tag

def remove_unwanted_tags(html_content):
    """Видаляє небажані теги і стилі з HTML-контенту."""
    soup = BeautifulSoup(html_content, 'html.parser')
    tags_to_remove = config.get('tags_to_remove', [])

    # Видалити небажані теги
    for tag in soup.find_all(tags_to_remove):
        tag.unwrap()  # видаляє тег, але залишає його вміст

    # Видалити стильові атрибути
    if config.get('remove_style_attributes', False):
        for tag in soup.find_all(True):  # True означає будь-який тег
            if 'style' in tag.attrs:
                del tag.attrs['style']

    return str(soup)

def replace_img_tags(content_html, base_url):
    """Замінює всі теги <img> у HTML-контенті на абсолютні URL."""
    soup = BeautifulSoup(content_html, 'html.parser')

    img_tags = soup.find_all('img')
    for img_tag in img_tags:
        src = img_tag.get('data-lazy-src') or img_tag.get('src')
        if src:
            absolute_url = urljoin(base_url, src)
            img_tag['src'] = absolute_url
            img_tag['data-lazy-src'] = absolute_url  # Заміна data-lazy-src

        # Обробка data-lazy-srcset
        srcset = img_tag.get('data-lazy-srcset')
        if srcset:
            srcset = re.sub(r'https?://[^\s]+', lambda m: urljoin(base_url, m.group(0)), srcset)
            img_tag['data-lazy-srcset'] = srcset

    return str(soup)
def get_status_description(status_code):
    """Повертає опис статус-коду HTTP."""
    description = http.HTTPStatus(status_code).description
    return f"Код відповіді: {status_code} - {description}"
async def extract_content(url: str, ignore_list: List[str], code_v1= False):
    """Витягує контент з URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        timeout_time = config.get('timeout_time', int)
        timeout = aiohttp.ClientTimeout(total=timeout_time)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                status_code = response.status
                status_description = get_status_description(response.status)
                logging.info(status_description)
                if status_code == 200:
                    response_text = await response.text()
                    soup = BeautifulSoup(response_text, 'html.parser')
                    tags_to_del = config.get('tags_to_del', [])

                    # Видалити всі небажані теги
                    for tag_name in tags_to_del:
                        for unwanted in soup.find_all(tag_name):
                            unwanted.decompose()  # Видаляє тег разом із вмістом
                            # Якщо потрібно, видаліть всі теги <head> разом із вмістом
                        for head in soup.find_all('head'):
                            head.decompose()

                    title_tag = soup.find('h1')
                    if title_tag:
                        cleaned_title = remove_attributes(title_tag)
                        title_html = cleaned_title.prettify()
                        title_text = cleaned_title.get_text(strip=True)
                    else:
                        title_html = '<h1></h1>'
                        title_text = 'No Title'

                    content = []

                    if code_v1:
                        if title_tag:
                            elements_after_title = soup.find('h1').find_next_siblings()

                            for tag in elements_after_title:
                                # Виключити текст до h1
                                if tag == title_tag:
                                    continue
                                cleaned_tag = remove_attributes(tag)
                                tag_text = cleaned_tag.get_text(strip=True)
                                if should_ignore(tag_text.lower(), ignore_list):
                                    break
                                content.append(cleaned_tag.prettify())

                    else:
                        if title_tag:
                            # Знайти всі елементи після h1
                            elements_after_title = soup.find('h1').find_all_next()

                            for tag in elements_after_title:
                                # Виключити текст до h1
                                if tag == title_tag:
                                    continue
                                cleaned_tag = remove_attributes(tag)
                                tag_text = cleaned_tag.get_text(strip=True)
                                if should_ignore(tag_text.lower(), ignore_list):
                                    break
                                content.append(cleaned_tag.prettify())


                    content_html = ''.join(content)
                    content_html = remove_unwanted_tags(content_html)  # Додаємо очищення від небажаних тегів
                    content_html_with_images = replace_img_tags(content_html, url)
                    images = soup.find_all('img')
                    image_urls = [urljoin(url, img.get('src')) for img in images if img.get('src')]

                    return {
                        'Status Parsing': 'ТАК',
                        'ID': '1.2.',
                        'Title': title_text.strip(),
                        'Content': title_html + content_html_with_images,
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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Головна сторінка"""
    return templates.TemplateResponse("index.html", {"request": request})

# Оновлений код для збереження результатів парсингу
@app.post("/parse")
async def parse_url(request: Request):
    """Парсинг URL або списку URL"""
    global parsed_data
    form = await request.form()
    url = form.get('url')
    urls = form.get('urls')
    code_v1 = form.get('code_v1') == 'true'
    ignore_list = config.get('ignore_words', [])

    def yield_ID(start_num=2):
        num = start_num
        while True:
            ID = f'1.{num}'
            yield ID
            num += 1

    id_generator = yield_ID()
    # Вибор парсера find_all_next - False find_next_siblings - True
    if url:
        data = await extract_content(url, ignore_list, code_v1=code_v1)
        if data:
            data['ID'] = next(id_generator)
            parsed_data = pd.DataFrame([data])

    elif urls:
        urls = urls.splitlines()
        all_data = []
        for index, url in enumerate(urls):
            # Затримка між запитами
            await asyncio.sleep(random.uniform(0.2, 0.4))  # випадкова затримка між 0.2 та 0.4 секундами
            if url.strip():
                data = await extract_content(url.strip(), ignore_list, code_v1=code_v1)
                if data:
                    data['ID'] = next(id_generator)
                    all_data.append(data)
        if all_data:
            parsed_data = pd.DataFrame(all_data)

    if parsed_data is not None and not parsed_data.empty:
        return templates.TemplateResponse("parsed_result.html", {"request": {}})
    else:
        return HTMLResponse(content="<h1>No data available</h1>", status_code=404)


@app.get("/table", response_class=HTMLResponse)
async def display_table(request: Request):
    """Відображення таблиці"""
    if parsed_data is not None:
        clean_df = parsed_data.map(lambda x: str(x).replace('\n', '').replace('\r', ' '))
        html_table = clean_df.to_html(index=False, border=1, classes='data-table')
        return templates.TemplateResponse("table_view.html", {"request": request, "html_table": html_table})
    else:
        return HTMLResponse(content="<h1>No data available</h1>", status_code=404)

@app.get("/download")
async def download_file(filetype: str = "xlsx"):
    """Завантаження файлів"""
    global parsed_data

    if parsed_data is not None:
        files = []
        try:
            if filetype == "xlsx":
                file_path = f'static/parsed_content_{random.randint(1000, 9999)}.xlsx'
                parsed_data.to_excel(file_path, index=False)
                media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                files.append(file_path)
            elif filetype == "csv":
                file_path = f'static/parsed_content_{random.randint(1000, 9999)}.csv'
                parsed_data.to_csv(file_path, index=False)
                media_type = 'text/csv'
                files.append(file_path)
            elif filetype == "xml":
                for _, row in parsed_data.iterrows():
                    title = row['Title']
                    content = row['Content']
                    file_name = f'static/{title}_{random.randint(1000, 9999)}.xml'
                    xml_data = html_to_xml(content)
                    with open(file_name, 'w', encoding='utf-8') as file:
                        file.write(xml_data)
                    files.append(file_name)
                media_type = 'application/xml'

                # Optional: Create a ZIP file containing all XML files
                zip_file_path = f'static/parsed_content_{random.randint(1000, 9999)}.zip'
                create_zip_archive(files, zip_file_path)
                return FileResponse(
                    path=zip_file_path,
                    media_type='application/zip',
                    filename=os.path.basename(zip_file_path)
                )
            else:
                return HTMLResponse(content="<h1>Unsupported file type</h1>", status_code=400)

            # Return the first file as an example
            return FileResponse(
                path=files[0],
                media_type=media_type,
                filename=os.path.basename(files[0])
            )
        except Exception as e:
            logging.error(f"Error generating file: {e}")
            return HTMLResponse(content=f"<h1>Error generating file: {e}</h1>", status_code=500)
    else:
        return HTMLResponse(content="<h1>No data available</h1>", status_code=404)

def html_to_xml(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    root = ET.Element("root")

    def parse_element(element, parent):
        tag = ET.SubElement(parent, element.name)
        for attr, value in element.attrs.items():
            tag.set(attr, value)
        if element.string:
            tag.text = element.string.strip()
        for child in element.children:
            if isinstance(child, str):
                continue
            parse_element(child, tag)

    parse_element(soup, root)
    return ET.tostring(root, encoding='unicode')

def create_zip_archive(files, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in files:
            zipf.write(file, os.path.basename(file))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
