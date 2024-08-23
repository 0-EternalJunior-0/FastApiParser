import asyncio
import os
import logging

from bs4 import BeautifulSoup
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import pandas as pd
from fastapi.responses import JSONResponse

from parser import extract_content
from data_processing import convert_data_to_files
from utils import load_config, blacklist, add_unreachable_site, get_google_search_results

# Налаштування статичних файлів
static_dir = 'templates'
os.makedirs(static_dir, exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates/static', exist_ok=True)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
# Налаштування логування
logging.basicConfig(level=logging.INFO, filename='parser.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Завантаження конфігурації
config = load_config('config.yaml')

# Глобальна змінна для зберігання результатів парсингу
parsed_data = pd.DataFrame()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Головна сторінка сайту.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/parse")
async def parse_url(request: Request):
    """
    Парсинг URL або списку URL.

    Args:
        request (Request): HTTP запит з URL або списком URL.

    Returns:
        HTMLResponse: HTML-сторінка з результатами парсингу або повідомленням про відсутність даних.
    """
    global parsed_data
    parsed_data = pd.DataFrame()  # Сброс данных

    form = await request.form()
    url = form.get('url')
    urls = form.get('urls')
    code_v = form.get('code_v', '0')  # Значення за замовчуванням
    parser_type = form.get('parser_type', 'https')  # Значення за замовчуванням
    min_chars = int(form.get('min_chars', 0) ) # Значення за замовчуванням
    max_chars = int(form.get('max_chars', -1))  # Значення за замовчуванням
    ignore_list = config.get('ignore_words', [])

    def yield_ID(start_num=2):
        """
        Генератор для створення унікальних ID.

        Args:
            start_num (int): Початковий номер для генерації ID.

        Yields:
            str: Унікальний ID.
        """
        num = start_num
        while True:
            ID = f'1.{num}'
            yield ID
            num += 1
    def block(url):
        black_list = blacklist('blacklist.txt')
        for url_stop in black_list:
            if url_stop == url:
                logging.info(f'Сайт занесений в blacklist\t\t {url}')
                return False
        return True
    def limit_text(text: BeautifulSoup, min_chars: int, max_chars: int, url: str):
        text_all = ' '.join(text.stripped_strings)
        if len(text_all) < min_chars:
            logging.info(f'Кількість символів занадто мала\t\t{url}')
            return False
        if max_chars != -1 and len(text_all) > max_chars:
            logging.info(f'Кількість символів занадто велика\t\t{url}')
            return False
        return True

    id_generator = yield_ID()
    all_data = []

    def log_unreachable_sites(data):
        if data['Status Parsing'] == 'НІ':
            try:
                domain = data["URL"].split("/")[2]
            except:
                domain = data["URL"]
            add_unreachable_site('Blacklist_Domen.txt', domain)
    def log_ok_parser(data):
        if data['Status Parsing'] == 'ТАК':
            domain = data["URL"]
            add_unreachable_site('Blacklist_Page.txt', domain)

    if url:
        if block(url):
            data = await extract_content(url, ignore_list, code_v=code_v, parser_type=parser_type)
            if data and limit_text(data['Content'], min_chars, max_chars, url):
                data['ID'] = next(id_generator)
                log_ok_parser(data)
                all_data.append(data)
            else:
                logging.error('Не вдалося отримати дані з URL або зміст сайту недійсний')
                log_unreachable_sites(data)
                return HTMLResponse(content="<h1>Не вдалося отримати дані з URL або зміст сайту недійсний</h1>", status_code=404)
        else:
            return HTMLResponse(content="<h1>Сайт занесений в blacklist</h1>", status_code=404)
    elif urls:
        urls = urls.splitlines()
        tasks = []
        urls = [url for url in urls if block(url)]
        for url in urls:
            url = url.strip()
            tasks.append(extract_content(url, ignore_list, code_v=code_v, parser_type=parser_type))
        results = await asyncio.gather(*tasks)
        for data in results:
            if data and limit_text(data['Content'], min_chars, max_chars, url):
                log_ok_parser(data)
                data['ID'] = next(id_generator)
                all_data.append(data)
            else:
                log_unreachable_sites(data)
                logging.error('Не вдалося отримати дані з URL або зміст сайту недійсний')

    if all_data:
        parsed_data = pd.DataFrame(all_data)

    if parsed_data is not None and not parsed_data.empty:
        return templates.TemplateResponse("parsed_result.html", {"request": request})
    else:
        return HTMLResponse(content="<h1>No data available</h1>", status_code=404)

@app.get("/table", response_class=HTMLResponse)
async def display_table(request: Request):
    """
    Відображення таблиці з парсингованими даними.
    """
    if parsed_data is not None:
        parsed_data_table_view = parsed_data
        if config.get('cleaned_data_table_view', False):
            parsed_data_table_view = (
                parsed_data.apply(lambda x: x.map(lambda y: str(y).replace('\n', '').replace('\r', ' '))))
        html_table = parsed_data_table_view.to_html(index=False, border=1, classes='data-table')
        return templates.TemplateResponse("table_view.html", {"request": request, "html_table": html_table})
    else:
        return HTMLResponse(content="<h1>No data available</h1>", status_code=404)

@app.get("/download")
async def download_file(filetype: str = "xlsx"):
    """
    Завантаження файлів у різних форматах (xlsx, csv, xml).
    """
    if parsed_data is None:
        return HTMLResponse(content="<h1>No data available</h1>", status_code=404)
    parsed_data_save = parsed_data
    if config.get('cleaned_data_save', False):
        parsed_data_save = (
            parsed_data.apply(lambda x: x.map(lambda y: str(y).replace('\n', '').replace('\r', ' '))))
    files_response = await convert_data_to_files(parsed_data_save, filetype)

    if isinstance(files_response, str):  # файл архіву
        return FileResponse(
            path=files_response,
            media_type='application/zip',
            filename=os.path.basename(files_response)
        )
    elif isinstance(files_response, tuple) and len(files_response) == 2:
        file_path, media_type = files_response
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=os.path.basename(file_path)
        )
    else:
        return HTMLResponse(content="<h1>Unsupported file type</h1>", status_code=400)

@app.post("/search", response_class=JSONResponse)
async def search_google(request: Request):
    """
    Пошук в Google за запитом.

    Args:
        request (Request): HTTP запит з параметром query.

    Returns:
        JSONResponse: JSON відповідь з результатами пошуку.
    """
    data = await request.form()
    query = data.get('query', '')
    num_results = data.get('num_results', 10)  # Значення за замовчуванням

    if not query:
        return JSONResponse(content={"error": "Query parameter 'query' is required"}, status_code=400)

    try:
        results = get_google_search_results(query, num_results=int(num_results))
        return JSONResponse(content={"results": results})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
