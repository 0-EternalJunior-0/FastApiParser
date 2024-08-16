import re
from typing import List

import requests
from bs4 import BeautifulSoup
from readability import Document


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
        html = match.group(1) + after_h1_content

    return html


def parse_readability(html: BeautifulSoup, ignore_list: List[str]) -> str:
    """
    Парсить HTML-код за допомогою readability для отримання очищеного тексту та додає зображення.

    :param html: HTML-код статті як об'єкт BeautifulSoup.
    :param ignore_list: Список стоп слів, якщо є таке слово, то далі нічого не зберігаємо.
    :return: HTML-код з очищеним текстом та зображеннями.
    """
    # Перетворюємо BeautifulSoup об'єкт в рядок
    html_text = str(html)

    # Використовуємо readability для отримання очищеного HTML
    doc = Document(html_text)
    article_html = doc.summary()  # Очищена розмітка тексту

    # Використовуємо регулярні вирази для парсингу очищеного HTML
    tags_pattern = re.compile(r'<[^>]+>.*?<\/[^>]+>', re.DOTALL)
    tags = tags_pattern.findall(article_html)

    # Знаходимо всі зображення в оригінальному HTML
    original_soup = BeautifulSoup(html_text, 'html.parser')
    images = original_soup.find_all('img')

    # Перетворюємо зображення на рядки
    images_str = ''.join([str(img) for img in images])

    # Формуємо очищений контент
    content = []
    skip = False

    for tag in tags:
        # Очищаємо текст від тегів
        tag_text = re.sub(r'<[^>]+>', '', tag).strip()
        # Перевіряємо наявність стоп-слів
        if any(word in tag_text.lower() for word in ignore_list):
            skip = True
        if not skip:
            content.append(tag)
        # Виходимо з циклу, якщо потрібно пропустити все, що йде далі
        if skip:
            break

    # Додаємо зображення в кінець очищеного контенту
    content.append(images_str)

    # Форматування фінального HTML
    final_html = ''.join(content)
    return final_html

# Приклад використання
if __name__ == "__main__":
    import requests

    response = requests.get('https://hmarka.ua/ru/articles/ostorozhnost-ili-fobiya/')
    html_content = BeautifulSoup(response.text, 'lxml')

    ignore_list = ['ользуется антибактер']
    processed_html = parse_readability(html_content, ignore_list)

    print(processed_html)
