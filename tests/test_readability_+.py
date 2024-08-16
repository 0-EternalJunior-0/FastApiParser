import requests
from readability import Document
from bs4 import BeautifulSoup

# Завантажуємо сторінку
response = requests.get('https://blog.comfy.ua/kak-vyvesti-pyatno-s-odezhdy-10-sovetov_a0-418/')
doc = Document(response.text)
article_html = doc.summary()  # Очищена розмітка тексту

# Використовуємо BeautifulSoup для парсингу HTML
soup = BeautifulSoup(article_html, 'html.parser')

# Завантажуємо оригінальний HTML для пошуку зображень
original_soup = BeautifulSoup(response.text, 'html.parser')

# Додаємо зображення до основного контенту
for img in original_soup.find_all('img'):
    # Перевіряємо, чи зображення знаходиться всередині основного контенту
    if img.parent in original_soup.find_all(['p', 'div', 'article']):
        # Вставляємо зображення в кінцевий контент
        soup.append(img)

# Конвертуємо модифікований контент назад у HTML
final_html = str(soup)

# Виводимо результат
print(final_html)
