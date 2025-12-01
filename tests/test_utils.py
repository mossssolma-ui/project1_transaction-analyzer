import logging
from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture

from src.utils import (
    currency_rate_api,
    fetch_currency_rates,
    fetch_stock_prices,
    get_card_spending_summary,
    get_convert_dates,
    get_currency,
    get_data_period_from_file,
    get_greeting,
    get_stock_prices,
    get_top_transactions,
    load_currency,
    load_stock,
    stock_price_api,
)


# Выборка данных из Excel-файла за определенный период
def test_get_convert_dates_success(caplog: LogCaptureFixture) -> None:
    """Тест успешной конвертации дат"""
    caplog.set_level(logging.INFO)
    test_date = "2021-01-10 12:00:00"

    res = get_convert_dates(test_date)
    expected = ["01.01.2021 00:00:00", "10.01.2021 23:59:59"]
    assert res == expected
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "INFO"
    assert f"Конвертация прошла успешно {expected}" in caplog.records[0].message


@patch("src.utils.datetime")
def test_get_convert_dates_exception(mock_datetime: Mock, caplog: LogCaptureFixture) -> None:
    """Тест ошибочной конвертации дат"""
    caplog.set_level(logging.ERROR)
    mock_datetime.strptime.side_effect = Exception("date invalid")

    res = get_convert_dates("invalid-date")
    expected = ["01.01.2000 00:00:00", "01.01.2000 23:59:59"]
    assert res == expected
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert "date invalid" in caplog.records[0].message


@patch("src.utils.pd.read_excel")
def test_get_data_period_from_file_success_simple(mock_read_excel: Mock, caplog: LogCaptureFixture) -> None:
    """Тест успешной загрузки данных"""
    caplog.set_level(logging.INFO)

    test_df = pd.DataFrame(
        {
            "Дата операции": ["01.05.2021 10:00:00", "10.05.2021 15:30:00"],
            "Сумма операции": [100, 200],
            "Описание": ["Покупка 1", "Покупка 2"],
        }
    )

    mock_read_excel.return_value = test_df

    result = get_data_period_from_file("test.xlsx", ["01.05.2021 00:00:00", "10.05.2021 23:59:59"])

    mock_read_excel.assert_called_once_with("test.xlsx")
    assert len(result) == 2
    assert "Загружено 2 записей за период" in caplog.text


@patch("src.utils.pd.read_excel")
def test_get_data_period_from_file_exception(mock_read_excel: Mock, caplog: LogCaptureFixture) -> None:
    """Тест ошибки загрузки файла"""
    caplog.set_level(logging.ERROR)
    mock_read_excel.side_effect = Exception("File not found")

    result = get_data_period_from_file("test_file.xlsx", ["01.05.2024 00:00:00", "15.05.2024 23:59:59"])

    assert result.empty
    assert "Ошибка загрузки из test_file.xlsx" in caplog.text


# 1. Функция "Приветствие"
@pytest.mark.parametrize(
    "date_time, expected_message",
    [
        ("2021-01-01 06:00:00", "Доброе утро"),
        ("2021-01-01 11:59:00", "Доброе утро"),
        ("2021-01-01 12:00:00", "Добрый день"),
        ("2021-01-01 17:59:00", "Добрый день"),
        ("2021-01-01 18:00:00", "Добрый вечер"),
        ("2021-01-01 22:59:00", "Добрый вечер"),
        ("2021-01-01 23:00:00", "Доброй ночи"),
        ("2021-01-01 05:59:00", "Доброй ночи"),
    ],
)
def test_get_greeting(date_time: str, expected_message: str) -> None:
    """Проверка на правильность вывода приветствия"""
    res = get_greeting(date_time)
    assert res == expected_message


