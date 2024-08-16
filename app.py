"""
# Документація для FastAPI проекту

Цей файл реалізує веб-застосунок на FastAPI з можливостями парсингу URL, відображення таблиць і завантаження файлів.

## Імпортовані бібліотеки

- `asyncio`, `os`, `random`, `logging`: стандартні бібліотеки Python.
- `FastAPI`, `Request`, `HTMLResponse`, `FileResponse`: FastAPI компоненти для обробки запитів і відповідей.
- `Jinja2Templates`: для рендерингу HTML шаблонів.
- `StaticFiles`: для роботи зі статичними файлами.
- `pandas`: для обробки даних.

## Налаштування

- **Статичні файли**: Директорії `templates` для шаблонів HTML та `static` для статичних файлів.
- **Логування**: Логи зберігаються у файлі `parser.log`.
- **Конфігурація**: Завантажується з `config.yaml`.

## Роутери

- **Головна сторінка (`/`)**: Відображає `index.html`.
- **Парсинг URL (`/parse`)**: Приймає одиночний URL або список URL для парсингу.
- **Відображення таблиці (`/table`)**: Показує таблицю з парсингованими даними.
- **Завантаження файлів (`/download`)**: Завантажує файли у форматах `xlsx`, `csv`, або `xml`.

## Запуск

Запустіть застосунок з `uvicorn`:

```bash
uvicorn your_script_name:app --host 127.0.0.1 --port 8000
"""
import asyncio
import os
import random
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
import pandas as pd

from parser import extract_content
from data_processing import convert_data_to_files
from utils import load_config

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
    parsed_data = None  # Сброс данных

    form = await request.form()
    url = form.get('url')
    urls = form.get('urls')
    code_v = form.get('code_v', '0')  # Значення за замовчуванням
    parser_type = form.get('parser_type', 'https')  # Значення за замовчуванням

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

    id_generator = yield_ID()
    if url:
        # Окремий URL
        data = await extract_content(url, ignore_list, code_v=code_v, parser_type=parser_type)
        if data:
            data['ID'] = next(id_generator)
            parsed_data = pd.DataFrame([data])

    elif urls:
        # Список URL
        urls = urls.splitlines()
        tasks = [extract_content(url.strip(), ignore_list, code_v=code_v, parser_type=parser_type) for url in urls if url.strip()]
        results = await asyncio.gather(*tasks)

        all_data = []
        for data in results:
            if data:
                data['ID'] = next(id_generator)
                all_data.append(data)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
