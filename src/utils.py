import json
import logging
import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/log.log", mode="w", encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY_APILAYER = os.getenv("API_KEY_APILAYER")
BASE_URL_APILAYER = os.getenv("BASE_URL_APILAYER")

API_KEY_ALPHAVANTAGE = os.getenv("API_KEY_ALPHAVANTAGE")
BASE_URL_ALPHAVANTAGE = os.getenv("BASE_URL_ALPHAVANTAGE")


# Выборка данных из Excel-файла за определенный период
def get_convert_dates(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """
    Функция принимает строку с датой и временем.
    Возвращает две даты в формате 'dd.mm.yyyy HH:MM:SS':
      - 1-е число текущего месяца в 00:00:00
      - Текущий день в 23:59:59
    Пример: "2021-05-10 12:00:00" → ["01.05.2021 00:00:00", "10.05.2021 23:59:59"]
    """
    try:
        dt = datetime.strptime(date_time, date_format)
        first_day = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_of_day = dt.replace(hour=23, minute=59, second=59, microsecond=0)

        result = [
            first_day.strftime("%d.%m.%Y %H:%M:%S"),
            end_of_day.strftime("%d.%m.%Y %H:%M:%S"),
        ]
        logger.info(f"Конвертация прошла успешно {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка конвертации {date_time}: {e}")
        return ["01.01.2000 00:00:00", "01.01.2000 23:59:59"]


def get_data_period_from_file(filepath: str, period_dates: list[str]) -> pd.DataFrame:
    """
    Функция принимает путь к xlsx-файлу и список из двух строковых дат в формате 'dd.mm.yyyy HH:MM:SS'.
    Возвращает DataFrame с транзакциями в указанном диапазоне (включительно).
    """
    try:
        df = pd.read_excel(filepath)
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

        start_date = datetime.strptime(period_dates[0], "%d.%m.%Y %H:%M:%S")
        end_date = datetime.strptime(period_dates[1], "%d.%m.%Y %H:%M:%S")

        filtered_df = df.loc[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
        logger.info(f"Загружено {len(filtered_df)} записей за период {period_dates}")
        return filtered_df
    except Exception as e:
        logger.error(f"Ошибка загрузки из {filepath}: {e}")
        return pd.DataFrame()


# 1. Функция "Приветствие"
def get_greeting(date_time: str) -> str:
    """Возвращает приветствие по времени суток из полученной строки."""
    try:
        date_dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
        time_now = date_dt.hour

        if 6 <= time_now < 12:
            message = "Доброе утро"
        elif 12 <= time_now < 18:
            message = "Добрый день"
        elif 18 <= time_now < 23:
            message = "Добрый вечер"
        else:
            message = "Доброй ночи"

        logger.info(f"Генерация приветствия {message} для времени {date_time}")
        return message
    except Exception as e:
        logger.error(f"Ошибка генерации приветствия для {date_time}: {e}")
        return "Добрый день"


# 2. Функция "По каждой карте"
def get_card_spending_summary(transactions: pd.DataFrame) -> list[dict]:
    """
    Функция принимает DataFrame и возвращает сводку по картам:
    последние 4 цифры, общие расходы, кешбэк.
    Учитываются только отрицательные 'Сумма операции' (расходы).
    """
    try:
        if transactions.empty:
            logger.error("Пустой DataFrame")
            return []

        df = transactions[transactions["Сумма операции"] < 0].copy()

        if df.empty:
            logger.info("Нет данных для анализа")
            return []

        df["last_digits"] = df["Номер карты"].astype("str").str[-4:]
        df["total_spent"] = df["Сумма операции"].abs()

        group_df = df.groupby("last_digits")["total_spent"].sum().reset_index()
        group_df["cashback"] = (group_df["total_spent"] / 100).round(2)
        group_df["total_spent"] = group_df["total_spent"].round(2)

        result = group_df[["last_digits", "total_spent", "cashback"]].to_dict(orient="records")
        logger.info(f"Генерация по {len(result)} картам")
        return result
    except Exception as e:
        logger.error(f"Ошибка генерации в get_card_spending_summary: {e}")
        return []


# 3. Функция "Топ-5 транзакций по сумме платежа"
def get_top_transactions(transactions: pd.DataFrame, get_count: int = 5) -> list[dict]:
    """
    Функция принимает DataFrame и возвращает по умолчанию
    топ 5 транзакций по сумме платежа (по модулю).
    """
    try:
        if transactions.empty:
            logger.error("Пустой DataFrame")
            return []

        df = transactions.copy()
        df["abs_amount"] = df["Сумма платежа"].abs()
        df_sorted = df.sort_values(by="abs_amount", ascending=False).head(get_count)

        result = []
        for _, row in df_sorted.iterrows():
            date = row["Дата операции"]
            if pd.isna(date):
                date_str = ""
            else:
                date_str = pd.to_datetime(date).strftime("%d.%m.%Y")

            result.append(
                {
                    "date": date_str,
                    "amount": round(row["Сумма платежа"], 2),
                    "category": row.get("Категория", ""),
                    "description": row.get("Описание", ""),
                }
            )
        logger.info(f"Найдено {len(result)} топ транзакций")
        return result
    except Exception as e:
        logger.error(f"Ошибка обработки в get_top_transactions: {e}")
        return []


# 4. Функция "Курс валют"
def load_currency(filepath: str) -> list[str]:
    """
    Загружает список валют из JSON-файла.
    Возвращает список кодов валют.
    """
    try:
        with open(filepath, encoding="utf-8") as file_json:
            data = json.load(file_json)
            currencies = data.get("user_currencies", [])
            logger.info(f"Загружены валюты: {currencies}")
            return currencies  # type: ignore
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        logger.error(f"Ошибка загрузки валют: {e}")
        return []


def fetch_currency_rates(currencies: list[str]) -> list[dict]:
    """
    Получает курсы валют через API.
    Возвращает список словарей с валютами и их курсами.
    """
    if not currencies:
        logger.error("Пустой список валют в fetch_currency_rates")
        return []

    currency_rates = []
    logger.info(f"Получение курсов для {len(currencies)} валют")

    for currency in currencies:
        rate = currency_rate_api(currency)
        currency_rates.append({"currency": currency, "rate": rate})

    logger.info(f"Получены курсы для {len(currency_rates)} валют")
    return currency_rates


def currency_rate_api(currency: str) -> float:
    """
    Получает курс одной валюты через API.
    Возвращает курс или 0.0 в случае ошибки.
    """
    params = {"amount": 1, "from": currency, "to": "RUB"}
    headers = {"apikey": API_KEY_APILAYER}

    try:
        logger.info(f"Запрос курса валюты {currency}")
        response = requests.get(BASE_URL_APILAYER, headers=headers, params=params, timeout=10)  # type: ignore

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Статус подключения успешен, код: {response.status_code}")
            if data.get("success"):
                rate = round(data["result"], 2)
                logger.info(f"Курс {currency}/RUB: {rate}")
                return rate  # type: ignore
            else:
                logger.error(f"Ошибка API, запрос по {currency} не выполнился")
        else:
            logger.error(f"Ошибка запроса для {currency}: {response.status_code}")

    except Exception as e:
        logger.error(f"Исключение при запросе {currency}: {e}")

    return 0.0


def get_currency(filepath: str) -> list[dict]:
    """
    Функция загружает настройки и получает курсы валют.
    """
    logger.info(f"Получение курсов валют из {filepath}")
    currencies = load_currency(filepath)
    result = fetch_currency_rates(currencies)
    logger.info(f"Завершено получение курсов валют, всего: {len(result)}")
    return result


# 5. Функция "Стоимость акций из S&P500"
def load_stock(filepath: str) -> list[str]:
    """
    Загружает список акций из JSON-файла.
    Возвращает список акций.
    """
    try:
        with open(filepath, encoding="utf-8") as file_json:
            data = json.load(file_json)
            stocks = data.get("user_stocks", [])
            logger.info(f"Загружены акции: {stocks}")
            return stocks  # type: ignore
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        logger.error(f"Ошибка загрузки акций из {filepath}: {e}")
        return []


def fetch_stock_prices(stocks: list[str]) -> list[dict]:
    """
    Получает цены акций через API.
    Возвращает список словарей с акциями и их ценами.
    """
    if not stocks:
        logger.error("Пустой список акций передан в fetch_stock_prices")
        return []

    stock_prices = []
    logger.info(f"Начало получения цен для {len(stocks)} акций")

    for stock in stocks:
        price = stock_price_api(stock)
        stock_prices.append({"stock": stock, "price": price})

    logger.info(f"Получение цен для {len(stock_prices)} акций")
    return stock_prices


def stock_price_api(stock: str) -> float:
    """
    Получает цену одной акции через API.
    Возвращает цену или 0.0 в случае ошибки.
    """
    params = {"function": "GLOBAL_QUOTE", "symbol": stock, "apikey": API_KEY_ALPHAVANTAGE}

    try:
        logger.info(f"Запрос цены акции {stock}")
        response = requests.get(BASE_URL_ALPHAVANTAGE, params=params, timeout=10)  # type: ignore

        if response.status_code == 200:
            data = response.json()
            quote = data.get("Global Quote")
            logger.info(f"Статус подключения успешен, код: {response.status_code}")

            if quote and "05. price" in quote:
                price = float(quote["05. price"])
                logger.info(f"Цена акции {stock}: {price}")
                return round(price, 2)
            else:
                logger.error(f"Нет данных для акции {stock}: {data}")
        else:
            logger.error(f"Ошибка запроса для акции {stock}: {response.status_code}")

    except Exception as e:
        logger.error(f"Исключение при запросе акции {stock}: {e}")

    return 0.0


def get_stock_prices(filepath: str) -> list[dict]:
    """
    Функция загружает акции и получает цены акций.
    """
    logger.info(f"Начало получения цен на акции из {filepath}")
    stocks = load_stock(filepath)
    result = fetch_stock_prices(stocks)
    logger.info(f"Завершено получение цен на акции, всего: {len(result)}")
    return result