def test_get_greeting_logging(caplog: LogCaptureFixture) -> None:
    """Проверка, что лог записывается при успешной генерации"""
    caplog.set_level(logging.INFO)
    test_date = "2021-01-01 12:00:00"
    expected_message = "Добрый день"

    res = get_greeting(test_date)
    assert res == expected_message

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    assert log_record.levelname == "INFO"
    expected_log = f"Генерация приветствия {expected_message} для времени {test_date}"
    assert log_record.message == expected_log


def test_get_greeting_logging_exception(caplog: LogCaptureFixture) -> None:
    """Отлавливаем лог ошибки генерации приветствия"""
    caplog.set_level(logging.ERROR)
    res = get_greeting("data")
    expected_message = "Добрый день"

    assert res == expected_message
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert "Ошибка генерации приветствия для" in caplog.records[0].message


# 2. Функция "По каждой карте"
def test_get_card_spending_summary_empty_dataframe(caplog: LogCaptureFixture) -> None:
    """Тест с пустым DataFrame"""
    caplog.set_level(logging.ERROR)
    empty_df = pd.DataFrame()
    result = get_card_spending_summary(empty_df)
    assert result == []
    assert "Пустой DataFrame" in caplog.text


def test_get_card_spending_summary_no_negative_transactions(caplog: LogCaptureFixture) -> None:
    """Тест когда DataFrame не пустой, но нет расходных операций"""
    caplog.set_level(logging.INFO)
    test_df = pd.DataFrame(
        {
            "Номер карты": ["1234567890123456", "9876543210987654"],
            "Сумма операции": [1000, 500],
            "Категория": ["Пополнение", "Бонусы"],
        }
    )

    result = get_card_spending_summary(test_df)

    assert result == []
    assert "Нет данных для анализа" in caplog.text


def test_get_card_spending_summary_success(caplog: LogCaptureFixture) -> None:
    """Тест успешной генерации сводки по картам"""
    caplog.set_level(logging.INFO)
    test_df = pd.DataFrame(
        {
            "Номер карты": ["*3456", "*1234", "*9876"],
            "Сумма операции": [-1500, -500, -1500],
            "Категория": ["Супермаркеты", "Транспорт", "Рестораны"],
        }
    )

    result = get_card_spending_summary(test_df)

    expected = [
        {"last_digits": "3456", "total_spent": 1500.0, "cashback": 15.0},
        {"last_digits": "1234", "total_spent": 500.0, "cashback": 5.0},
        {"last_digits": "9876", "total_spent": 1500.0, "cashback": 15.0},
    ]
    result_sorted = sorted(result, key=lambda x: x["last_digits"])
    expected_sorted = sorted(expected, key=lambda x: x["last_digits"])  # type: ignore

    assert result_sorted == expected_sorted
    assert "Генерация по 3 картам" in caplog.text


def test_get_card_spending_summary_exception(caplog: LogCaptureFixture) -> None:
    """Тест ошибки генерации в get_card_spending_summary"""
    caplog.set_level(logging.ERROR)
    test_df = pd.DataFrame(
        {"Номер карты": [None, None, None], "Сумма операции": ["", "текст", "123"], "Категория": [None, None, None]}
    )
    get_card_spending_summary(test_df)

    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert "Ошибка генерации в get_card_spending_summary" in caplog.records[0].message


# 3. Функция "Топ-5 транзакций по сумме платежа"
def test_get_top_transactions_empty_dataframe(caplog: LogCaptureFixture) -> None:
    """Тест с пустым DataFrame"""
    caplog.set_level(logging.ERROR)
    empty_df = pd.DataFrame()
    result = get_top_transactions(empty_df)
    assert result == []
    assert "Пустой DataFrame" in caplog.text


