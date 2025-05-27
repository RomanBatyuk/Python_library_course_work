from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pandas as pd
import pytest


@pytest.fixture(scope="session", autouse=True)
def patch_pandas_read_excel():
    with patch("pandas.read_excel") as mock_read:
        mock_read.return_value = pd.DataFrame()
        global reports
        import src.reports as reports

        yield


@pytest.fixture
def mock_transactions():
    data = {
        "Дата платежа": ["01.01.2023", "15.02.2023", "10.03.2023", "05.04.2023"],
        "Категория": ["Продукты", "Транспорт", "Продукты", "Развлечения"],
        "Сумма": [100, 200, 150, 300],
    }
    return pd.DataFrame(data)


def test_spending_by_category_returns_correct_data(mock_transactions):
    with patch("src.utils.read_excel", return_value=mock_transactions):
        fixed_now = datetime(2023, 4, 10)
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            result = reports.spending_by_category(mock_transactions.copy(), "Продукты", date="01.04.2023")
            assert isinstance(result, pd.DataFrame)
            categories = result["Категория"]
            if isinstance(categories, pd.Series):
                categories_str = categories.astype(str).str.strip().str.lower()
                assert all(categories_str == "продукты")
            else:
                assert categories.strip().lower() == "продукты"
            assert len(result) >= 1


def test_spending_by_category_without_date(mock_transactions):
    with patch("src.utils.read_excel", return_value=mock_transactions):
        fixed_now = datetime(2023, 4, 10)
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
            result = reports.spending_by_category(mock_transactions.copy(), "Транспорт")
            assert isinstance(result, str)
            assert "Нет транзакций для категории" in result


def test_spending_by_category_missing_column():
    df = pd.DataFrame({"SomeColumn": [1, 2]})
    with pytest.raises(ValueError):
        reports.spending_by_category(df, "Категория")


def test_save_report_decorator_writes_file():
    mock_df = pd.DataFrame({"A": [1, 2]})
    with patch("builtins.open", new_callable=MagicMock) as m_open:
        handle_mock = MagicMock()
        m_open.return_value.__enter__.return_value = handle_mock

        @reports.save_report("testfile.txt")
        def dummy_func():
            return mock_df

        result = dummy_func()

        calls = handle_mock.write.call_args_list

        expected_lines = result.to_csv(index=False).splitlines(keepends=True)

        written_strings = [call_args[0][0] for call_args in calls]
        for line in expected_lines:
            assert line in written_strings, f"Строка '{line}' не найдена в вызовах write"


def test_generate_spending_report_calls_spending_by_category_and_saves():
    df = pd.DataFrame({"Дата платежа": ["01.01.2023"], "Категория": ["Продукты"], "Сумма": [100]})
    with (
        patch("src.utils.read_excel", return_value=df),
        patch.object(reports, "spending_by_category", return_value=df),
    ):
        # Патчим open только внутри функции
        with patch("builtins.open", create=True) as m_open:
            handle_mock = MagicMock()
            m_open.return_value.__enter__.return_value = handle_mock

            result = reports.generate_spending_report(df.copy(), "Продукты")

            calls = reports.spending_by_category.call_args_list
            assert len(calls) == 1
            args, kwargs = calls[0]
            assert args[0].equals(df.copy()), "Первый аргумент не совпадает"
            assert args[1] == "Продукты", "Второй аргумент не совпадает"

            m_open.assert_any_call("spending_report.txt", "w", encoding="utf-8")

            calls_write = handle_mock.write.call_args_list
            assert len(calls_write) >= 2, "Ожидалось минимум два вызова write()"

            assert calls_write[0] == call(
                "Дата платежа,Категория,Сумма\r\n"
            ), "Первый вызов write() не содержит заголовки"

            assert calls_write[1] == call("01.01.2023,Продукты,100\r\n"), "Второй вызов write() не содержит данных"

            assert result.equals(df)
