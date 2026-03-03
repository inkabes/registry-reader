# Registry Reader

Программное обеспечение для анализа реестра Windows.

## Возможности

- Чтение live-реестра Windows
- Чтение offline-кустов (SYSTEM, SOFTWARE, SAM, SECURITY, NTUSER.DAT)
- GUI-интерфейс (PyQt6)
- Логирование ошибок
- Расширяемая архитектура через RegistryInterface

## Установка
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

## Запуск
python src/main.py