def test_get_top_transactions_exception_in_sort(caplog: LogCaptureFixture) -> None:
    """Тест обработки исключения при сортировке"""
    caplog.set_level(logging.ERROR)

    test_df = pd.DataFrame(
        {
            "Дата операции": ["2023-10-01", "2023-10-02"],
            "Сумма платежа": [100.50, -500.75],
            "Категория": ["Еда", "Транспорт"],
            "Описание": ["Обед", "Такси"],
        }
    )

    with patch("pandas.DataFrame.sort_values") as mock_sort:
        mock_sort.side_effect = Exception("Ошибка сортировки")

        result = get_top_transactions(test_df)

        assert result == []
        assert "Ошибка обработки в get_top_transactions" in caplog.text
        assert "Ошибка сортировки" in caplog.text


def test_get_top_transactions_success(caplog: LogCaptureFixture) -> None:
    """Тест успешного выполнения функции"""
    caplog.set_level(logging.INFO)
    test_df = pd.DataFrame(
        {
            "Дата операции": ["2023-10-01", "2023-10-02", "2023-10-03"],
            "Сумма платежа": [100.50, -500.75, 1000.00],
            "Категория": ["Еда", "Транспорт", "Зарплата"],
            "Описание": ["Обед", "Такси", "ЗП"],
        }
    )

    result = get_top_transactions(test_df, 2)

    assert len(result) == 2
    assert result[0]["amount"] == 1000.00
    assert result[1]["amount"] == -500.75
    assert result[0]["date"] == "03.10.2023"
    assert result[1]["date"] == "02.10.2023"
    assert "Найдено 2 топ транзакций" in caplog.text


def test_get_top_transactions_nan_date(caplog: LogCaptureFixture) -> None:
    """Тест обработки NaN дат в DataFrame"""
    caplog.set_level(logging.INFO)
    test_df = pd.DataFrame(
        {
            "Дата операции": [None, "2023-10-02", pd.NaT, float("nan")],
            "Сумма платежа": [100.50, -500.75, 1000.00, 200.25],
            "Категория": ["Еда", "Транспорт", "Зарплата", "Развлечения"],
            "Описание": ["Обед", "Такси", "ЗП", "Кино"],
        }
    )

    result = get_top_transactions(test_df)

    assert result[0]["amount"] == 1000.00
    assert result[0]["date"] == ""

    assert result[1]["amount"] == -500.75
    assert result[1]["date"] == "02.10.2023"

    assert result[2]["amount"] == 200.25
    assert result[2]["date"] == ""

    assert result[3]["amount"] == 100.50
    assert result[3]["date"] == ""

    assert len(result) == 4
    assert "Найдено 4 топ транзакций" in caplog.text


# 4. Функция "Курс валют"
def test_load_currency_success(caplog: LogCaptureFixture) -> None:
    """Тест успешной загрузки валют из JSON файла"""
    caplog.set_level(logging.INFO)
    mock_data = '{"user_currencies": ["USD", "EUR", "GBP"]}'

    with patch("builtins.open", mock_open(read_data=mock_data)):
        result = load_currency("test_currency.json")

    assert result == ["USD", "EUR", "GBP"]
    assert "Загружены валюты: ['USD', 'EUR', 'GBP']" in caplog.text


def test_load_currency_file_not_found(caplog: LogCaptureFixture) -> None:
    """Тест загрузки валют при отсутствии файла"""
    caplog.set_level(logging.ERROR)
    with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
        result = load_currency("nonexistent.json")

    assert result == []
    assert "File not found" in caplog.text


def test_load_currency_json_decode_error(caplog: LogCaptureFixture) -> None:
    """Тест загрузки валют при ошибке JSON"""
    caplog.set_level(logging.ERROR)
    with patch("builtins.open", mock_open(read_data="invalid json")):
        result = load_currency("invalid.json")

    assert result == []
    assert "Ошибка загрузки валют" in caplog.text


