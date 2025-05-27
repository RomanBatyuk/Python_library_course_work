import json
import re
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_read_excel_data():
    return [
        {
            "Категория": "Переводы",
            "Описание": "Иванов А.",
            "Номер карты": None,
            "Сумма платежа": "500",
            "Сумма операции": "500",
            "Дата операции": "02.02.2023 14:00:00",
        },
        {
            "Категория": "Переводы",
            "Описание": "Петров Б.",
            "Номер карты": None,
            "Сумма платежа": "700",
            "Сумма операции": "-700",
            "Дата операции": "03.03.2023 15:30:00",
        },
        {
            "Категория": "Переводы",
            "Описание": "Некорректное описание",
            "Номер карты": None,
            "Сумма платежа": "300",
            "Сумма операции": "-300",
            "Дата операции": "04.04.2023 16:45:00",
        },
        {
            "Категория": "Покупки",
        },
    ]


@pytest.mark.parametrize(
    "category, description, expected_in_result", [("Переводы", "Смирнов Г.", True), ("Переводы", "Петров Б.", True)]
)
def test_search_transact_filters_correctly(mock_read_excel_data, category, description, expected_in_result):
    with patch("src.utils.read_excel", return_value=mock_read_excel_data):
        import src.services as services

        result_json = services.search_transact(mock_read_excel_data)
        result = json.loads(result_json)

        pattern = re.compile(r"^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.?$")

        if expected_in_result:
            # Проверяем наличие хотя бы одной транзакции с нужной категорией
            filtered_items = [item for item in result if item["Категория"] == category]
            for item in filtered_items:
                assert pattern.search(item["Описание"]) is not None


@pytest.mark.parametrize(
    "category, description, expected_in_result",
    [
        ("Переводы", "Некорректное описание", False),
        ("Покупки", "", False),
    ],
)
def test_search_transact_filters_correctly_2(mock_read_excel_data, category, description, expected_in_result):
    with patch("src.utils.read_excel", return_value=mock_read_excel_data):
        import src.services as services

        result_json = services.search_transact(mock_read_excel_data)
        result = json.loads(result_json)

        pattern = re.compile(r"^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.?$")

        if expected_in_result:
            for item in result:
                if item["Категория"] == category:
                    assert pattern.search(item["Описание"]) is None
