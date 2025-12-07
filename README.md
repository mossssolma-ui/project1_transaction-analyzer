# 🏦 Анализ Банковских Транзакций

Проект предназначен для анализа банковских операций, генерации отчетов и предоставления данных для веб-интерфейса. Реализованы функции для анализа кешбэка, отслеживания трат по категориям и формирования данных для главной страницы финансового приложения.

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?logo=github)](https://github.com/mossssolma-ui/project1_transaction-analyzer)

---

## 📋 Функциональные возможности

### 🌐 Веб-страницы
- **Главная страница** — отображает персонализированную информацию на основе входящей даты:
  - Приветствие по времени суток
  - Сводка по банковским картам (расходы и кешбэк)
  - Топ-5 транзакций за период
  - Курсы валют (USD, EUR и др.)
  - Цены на акции из S&P500 (AAPL, AMZN, GOOGL и др.)

### ⚙️ Сервисы
- **Анализ выгодных категорий кешбэка** — определяет категории с максимальным кешбэком за указанный месяц и год
- Поддержка пользовательских настроек через `data/user_settings.json`

### 📊 Отчеты
- **Траты по категории** — анализ расходов по выбранной категории за последние 90 дней
- Автоматическое сохранение отчетов в формате JSON с помощью декоратора

---

## 🏗️ Структура проекта
```
.
├── src/
│ ├── init.py
│ ├── utils.py # Вспомогательные функции обработки данных
│ ├── views.py # Генерация JSON для веб-страниц
│ ├── services.py # Анализ кешбэка и бизнес-логика
│ └── reports.py # Отчеты и декоратор для сохранения
├── data/
│ ├── operations.xlsx # Файл с банковскими транзакциями
│ └── user_settings.json # Настройки пользователя (валюты и акции)
├── tests/
│ ├── init.py
│ ├── test_utils.py
│ ├── test_views.py
│ ├── test_reports.py
│ └── test_services.py
├── main.py # Точка входа приложения
├── .env # Переменные окружения (API ключи)
├── .env_template # Шаблон файла .env
├── pyproject.toml # Зависимости проекта
├── logs/ # Каталог для логов и отчетов
└── README.md
```

---

## 🚀 Быстрый старт

### Требования
- Python 3.10+
- Poetry (для управления зависимостями)

### Установка
1. Клонируйте репозиторий:
   ```bash
   git clone git@github.com:mossssolma-ui/project1_transaction-analyzer.git
   cd project1_transaction-analyzer

2. Установите зависимости:
    ```bash
       poetry install
3. Заполните .env файл вашими API-ключами:
    ```bash
       API_KEY_APILAYER=your_apilayer_key
       API_KEY_ALPHAVANTAGE=your_alphavantage_key
4. Подготовьте данные:
    ```bash
    Убедитесь, что файл data/operations.xlsx существует
    Настройте желаемые валюты и акции в data/user_settings.json
5. Запуск
    ```bash
    poetry run python main.py
## 🧪 Тестирование
Проект полностью покрыт unit-тестами с использованием pytest:
```
Name                     Stmts   Miss  Cover
--------------------------------------------
src\__init__.py              0      0   100%
src\reports.py              59     10    83%
src\services.py             26      0   100%
src\utils.py               183      0   100%
src\views.py                22      0   100%
tests\__init__.py            0      0   100%
tests\test_reports.py       35      0   100%
tests\test_services.py      82      0   100%
tests\test_utils.py        286      0   100%
tests\test_views.py         89      0   100%
--------------------------------------------
TOTAL                      782     10    99%
```

```bash
# Запуск всех тестов
poetry run pytest
# Запуск с отчетом о покрытии
poetry run pytest --cov=src --cov-report=html
```
## 🔧 Используемые технологии

+ + Python 3.12 — основной язык программирования
+ + pandas — обработка и анализ табличных данных
+ + requests — взаимодействие с внешними API
+ + pytest — модульное тестирование
+ + logging — логирование операций приложения
+ + python-dotenv — управление переменными окружения
+ + Poetry — управление зависимостями и виртуальным окружением

## 🌍 Внешние API
Для получения актуальных данных проект использует:

+ + APILayer Fixer API — курсы валют
+ + Alpha Vantage — цены на акции
`Примечание: Для работы с API необходимо зарегистрироваться на соответствующих платформах и получить бесплатные API-ключи.`

## 📄 Примеры использования
Главная страница
`python`
```bash
    from src.views import views_info
    
    json_response = views_info("2021-05-01 12:00:00")
    print(json_response)
```

Анализ кешбэка
`python`
```bash
    from src.services import analyze_cashback_by_category
    import pandas as pd

    df = pd.read_excel("data/operations.xlsx")
    result = analyze_cashback_by_category(df, year=2021, month=5)
```

Отчет по категории
`python`
```bash
    from src.reports import spending_by_category
    import pandas as pd
    
    df = pd.read_excel("data/operations.xlsx")
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    report = spending_by_category(df, "Супермаркеты", "2021-05-31")
```

## 📝 Лицензия
```
Этот проект создан в образовательных целях для курсовой работы и не предназначен для коммерческого использования.
```