@patch("src.utils.currency_rate_api")
def test_fetch_currency_rates_success(mock_currency_api: Mock, caplog: LogCaptureFixture) -> None:
    """Тест успешного получения курсов валют"""
    caplog.set_level(logging.INFO)
    mock_currency_api.side_effect = [75.50, 85.25, 95.75]
    currencies = ["USD", "EUR", "GBP"]

    result = fetch_currency_rates(currencies)

    expected = [
        {"currency": "USD", "rate": 75.50},
        {"currency": "EUR", "rate": 85.25},
        {"currency": "GBP", "rate": 95.75},
    ]
    assert result == expected
    assert "Получение курсов для 3 валют" in caplog.text
    assert "Получены курсы для 3 валют" in caplog.text


def test_fetch_currency_rates_empty_list(caplog: LogCaptureFixture) -> None:
    """Тест получения курсов при пустом списке валют"""
    caplog.set_level(logging.ERROR)
    result = fetch_currency_rates([])

    assert result == []
    assert "Пустой список валют в fetch_currency_rates" in caplog.text


@patch("src.utils.requests.get")
def test_currency_rate_api_success(mock_get: Mock, caplog: LogCaptureFixture) -> None:
    """Тест успешного получения курса валюты через API"""
    caplog.set_level(logging.INFO)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True, "result": 75.50}
    mock_get.return_value = mock_response

    result = currency_rate_api("USD")

    assert result == 75.50
    assert "Запрос курса валюты USD" in caplog.text
    assert "Курс USD/RUB: 75.5" in caplog.text


@patch("src.utils.requests.get")
def test_currency_rate_api_success_false(mock_get: Mock, caplog: LogCaptureFixture) -> None:
    """Тест когда API возвращает success: false"""
    caplog.set_level(logging.ERROR)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": False}
    mock_get.return_value = mock_response

    result = currency_rate_api("INVALID")

    assert result == 0.0
    assert "Ошибка API, запрос по INVALID не выполнился" in caplog.text


@patch("src.utils.requests.get")
def test_currency_rate_api_failure(mock_get: Mock, caplog: LogCaptureFixture) -> None:
    """Тест неудачного получения курса валюты"""
    caplog.set_level(logging.ERROR)
    mock_response = Mock()
    mock_response.status_code = 400
    mock_get.return_value = mock_response

    result = currency_rate_api("USD")

    assert result == 0.0
    assert "Ошибка запроса для USD: 400" in caplog.text


@patch("src.utils.requests.get")
def test_currency_rate_api_exception(mock_get: Mock, caplog: LogCaptureFixture) -> None:
    """Тест исключения при запросе курса валюты"""
    caplog.set_level(logging.ERROR)
    mock_get.side_effect = Exception("Connection error")

    result = currency_rate_api("USD")

    assert result == 0.0
    assert "Исключение при запросе USD: Connection error" in caplog.text


@patch("src.utils.fetch_currency_rates")
@patch("src.utils.load_currency")
def test_get_currency_success(mock_load: Mock, mock_fetch: Mock, caplog: LogCaptureFixture) -> None:
    """Тест успешного получения курсов валют"""
    caplog.set_level(logging.INFO)
    mock_load.return_value = ["USD", "EUR"]
    mock_fetch.return_value = [{"currency": "USD", "rate": 75.50}, {"currency": "EUR", "rate": 85.25}]

    result = get_currency("currencies.json")

    assert len(result) == 2
    assert "Получение курсов валют из currencies.json" in caplog.text
    assert "Завершено получение курсов валют, всего: 2" in caplog.text


# 5. Функция "Стоимость акций из S&P500"
def test_load_stock_success(caplog: LogCaptureFixture) -> None:
    """Тест успешной загрузки акций из JSON файла"""
    caplog.set_level(logging.INFO)
    mock_data = '{"user_stocks": ["AAPL", "GOOGL", "TSLA"]}'

    with patch("builtins.open", mock_open(read_data=mock_data)):
        result = load_stock("test_stocks.json")

    assert result == ["AAPL", "GOOGL", "TSLA"]
    assert "Загружены акции: ['AAPL', 'GOOGL', 'TSLA']" in caplog.text


