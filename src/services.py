import json
import re

from src.logging_config import setup_module_logger
from src.utils import list_transact, read_excel

logger = setup_module_logger(__name__)

data_for_search = read_excel(list_transact)


def search_transact(data_for_search):
    """Функция возвращает JSON со всеми транзакциями, которые относятся к переводам физлицам"""
    pattern = re.compile(r"^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.?$")
    logger.info("Возврат JSON со всеми транзакциями, которые относятся к переводам физлицам")
    result = [i for i in data_for_search if i["Категория"] == "Переводы" and pattern.search(i["Описание"]) is not None]
    result_json = json.dumps(result)
    return result_json
