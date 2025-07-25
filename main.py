import os
import glob
import uvicorn
from app import app
from utils import load_config

config = load_config('config.yaml')

def static_clir():
    """Перевіряє наявність папки статтік в цій директорії і видаляє з неї файли, які застарілі, залишаючи 50 найновіших."""
    static_dir = 'static'
    if not os.path.exists(static_dir):
        print(f"Директорія '{static_dir}' не існує.")
        return

    # Отримуємо список всіх файлів у директорії та їх дату зміни
    files = glob.glob(os.path.join(static_dir, '*'))
    files.sort(key=os.path.getmtime, reverse=True)  # Сортуємо файли за датою зміни

    # Залишаємо 50 найновіших файлів
    files_to_remove = files[10:]
    for file in files_to_remove:
        try:
            os.remove(file)
            print(f"Видалено старий файл: {file}")
        except Exception as e:
            print(f"Не вдалося видалити файл {file}: {e}")

def main():
    try:
        static_clir()
        uvicorn.run(app, host=config.get('host', '127.0.0.1'), port=config.get('port', 8000))
        print('Запуск сервера... Відкрийте локальний хост за адресою http://127.0.0.1:8000/ у браузері.')
    except OSError as e:
        print(f"Помилка при запуску сервера: {e}")
    except Exception as e:
        print(f"Сталася помилка: {e}")
    input("Натисніть Enter для завершення...")

if __name__ == "__main__":
    main()
