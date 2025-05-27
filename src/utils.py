import datetime
import os

import pandas as pd
import requests
from dotenv import load_dotenv

from src.logging_config import setup_module_logger

logger = setup_module_logger(__name__)

list_transact = "data/operations.xlsx"


def get_transaction_amount(transaction: dict):
    """Функция, которая конвертирует сумму транзакции в рубли"""
    load_dotenv()
    api_key = os.getenv("API_KEY")
    header = {"apikey": api_key}
    amount = transaction.get("Сумма операции")
    conv_from = transaction.get("Валюта операции")
    url = f"https://api.apilayer.com/exchangerates_data/convert?to=RUB&from={conv_from}&amount={amount}"
    if conv_from == "RUB":
        logger.info("Возврат суммы в рублях")
        return float(transaction["Сумма операции с округлением"])
    else:
        result = requests.get(url, headers=header).json()
        logger.info(f"Конвертация {conv_from} -> RUB: {round(float(result.get("result")), 2)}")
        return round(float(result.get("result")), 2)


def read_excel(arg):
    """Функция чтения excel файла"""
    df = pd.read_excel(list_transact, dtype=str, engine="openpyxl")
    transactions = df.to_dict(orient="records")
    logger.info("Функция прочитала excel файл и вернула корректные данные для работы программы")
    return transactions


def sort_transact_by_date(data):
    """Функция фильтрует транзакции по дате в диапазоне
    с первого дня месяца из введенной даты по саму введенную дату включительно"""
    inp_user_data = input("Введите дату и время в формате: YYYY-MM-DD HH:MM:SS (пример: '2018-05-03 01:20:20')\n")

    inp_user_data_redact = datetime.datetime.strptime(inp_user_data, "%Y-%m-%d %H:%M:%S")
    logger.info(f"Введенная дата пользователем: {inp_user_data_redact}")
    sort_list_for_data = []  # Отфильтрованный список в нужном диапазоне дат
    y = inp_user_data_redact.year
    m = inp_user_data_redact.month
    d = inp_user_data_redact.day
    for i in data:
        if i["Сумма операции"][0] == "-":
            i["Сумма операции"] = i["Сумма операции"][1:]
            if i["Сумма платежа"][0] == "-":
                i["Сумма платежа"] = i["Сумма платежа"][1:]
        date_obj_i = datetime.datetime.strptime(i["Дата операции"], "%d.%m.%Y %H:%M:%S")
        if date_obj_i.month == m and date_obj_i.year == y and 1 <= date_obj_i.day <= d:
            sort_list_for_data.append(i)
    logger.info(f"Отфильтровано {len(sort_list_for_data)} транзакций по дате")
    return sort_list_for_data


def answer_file(list_transaction):
    """Функция собирает списки словарей согласно заданию"""

    logger.info("cards - выборочные данные по всем транзакциям из sort_list_for_data")
    # cards - выборочные данные по всем транзакциям из sort_list_for_data
    cards = [
        dict(
            last_digits=i["Номер карты"] if i["Номер карты"] is not None else "",
            total_spent=i["Сумма платежа"],
            cashback=round(float(i["Сумма операции с округлением"]) / 100, 2),
        )
        for i in list_transaction
    ]

    logger.info("sort_in_amount - сортировка sort_list_for_data по сумме в порядке убывания")
    # sort_in_amount - сортировка sort_list_for_data по сумме в порядке убывания
    sort_in_amount = sorted(list_transaction, key=lambda x: float(x["Сумма операции с округлением"]), reverse=True)

    logger.info("Отбор первых 5 транзакций из sort_in_amount")
    # Отбор первых 5 транзакций из sort_in_amount
    sort_five = sort_in_amount[:5]

    logger.info("Формирование нового словаря из sort_five с нужными данными")
    # Формирование нового словаря из sort_five с нужными данными
    top_five_transactions = [
        dict(
            date=i["Дата операции"],
            amount=get_transaction_amount(i),
            category=i["Категория"],
            description=i["Описание"] if i["Описание"] is not None else "",
        )
        for i in sort_five
    ]

    logger.info("Стоимость валют -> list[dict]")
    # Стоимость валют -> list[dict]
    currency_rates = [
        dict(
            currency="USD",
            rate=round(
                requests.get(
                    "https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base=USD",
                    headers={"apikey": os.getenv("API_KEY")},
                ).json()["rates"]["RUB"],
                2,
            ),
        ),
        dict(
            currency="EUR",
            rate=round(
                requests.get(
                    "https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base=EUR",
                    headers={"apikey": os.getenv("API_KEY")},
                ).json()["rates"]["RUB"],
                2,
            ),
        ),
    ]

    logger.info("Получение стоимости акций: 'AAPL', 'AMZN', 'GOOGL', 'MSFT', 'TSLA'")
    # Получение стоимости акций: 'AAPL', 'AMZN', 'GOOGL', 'MSFT', 'TSLA'
    api_key = "ALPHAVANTAGE_API_KEY"
    symbols = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    stock_prices = [
        {
            "stock": s,
            "price": float(
                requests.get(
                    f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={s}&apikey={api_key}"
                ).json()["Global Quote"]["05. price"]
            ),
        }
        for s in symbols
    ]

    logger.info("Сборка всех списков словарей согласно заданию")
    # Собираем все списки словарей согласно заданию
    answer_file = dict(
        cards=cards, top_transactions=top_five_transactions, currency_rates=currency_rates, stock_prices=stock_prices
    )
    return answer_file


def combining_functionality():
    """Функция собирающая весь функционал модуля utils.py"""
    sorting = sort_transact_by_date(read_excel(list_transact))
    result = answer_file(sorting)
    return result


# combining_functionality()