def test_load_stock_file_not_found(caplog: LogCaptureFixture) -> None:
    """Тест загрузки акций при отсутствии файла"""
    caplog.set_level(logging.ERROR)
    with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
        result = load_stock("nonexistent.json")

    assert result == []
    assert "File not found" in caplog.text


@patch("src.utils.stock_price_api")
def test_fetch_stock_prices_success(mock_stock_api: Mock, caplog: LogCaptureFixture) -> None:
    """Тест успешного получения цен акций"""
    caplog.set_level(logging.INFO)
    mock_stock_api.side_effect = [150.25, 2750.50, 850.75]
    stocks = ["AAPL", "GOOGL", "TSLA"]

    result = fetch_stock_prices(stocks)

    expected = [
        {"stock": "AAPL", "price": 150.25},
        {"stock": "GOOGL", "price": 2750.50},
        {"stock": "TSLA", "price": 850.75},
    ]
    assert result == expected
    assert "Начало получения цен для 3 акций" in caplog.text
    assert "Получение цен для 3 акций" in caplog.text


def test_fetch_stock_prices_empty_list(caplog: LogCaptureFixture) -> None:
    """Тест получения цен при пустом списке акций"""
    caplog.set_level(logging.ERROR)
    result = fetch_stock_prices([])

    assert result == []
    assert "Пустой список акций передан в fetch_stock_prices" in caplog.text


@patch("src.utils.requests.get")
def test_stock_price_api_success(mock_get: Mock, caplog: LogCaptureFixture) -> None:
    """Тест успешного получения цены акции через API"""
    caplog.set_level(logging.INFO)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Global Quote": {"05. price": "150.2500"}}
    mock_get.return_value = mock_response

    result = stock_price_api("AAPL")

    assert result == 150.25
    assert "Цена акции AAPL: 150.25" in caplog.text


@patch("src.utils.requests.get")
def test_stock_price_api_no_data(mock_get: Mock, caplog: LogCaptureFixture) -> None:
    """Тест получения цены акции когда нет данных"""
    caplog.set_level(logging.ERROR)
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Global Quote": {}}
    mock_get.return_value = mock_response

    result = stock_price_api("INVALID")

    assert result == 0.0
    assert "Нет данных для акции INVALID" in caplog.text


@patch("src.utils.requests.get")
def test_stock_price_api_request_error(mock_get: Mock, caplog: LogCaptureFixture) -> None:
    """Тест ошибки запроса для акции (status code не 200)"""
    caplog.set_level(logging.ERROR)
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = stock_price_api("INVALID_STOCK")

    assert result == 0.0
    assert "Ошибка запроса для акции INVALID_STOCK: 404" in caplog.text


@patch("src.utils.requests.get")
def test_stock_price_api_exception(mock_get: Mock, caplog: LogCaptureFixture) -> None:
    """Тест исключения при запросе цены акции"""
    caplog.set_level(logging.ERROR)
    mock_get.side_effect = Exception("Timeout error")

    result = stock_price_api("AAPL")

    assert result == 0.0
    assert "Исключение при запросе акции AAPL: Timeout error" in caplog.text


@patch("src.utils.fetch_stock_prices")
@patch("src.utils.load_stock")
def test_get_stock_prices_success(mock_load: Mock, mock_fetch: Mock, caplog: LogCaptureFixture) -> None:
    """Тест успешного получения цен акций"""
    caplog.set_level(logging.INFO)
    mock_load.return_value = ["AAPL", "GOOGL"]
    mock_fetch.return_value = [{"stock": "AAPL", "price": 150.25}, {"stock": "GOOGL", "price": 2750.50}]

    result = get_stock_prices("stocks.json")

    assert len(result) == 2
    assert "Начало получения цен на акции из stocks.json" in caplog.text
    assert "Завершено получение цен на акции, всего: 2" in caplog.text
