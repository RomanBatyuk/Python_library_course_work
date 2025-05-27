import datetime
from unittest.mock import MagicMock, patch

import pytest

from src import utils


@pytest.fixture
def sample_transaction():
    return {
        "Сумма операции": "1000",
        "Валюта операции": "USD",
        "Сумма операции с округлением": "1000.00",
        "Дата операции": "01.05.2023 12:00:00",
        "Категория": "Категория1",
        "Описание": "Описание транзакции",
        "Номер карты": "1234",
    }


@pytest.mark.parametrize(
    "currency, api_response, expected",
    [
        ("USD", {"result": 75.5}, 75.5),
        ("EUR", {"result": 85.3}, 85.3),
    ],
)
def test_get_transaction_amount_convert(sample_transaction, currency, api_response, expected):
    sample_transaction["Валюта операции"] = currency

    # Мокаем os.getenv для получения API_KEY
    with patch("os.getenv", return_value="test_api_key"):
        mock_response = MagicMock()
        mock_response.json.return_value = api_response
        with patch("requests.get", return_value=mock_response):
            result = utils.get_transaction_amount(sample_transaction)
            assert result == expected


def test_get_transaction_amount_rub():
    transaction = {"Сумма операции": "500", "Валюта операции": "RUB", "Сумма операции с округлением": "500.00"}
    result = utils.get_transaction_amount(transaction)
    assert result == 500.0


def test_get_transaction_amount_non_rub_no_api_call(sample_transaction):
    sample_transaction["Валюта операции"] = "GBP"

    with patch("os.getenv", return_value="test_api_key"):
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": 123.45}
            mock_get.return_value = mock_response

            amount = utils.get_transaction_amount(sample_transaction)
            assert amount == round(123.45, 2)


def test_read_excel_reads_file():
    sample_data = [
        {
            "Сумма операции": "100",
            "Валюта операции": "USD",
            "Сумма операции с округлением": "100.00",
            "Дата операции": "01.05.2023 12:00:00",
            "Категория": "Категория1",
            "Описание": "desc",
            "Номер карты": "1234",
        }
    ]

    class DummyDataFrame:
        def to_dict(self, orient):
            return sample_data

    with patch("pandas.read_excel", return_value=DummyDataFrame()):
        transactions = utils.read_excel("data/operations.xlsx")
        assert transactions == sample_data


@pytest.mark.parametrize(
    "input_str,expected_date",
    [
        ("2023-05-15 10:20:30", datetime.datetime(2023, 5, 15, 10, 20, 30)),
    ],
)
def test_sort_transact_by_date_filters(
    input_str,
    expected_date,
):
    data = [
        {"Сумма операции": "100", "Сумма платежа": "50", "Дата операции": "15.05.2023 09:00:00"},
        {"Сумма операции": "-200", "Сумма платежа": "-150", "Дата операции": "14.05.2023 10:00:00"},
        {"Сумма операции": "300", "Сумма платежа": "200", "Дата операции": "16.05.2023 11:00:00"},
    ]

    with patch("builtins.input", return_value=input_str):
        filtered = utils.sort_transact_by_date(data)

        assert all(
            datetime.datetime.strptime(i["Дата операции"], "%d.%m.%Y %H:%M:%S").month == expected_date.month
            and datetime.datetime.strptime(i["Дата операции"], "%d.%m.%Y %H:%M:%S").year == expected_date.year
            and 1 <= datetime.datetime.strptime(i["Дата операции"], "%d.%m.%Y %H:%M:%S").day <= expected_date.day
            for i in filtered
        )


def test_answer_file_merges_data_and_requests(monkeypatch):

    transactions = [
        {
            "Номер карты": None,
            "Сумма платежа": 50,
            "Сумма операции с округлением": "1000",
            "Дата операции": "01.05.2023 12:00:00",
            "Категория": "Cat1",
            "Описание": None,
        },
        {
            "Номер карты": "5678",
            "Сумма платежа": 200,
            "Сумма операции с округлением": "2000",
            "Дата операции": "02.05.2023 13:30:00",
            "Категория": "Cat2",
            "Описание": "desc2",
        },
    ]

    def fake_get_transaction_amount(transaction):
        return float(transaction["Сумма операции с округлением"]) / 100

    monkeypatch.setattr(utils, "get_transaction_amount", fake_get_transaction_amount)

    def mock_requests_get(url, headers=None):
        class Response:
            def json(self_inner):
                if url.startswith("https://api.apilayer.com/exchangerates_data/latest"):
                    return {"rates": {"RUB": 75}}
                elif url.startswith("https://www.alphavantage.co/query"):
                    symbol = url.split("symbol=")[-1]
                    return {"Global Quote": {"05. price": str(150 + len(symbol))}}
                else:
                    return {}

        return Response()

    with patch("requests.get", side_effect=mock_requests_get):
        result = utils.answer_file(transactions)

        assert isinstance(result, dict)

        assert set(result.keys()) >= {"cards", "top_transactions", "currency_rates"}

        cards = result["cards"]
        assert all(isinstance(c, dict) for c in cards)

        top_txns = result["top_transactions"]
        assert len(top_txns) <= 5

        currency_rates = result["currency_rates"]
        currencies = {c["currency"]: c["rate"] for c in currency_rates}

        assert set(currencies.keys()) >= {"USD", "EUR"}


@pytest.mark.parametrize(
    "symbol_list",
    [
        (["AAPL", "AMZN"]),
    ],
)
def test_answer_file_stock_prices(symbol_list):
    def mock_requests_get(url, *args, **kwargs):
        class Response:
            def json(self_inner):
                if "exchangerates_data" in url:
                    # Мокаем ответ с ключом 'rates'
                    return {"rates": {"RUB": 75.0}}
                else:
                    s = url.split("symbol=")[-1]
                    return {"Global Quote": {"05. price": str(100 + len(s))}}

        return Response()

    with patch("requests.get", side_effect=mock_requests_get):
        result = utils.answer_file([])
        stock_prices = result.get("stock_prices", [])
        for stock in stock_prices:
            assert stock["stock"] in symbol_list or isinstance(stock["price"], float)
