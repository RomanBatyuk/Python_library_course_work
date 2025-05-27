import datetime
import json

from logging_config import setup_module_logger
from reports import spending_by_category, transactions
from services import data_for_search, search_transact
from utils import combining_functionality

logger = setup_module_logger(__name__)

data = datetime.datetime.now()


def welcome_function_main(data):
    """Главная функция, принимающая на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ, согласно шаблону задания"""
    hour = data.hour
    if 6 <= hour < 12:
        greeting = "Доброе утро"
    elif 12 <= hour < 18:
        greeting = "Добрый день"
    elif 18 <= hour < 24:
        greeting = "Добрый вечер"
    else:
        greeting = "Доброй ночи"

    logger.info("Формирование окончательного результата")
    utils = {"greeting": greeting, **combining_functionality()}
    reports_services = [spending_by_category(transactions, "Переводы"), search_transact(data_for_search)]
    logger.info("Вывод окончательного результата")
    return utils, reports_services


if __name__ == "__main__":
    current_time = datetime.datetime.now()
    result_dict = welcome_function_main(current_time)
    print(json.dumps(result_dict, ensure_ascii=False))
