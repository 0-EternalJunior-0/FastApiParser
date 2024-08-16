from newspaper import Article
import requests
from bs4 import BeautifulSoup

# URL статті
url = 'https://blog.comfy.ua/kak-vyvesti-pyatno-s-odezhdy-10-sovetov_a0-418/'

# Завантаження та парсинг статті за допомогою newspaper3k
article = Article(url)
article.download()
article.parse()

# Отримання заголовка і тексту
title = article.title
text = article.text

# Перевірка, чи текст статті був отриманий
if not text:
    print("Text not found using newspaper3k. Trying with BeautifulSoup...")
    # Якщо текст не знайдено, спробуємо отримати його за допомогою BeautifulSoup
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # Знайдемо основний текст статті
    article_content = soup.find('article') or soup.find('div', class_='content') or soup.find('div', class_='post')
    if article_content:
        paragraphs = article_content.find_all('p')
        text = '\n'.join(p.get_text() for p in paragraphs)
    else:
        text = "Text not found in HTML."

# Завантаження HTML-коду статті для отримання зображень
response = requests.get(url)
html = response.text
soup = BeautifulSoup(html, 'html.parser')

# Отримання зображень
images = [img['src'] for img in soup.find_all('img') if 'src' in img.attrs]

# Форматування фінального HTML
final_html = f"<h1>{title}</h1><div>{text}</div>"

# Додавання зображень до фінального HTML
for img_url in images:
    final_html += f'<img src="{img_url}" alt="Image">'

# Виводимо результат
print(final_html)
