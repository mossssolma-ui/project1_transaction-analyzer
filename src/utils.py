import json
import os
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY_APILAYER = os.getenv("API_KEY_APILAYER")
BASE_URL_APILAYER = os.getenv("BASE_URL_APILAYER")

API_KEY_ALPHAVANTAGE = os.getenv("API_KEY_ALPHAVANTAGE")
BASE_URL_ALPHAVANTAGE = os.getenv("BASE_URL_ALPHAVANTAGE")


# Выборка данных из Excel-файла за определенный период
def get_convert_dates(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """
    Функция принимает строку с датой и временем
    Возращает 2 конвертированные даты: 1 день текущего месяца, текущий день месяца,
    в формате: день.месяц.год.
    """
    dt = datetime.strptime(date_time, date_format)
    first_day = dt.replace(day=1)

    return [
        first_day.strftime("%d.%m.%Y %H:%M:%S"),
        dt.strftime("%d.%m.%Y %H:%M:%S"),
    ]


def get_data_period_from_file(filepath: str, period_dates: list[str]) -> pd.DataFrame:
    """
    Функция принимает путь к xlsx-файлу и список дат.
    Возвращает DataFrame, которая соответсвуют списку дат.
    """
    df = pd.read_excel(filepath)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

    start_date = datetime.strptime(period_dates[0], "%d.%m.%Y %H:%M:%S")
    end = datetime.strptime(period_dates[1], "%d.%m.%Y %H:%M:%S")
    end_date = end.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    filtered_df = df.loc[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
    return filtered_df


# 1. Функция "Приветствие"
def get_greeting(date_time: str) -> str:
    """Возвращает приветствие по времени суток из полученной строки"""
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

    return message


# 2. Функция "По каждой карте"
def get_card_spending_summary(transactions: pd.DataFrame) -> list[dict]:
    """
    Функция принимает DataFrame и возвращает сводку по картам:
    последние 4 цифры, общие расходы, кешбэк.
    Учитываются только отрицательные 'Сумма операции' (расходы).
    """
    if transactions.empty:
        return []

    df = transactions[transactions["Сумма операции"] < 0].copy()

    if df.empty:
        return []

    df["last_digits"] = df["Номер карты"].astype("str").str[-4:]
    df["total_spent"] = df["Сумма операции"].abs()

    group_df = df.groupby("last_digits")["total_spent"].sum().reset_index()
    group_df["cashback"] = (group_df["total_spent"] / 100).round(2)
    group_df["total_spent"] = group_df["total_spent"].round(2)

    result = group_df[["last_digits", "total_spent", "cashback"]].to_dict(orient="records")
    return result


# 3. Функция "Топ-5 транзакций по сумме платежа"
def get_top_transactions(transactions: pd.DataFrame, get_count: int = 5) -> list[dict]:
    """
    Функция принимает DataFrame и возвращает по умолчанию
    топ 5 транзакций по сумме платежа
    """
    if transactions.empty:
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
    return result


# 4. Функция "Курс валют"
def load_currency(filepath: str) -> list[str]:
    """
    Загружает список валют из JSON-файла.
    Возвращает список кодов валют.
    """
    try:
        with open(filepath, encoding="utf-8") as file_json:
            data = json.load(file_json)
            return data.get("user_currencies", [])  # type: ignore
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        print(f"Ошибка загрузки {e}")
        return []


def fetch_currency_rates(currencies: list[str]) -> list[dict]:
    """
    Получает курсы валют через API.
    Возвращает список словарей с валютами и их курсами.
    """
    if not currencies:
        return []

    currency_rates = []

    for currency in currencies:
        rate = currency_rate_api(currency)
        currency_rates.append({"currency": currency, "rate": rate})

    return currency_rates


def currency_rate_api(currency: str) -> float:
    """
    Получает курс одной валюты через API.
    Возвращает курс или 0.0 в случае ошибки.
    """
    params = {"amount": 1, "from": currency, "to": "RUB"}
    headers = {"apikey": API_KEY_APILAYER}

    try:
        response = requests.get(BASE_URL_APILAYER, headers=headers, params=params, timeout=10)  # type: ignore

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return round(data["result"], 2)  # type: ignore
            else:
                print(f"Ошибка API, запрос по {currency} не выполнился")
        else:
            print(f"Ошибка запроса для {currency}: {response.status_code}")

    except Exception as e:
        print(f"Исключение при запросе {currency}: {e}")

    return 0.0


def get_currency(filepath: str) -> list[dict]:
    """
    Функция загружает настройки и получает курсы валют.
    """
    currencies = load_currency(filepath)
    return fetch_currency_rates(currencies)


# 5. Функция "Стоимость акций из S&P500"
def load_stock(filepath: str) -> list[str]:
    """
    Загружает список акций из JSON-файла.
    Возвращает список акций.
    """
    try:
        with open(filepath, encoding="utf-8") as file_json:
            data = json.load(file_json)
            return data.get("user_stocks", [])  # type: ignore
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        print(f"Ошибка загрузки {e}")
        return []


def fetch_stock_prices(stocks: list[str]) -> list[dict]:
    """
    Получает цены акций через API.
    Возвращает список словарей с акциями и их ценами.
    """
    if not stocks:
        return []

    stock_prices = []

    for stock in stocks:
        price = stock_price_api(stock)
        stock_prices.append({"stock": stock, "price": price})

    return stock_prices


def stock_price_api(stock: str) -> float:
    """
    Получает цену одной акции через API.
    Возвращает цену или 0.0 в случае ошибки.
    """
    params = {"function": "GLOBAL_QUOTE", "symbol": stock, "apikey": API_KEY_ALPHAVANTAGE}

    try:
        response = requests.get(BASE_URL_ALPHAVANTAGE, params=params, timeout=10)  # type: ignore

        if response.status_code == 200:
            data = response.json()
            quote = data.get("Global Quote")

            if quote and "05. price" in quote:
                price = float(quote["05. price"])
                return round(price, 2)
            else:
                print(f"Нет данных для акции {stock}: {data}")
        else:
            print(f"Ошибка запроса для акции {stock}: {response.status_code}")

    except Exception as e:
        print(f"Исключение при запросе акции {stock}: {e}")

    return 0.0


def get_stock_prices(filepath: str) -> list[dict]:
    """
    Функция загружает акции и получает цены акций.
    """
    stocks = load_stock(filepath)
    return fetch_stock_prices(stocks)
