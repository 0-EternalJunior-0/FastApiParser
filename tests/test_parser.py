import requests
from bs4 import BeautifulSoup
import re

def clean_html_content(html_content):
    """
    Видаляє всі скрипти, стилі та інші непотрібні елементи з HTML-коду, залишаючи лише текст.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Видалити скрипти та стилі
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()

    # Видалити залишки HTML тегів, такі як коментарі, і залишити лише текст
    text = soup.get_text(separator='\n', strip=True)

    # Повертає очищений текст з форматуванням
    return text

def fetch_and_clean_url(url):
    """
    Завантажує HTML з URL, очищує його і повертає обгорнутий текст в нову HTML-структуру.
    """
    try:
        # Отримати HTML контент
        response = requests.get(url)
        response.raise_for_status()  # Перевірити на помилки

        html_content = response.text

        # Очистити HTML контент
        clean_text = clean_html_content(html_content)

        # Створити нову HTML-структуру
        new_html = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Cleaned Text Content</title>
        </head>
        <body>
            <pre>{clean_text}</pre>
        </body>
        </html>"""

        return new_html

    except requests.RequestException as e:
        return f"Error: {str(e)}"

# Приклад використання
url = 'https://hmarka.ua/ru/articles/ostorozhnost-ili-fobiya/'  # Замініть на ваш URL
clean_html_result = fetch_and_clean_url(url)
print(clean_html_result)
