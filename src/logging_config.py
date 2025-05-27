import logging
import os


def setup_module_logger(module_name: str):
    """
    Настраивает логгер для модуля.
    Логи пишутся в файл data/<module_name>.log с перезаписью при каждом запуске.
    """
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{module_name}.log")

    # Создаем или очищаем файл лога при каждом запуске
    with open(log_file, "w"):
        pass

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    # Создаем обработчик файла
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)

    # Форматтер для логов
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    if not logger.hasHandlers():
        logger.addHandler(fh)

    return logger
