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

import yaml
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import os

from bs4 import BeautifulSoup


def load_config(config_file: str):
    """Завантажує конфігурацію з YAML файлу."""
    if not os.path.isfile(config_file):
        raise FileNotFoundError(f"Файл конфігурації {config_file} не знайдено.")
    with open(config_file, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

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
