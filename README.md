# Registry Reader

Программное обеспечение для анализа реестра Windows.

## Возможности

- Чтение live-реестра Windows
- Чтение offline-кустов (SYSTEM, SOFTWARE, SAM, SECURITY, NTUSER.DAT)
- GUI-интерфейс (PyQt6)
- Логирование ошибок
- Расширяемая архитектура через RegistryInterface

## Установка
```markdown
Выполните команды последовательно:

```cmd
:: Шаг 1: Создание виртуального окружения
python -m venv venv

:: Шаг 2: Активация (Windows cmd)
venv\Scripts\activate

:: Шаг 3: Установка зависимостей
pip install -r requirements.txt

## Запуск
python src/main.py
