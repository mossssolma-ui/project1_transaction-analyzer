import json
import logging
from typing import Generator
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture

from src.views import views_info

EXCEL_PATH = "data/operations.xlsx"
JSON_PATH = "data/user_settings.json"


@pytest.fixture
def sample_transactions_df() -> pd.DataFrame:
    """Фикстура с примером транзакций"""
    return pd.DataFrame(
        {
            "Дата операции": ["01.05.2021 10:00:00", "10.05.2021 15:30:00"],
            "Сумма операции": [-1000, -500],
            "Номер карты": ["1234567890123456", "9876543210987654"],
            "Сумма платежа": [-1000, -500],
            "Категория": ["Супермаркет", "Транспорт"],
            "Описание": ["Покупка", "Такси"],
        }
    )


@pytest.fixture
def mock_currency_and_stock() -> Generator:
    """Фикстура для мока валют и акций"""
    with patch("src.views.get_currency") as mock_currency, patch("src.views.get_stock_prices") as mock_stock:
        mock_currency.return_value = [{"currency": "USD", "rate": 75.5}]
        mock_stock.return_value = [{"stock": "AAPL", "price": 150.25}]
        yield mock_currency, mock_stock


def test_views_info_success(
    caplog: LogCaptureFixture, sample_transactions_df: pd.DataFrame, mock_currency_and_stock: Mock
) -> None:
    """Тест успешного формирования JSON-ответа"""
    caplog.set_level(logging.INFO)

    with patch("src.views.get_data_period_from_file") as mock_get_data, patch(
        "src.views.get_convert_dates"
    ) as mock_convert:

        mock_convert.return_value = ["01.05.2021 00:00:00", "10.05.2021 23:59:59"]
        mock_get_data.return_value = sample_transactions_df

        result = views_info("2021-05-10 12:00:00")

        response = json.loads(result)
        assert "greeting" in response
        assert "cards" in response
        assert "top_transactions" in response
        assert "currency_rates" in response
        assert "stock_prices" in response

        assert response["greeting"] in ["Доброе утро", "Добрый день", "Добрый вечер", "Доброй ночи"]
        assert len(response["cards"]) == 2
        assert len(response["top_transactions"]) == 2
        assert response["currency_rates"] == [{"currency": "USD", "rate": 75.5}]
        assert response["stock_prices"] == [{"stock": "AAPL", "price": 150.25}]

        assert "Формирование главной страницы для даты: 2021-05-10 12:00:00" in caplog.text
        assert "Главная страница успешно сформирована" in caplog.text


def test_views_info_empty_dataframe(caplog: LogCaptureFixture, mock_currency_and_stock: Mock) -> None:
    """Тест с пустым DataFrame"""
    caplog.set_level(logging.INFO)

    empty_df = pd.DataFrame()

    with patch("src.views.get_data_period_from_file") as mock_get_data, patch(
        "src.views.get_convert_dates"
    ) as mock_convert:

        mock_convert.return_value = ["01.05.2021 00:00:00", "10.05.2021 23:59:59"]
        mock_get_data.return_value = empty_df

        result = views_info("2021-05-10 12:00:00")

        response = json.loads(result)
        assert response["cards"] == []
        assert response["top_transactions"] == []
        assert "greeting" in response


def test_views_info_exception_in_subfunction(caplog: LogCaptureFixture) -> None:
    """Тест обработки исключения внутри одной из функций"""
    caplog.set_level(logging.ERROR)

    with patch("src.views.get_data_period_from_file") as mock_get_data, patch(
        "src.views.get_convert_dates"
    ) as mock_convert, patch("src.views.get_card_spending_summary", side_effect=Exception("Test error")):

        mock_convert.return_value = ["01.05.2021 00:00:00", "10.05.2021 23:59:59"]
        mock_get_data.return_value = pd.DataFrame()

        result = views_info("2021-05-10 12:00:00")

        response = json.loads(result)
        assert response == {"error": "error"}
        assert "Ошибка во views_info для даты 2021-05-10 12:00:00: Test error" in caplog.text


def test_views_info_file_not_found_excel(caplog: LogCaptureFixture, mock_currency_and_stock: Mock) -> None:
    """Тест ошибки при отсутствии Excel-файла"""
    caplog.set_level(logging.ERROR)

    with patch("src.views.get_data_period_from_file") as mock_get_data, patch(
        "src.views.get_convert_dates"
    ) as mock_convert:

        mock_convert.return_value = ["01.05.2021 00:00:00", "10.05.2021 23:59:59"]
        mock_get_data.return_value = pd.DataFrame()

        result = views_info("2021-05-10 12:00:00")

        response = json.loads(result)
        assert response["cards"] == []
        assert response["top_transactions"] == []


def test_views_info_invalid_date_format(caplog: LogCaptureFixture, mock_currency_and_stock: Mock) -> None:
    """Тест с некорректной датой — приветствие по умолчанию"""
    caplog.set_level(logging.INFO)

    with patch("src.views.get_data_period_from_file") as mock_get_data, patch(
        "src.views.get_convert_dates"
    ) as mock_convert:

        mock_convert.return_value = ["01.01.2000 00:00:00", "01.01.2000 23:59:59"]
        mock_get_data.return_value = pd.DataFrame()

        result = views_info("invalid-date")

        response = json.loads(result)
        assert response["greeting"] == "Добрый день"
        assert response["cards"] == []
        assert "Формирование главной страницы для даты: invalid-date" in caplog.text


@patch("src.views.get_currency")
@patch("src.views.get_stock_prices")
def test_views_info_currency_stock_called_with_correct_path(
    mock_stock: Mock, mock_currency: Mock, caplog: LogCaptureFixture
) -> None:
    """Проверка, что валюты и акции загружаются с правильного пути"""
    caplog.set_level(logging.INFO)

    mock_currency.return_value = []
    mock_stock.return_value = []

    with patch("src.views.get_data_period_from_file") as mock_get_data, patch(
        "src.views.get_convert_dates"
    ) as mock_convert:

        mock_convert.return_value = ["01.05.2021 00:00:00", "10.05.2021 23:59:59"]
        mock_get_data.return_value = pd.DataFrame()

        views_info("2021-05-10 12:00:00")

        mock_currency.assert_called_once_with(JSON_PATH)
        mock_stock.assert_called_once_with(JSON_PATH)
