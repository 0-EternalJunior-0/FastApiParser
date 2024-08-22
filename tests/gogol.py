from googlesearch import search

def get_google_search_results(query, num_results=100):
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

if __name__ == "__main__":
    query = "наукові статті про котиків"
    urls = get_google_search_results(query)
    for i, url in enumerate(urls, start=1):
        print(f"{i}: {url}")
