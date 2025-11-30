import json
import logging

from src.utils import (
    get_card_spending_summary,
    get_convert_dates,
    get_currency,
    get_data_period_from_file,
    get_greeting,
    get_stock_prices,
    get_top_transactions,
)

logger = logging.getLogger(__name__)

EXCEL_PATH = "data/operations.xlsx"
JSON_PATH = "data/user_settings.json"


def views_info(date_time: str) -> str:
    """
    Главная функция, принимающая на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ
    """
    try:
        logger.info(f"Формирование главной страницы для даты: {date_time}")

        # Выборка данных из Excel-файла за определенный период
        dates_period = get_convert_dates(date_time)
        filtered_df = get_data_period_from_file(EXCEL_PATH, dates_period)

        # 1. Функция "Приветствие"
        greeting = get_greeting(date_time)

        # 2. Функция "По каждой карте"
        cards = get_card_spending_summary(filtered_df)

        # 3. Функция "Топ-5 транзакций по сумме платежа"
        top_transactions = get_top_transactions(filtered_df)

        # 4. Функция "Курс валют"
        currency_rates = get_currency(JSON_PATH)
        #
        # 5. Функция "Стоимость акций из S&P500"
        stock_prices = get_stock_prices(JSON_PATH)

        # формирование json-ответа
        response = {
            "greeting": greeting,
            "cards": cards,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

        logger.info("Главная страница успешно сформирована")
        return json.dumps(response, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка во views_info для даты {date_time}: {e}")
        return json.dumps({"error": "error"}, ensure_ascii=False, indent=4)
