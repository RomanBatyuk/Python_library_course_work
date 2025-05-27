import functools
from datetime import datetime
from typing import Optional

import pandas as pd

from src.logging_config import setup_module_logger

logger = setup_module_logger(__name__)

list_transact = "data/operations.xlsx"
transactions = pd.read_excel(list_transact)


def save_report(file_name="report.txt"):
    """
    Декоратор для сохранения результата функции в файл.
    Можно использовать как с параметром так и без параметров.

    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Записываем результат в файл
            with open(file_name, "w", encoding="utf-8") as f:
                # Если результат — DataFrame или Series, сохраняем его в виде CSV
                if hasattr(result, "to_csv"):
                    result.to_csv(f, index=False)
                else:
                    f.write(str(result))
            return result

        return wrapper

    # Если декоратор вызван без аргументов
    if callable(file_name):
        func = file_name
        file_name = "report.txt"
        return decorator(func)
    else:
        return decorator


@save_report("spending_report.txt")  # Можно указать любой файл или оставить без параметров
def generate_spending_report(transactions: pd.DataFrame, category: str, date: Optional[str] = None):
    """Обертка функции spending_by_category с декоратором для автоматического сохранения"""
    return spending_by_category(transactions, category, date)


def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает транзакции по заданной категории за последние 3 месяца от указанной даты"""
    # Если дата не передана, берем текущую дату
    if date is None:
        current_date = datetime.now()
    else:
        current_date = datetime.strptime(date, "%d.%m.%Y")

    # Проверяем наличие нужных колонок
    if "Дата платежа" not in transactions.columns:
        logger.error("DataFrame должен содержать колонку 'Дата платежа'")
        raise ValueError("DataFrame должен содержать колонку 'Дата платежа'")
    if "Категория" not in transactions.columns:
        logger.error("DataFrame должен содержать колонку 'Категория'")
        raise ValueError("DataFrame должен содержать колонку 'Категория'")

    logger.info("Преобразуем колонку 'Дата платежа' в тип datetime")
    # Преобразуем колонку 'Дата платежа' в тип datetime
    transactions["Дата платежа"] = pd.to_datetime(transactions["Дата платежа"], errors="coerce", dayfirst=True)

    logger.info("Заполняем пропуски в колонке 'Категория' пустой строкой")
    # Заполняем пропуски в колонке 'Категория' пустой строкой
    transactions["Категория"] = transactions["Категория"].fillna("")

    logger.info("Определяем границы периода (последние 3 месяца)")
    # Определяем границы периода (последние 3 месяца)
    start_date = current_date - pd.DateOffset(months=3)

    logger.info("Фильтруем по категории и дате, игнорируя регистр и пробелы")
    # Фильтруем по категории и дате, игнорируя регистр и пробелы
    filtered_transactions = transactions[
        (transactions["Категория"].str.strip().str.lower() == category.lower())
        & (transactions["Дата платежа"] >= start_date)
        & (transactions["Дата платежа"] <= current_date)
    ]

    # Проверяем наличие транзакций и выводим результат
    if filtered_transactions.empty:
        logger.info(f"Нет транзакций для категории '{category}' за 3 месяца заданного диапазона")
        answer = f"Нет транзакций для категории '{category}' за 3 месяца заданного диапазона"
        return answer
    else:
        logger.info("Вывод результата")
        return filtered_transactions


# Вызов функции - результат автоматически сохранится в файл "spending_report.txt"
# generate_spending_report(transactions, "Продукты", "01.01.2024")
