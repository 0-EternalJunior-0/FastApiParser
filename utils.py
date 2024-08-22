"""
Цей модуль містить утиліти для роботи з конфігураційними файлами, HTTP статусами,
перетворенням HTML в XML та створенням ZIP архівів.

Функції:
1. `load_config(config_file)`: Завантажує конфігурацію з YAML файлу.
   - Параметри:
     - `config_file` (str): Шлях до YAML файлу конфігурації.
   - Повертає:
     - dict: Словник з конфігураційними налаштуваннями.
   - Викидає:
     - FileNotFoundError: Якщо файл не знайдено.

2. `get_status_description(status_code)`: Повертає опис статус-коду HTTP.
   - Параметри:
     - `status_code` (int): Код HTTP статусу.
   - Повертає:
     - str: Опис статусу у форматі "Код відповіді: <код> - <опис>".

3. `html_to_xml(html_content)`: Перетворює HTML в XML формат.
   - Параметри:
     - `html_content` (BeautifulSoup): HTML контент у вигляді BeautifulSoup об'єкта.
   - Повертає:
     - str: XML представлення HTML контенту.

4. `create_zip_archive(files, zip_file_path)`: Створює ZIP архів з файлів.
   - Параметри:
     - `files` (list): Список шляхів до файлів, які потрібно включити в архів.
     - `zip_file_path` (str): Шлях до створюваного ZIP архіву.
   - Викидає:
     - FileNotFoundError: Якщо якийсь з файлів не знайдено.

"""
import logging

import yaml
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import os
from googlesearch import search

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, filename='parser.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_config(config_file: str):
    """Завантажує конфігурацію з YAML файлу."""
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"Файл конфігурації {config_file} не знайдено.")
    with open(config_file, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)



def blacklist(blacklist_file: str):
    """blacklist - список сторінок які потрібно блокувати txt"""
    if not os.path.isfile(blacklist_file):
        raise FileNotFoundError(f"Файл blacklist :  {blacklist_file} не знайдено.")
    with open(blacklist_file, 'r', encoding='utf-8') as file:
        return file.read().split('\n')

def add_unreachable_site(blacklist_file: str, site_url: str):
    print(1)
    print(blacklist_file)
    """
    Додає недоступний сайт у файл.

    blacklist_file - назва текстового файлу, в який записуються недоступні сайти.
    site_url - URL сайту, який потрібно додати до списку недоступних.
    """
    # Отримуємо шлях до поточної директорії
    current_directory = os.getcwd()

    # Створюємо повний шлях до файлу
    blacklist_file_path = os.path.join(current_directory, blacklist_file)
    print(blacklist_file_path)
    # Перевіряємо, чи файл існує і створюємо його, якщо необхідно
    file_exists = os.path.isfile(blacklist_file_path)

    if not file_exists:
        with open(blacklist_file_path, 'w', encoding='utf-8') as file:
            pass  # Просто створюємо порожній файл

    # Читаємо існуючі сайти, якщо файл існує
    existing_sites = set()
    if file_exists:
        with open(blacklist_file_path, 'r', encoding='utf-8') as file:
            existing_sites = set(file.read().splitlines())

    # Додаємо сайт у файл, якщо його ще немає
    if site_url not in existing_sites:
        with open(blacklist_file_path, 'a', encoding='utf-8') as file:
            file.write(site_url + '\n')
            logging.info(f"Сайт {site_url} додано до тимчасового списку недоступних.")
    else:
        logging.info(f"Сайт {site_url} вже є у тимчасовому списку недоступних.")




def get_status_description(status_code: int)->str:
    """Повертає опис статус-коду HTTP."""
    from http import HTTPStatus
    try:
        description = HTTPStatus(status_code).description
        return f"Код відповіді: {status_code} - {description}"
    except ValueError:
        return f"Невідомий код відповіді: {status_code}"


def html_to_xml(html_content: BeautifulSoup):
    """
    Перетворює HTML-контент у формат XML.
    Якщо виникає помилка або результат порожній, зберігає HTML-контент як XML.

    :param html_content: Об'єкт BeautifulSoup, що містить HTML-контент.
    :return: XML-контент у вигляді рядка.
    """
    import xml.etree.ElementTree as ET

    try:
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

        parse_element(html_content, root)
        xml_result = ET.tostring(root, encoding='unicode')

        if not xml_result.strip():
            raise ValueError("Результат перетворення пустий.")

    except Exception as e:
        # Якщо виникає помилка, зберігаємо HTML-контент як XML
        xml_result = f"<root><![CDATA[{html_content}]]></root>"
    return xml_result

def create_zip_archive(files: list, zip_file_path: str):
    """Створює ZIP архів з файлів."""
    print('Створює ZIP архів з файлів')
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in files:
            if os.path.isfile(file):
                zipf.write(file, os.path.basename(file))
            else:
                raise FileNotFoundError(f"Файл {file} не знайдено.")

def get_google_search_results(query: str, num_results: int = 100):
    """
    Отримує перші `num_results` посилань з Google за запитом `query`.

    :param query: Пошуковий запит
    :param num_results: Кількість результатів для отримання
    :return: Список URL-адрес
    """
    urls = []
    try:
        # Змінюємо параметри пошуку для отримання результатів
        for url in search(query, num_results=num_results, lang="en"):
            urls.append(url)
            if len(urls) >= num_results:
                break
    except Exception as e:
        print(f"Виникла помилка: {e}")
    return urls