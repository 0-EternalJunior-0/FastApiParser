"""
Цей модуль відповідає за створення виконуваного файлу з Python скрипту за допомогою PyInstaller.

## Імпортовані бібліотеки

- `subprocess`: Для виконання команд оболонки в Python.

## Команди для створення виконуваного файлу

1. `pip install pyinstaller`
   - **Опис**: Встановлює PyInstaller, якщо він ще не встановлений. PyInstaller необхідний для перетворення Python скриптів у самостійні виконувані файли.

2. `pyinstaller --onefile myapp.spec`
   - **Опис**: Створює виконуваний файл з Python скрипту на основі конфігурації, зазначеної у файлі `myapp.spec`.
   - `--onefile`: Вказує PyInstaller створювати один єдиний виконуваний файл, що спрощує розгортання і розподіл.

**Приклад використання**:
1. Запустіть модуль Python для встановлення PyInstaller.
2. Після успішного встановлення PyInstaller, створіть виконуваний файл з Python скрипту за допомогою конфігураційного файлу `myapp.spec`.

Зверніть увагу, що перед виконанням цих команд, переконайтесь, що у вас є доступ до Python середовища та налаштованого файлу конфігурації `myapp.spec`.
"""


import subprocess

# Команда для установки PyInstaller
command_install_building = 'pip install pyinstaller'

# Команда для створення виконуваного файлу
command = 'pyinstaller myapp.spec'


# Виконання команди для установки PyInstaller
subprocess.run(command_install_building, shell=True, check=True)

# Виконання команди для створення виконуваного файлу
subprocess.run(command, shell=True, check=True)
