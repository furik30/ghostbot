from typing import Callable, Dict, List, Any
import re
from utils.logger import setup_logger

logger = setup_logger("CommandRegistry")

class CommandRegistry:
    def __init__(self):
        # Структура: { "команда": handler_function }
        self.commands: Dict[str, Callable] = {}
        # Структура: { "команда": "описание" } (для справки)
        self.descriptions: Dict[str, str] = {}

    def register(self, triggers: List[str], handler: Callable, description: str = ""):
        """
        Регистрирует обработчик для списка триггеров.
        Пример: register(['.r', '.к'], handle_reply, "Генерация ответа")
        """
        for trigger in triggers:
            if trigger in self.commands:
                logger.warning(f"Command '{trigger}' is already registered! Overwriting.")
            self.commands[trigger] = handler
            self.descriptions[trigger] = description
        logger.info(f"Registered commands: {triggers}")

    def get_handler(self, text: str):
        r"""
        Ищет обработчик в тексте.
        Использует Regex для поиска триггера, который:
        1. Находится в начале строки ИЛИ предваряется пробельным символом (\s, \n).
        2. Заканчивается концом строки ИЛИ пробельным символом.

        Возвращает: (handler, trigger, args_text) или (None, None, None)
        """
        if not text:
            return None, None, None

        # Сортируем триггеры по длине (обратно), чтобы .roast ловился раньше .r (если бы были пересечения)
        sorted_triggers = sorted(self.commands.keys(), key=len, reverse=True)

        for trigger in sorted_triggers:
            # Экранируем триггер для использования в regex
            escaped_trigger = re.escape(trigger)

            # Паттерн:
            # (?:^|\s) - начало строки или пробельный символ
            # trigger
            # (?:$|\s) - конец строки или пробельный символ
            pattern = r"(?:^|\s)" + escaped_trigger + r"(?:$|\s)"

            match = re.search(pattern, text)

            if match:
                # Нашли совпадение. Теперь нужно понять, это префикс или инфикс.

                # match.start() указывает на начало совпадения (включая пробел перед триггером, если он есть)
                # Нам нужно найти точную позицию самого триггера внутри совпадения.
                # Так как мы знаем, что триггер там есть, используем find, начиная с match.start()
                trigger_start_index = text.find(trigger, match.start())

                # Проверяем текст ДО триггера
                prefix_text = text[:trigger_start_index]

                if not prefix_text.strip():
                    # Если перед триггером только пробелы (или ничего) -> это ПРЕФИКСНАЯ команда.
                    # Возвращаем аргументы (текст после триггера)
                    trigger_end_index = trigger_start_index + len(trigger)
                    args_text = text[trigger_end_index:].strip()
                    return self.commands[trigger], trigger, args_text
                else:
                    # Если перед триггером есть текст -> это ИНФИКСНАЯ/ПОСТФИКСНАЯ команда.
                    # Возвращаем ВЕСЬ текст как аргумент (модуль сам разберется, как его резать)
                    return self.commands[trigger], trigger, text

        return None, None, None

# Глобальный экземпляр реестра
registry = CommandRegistry()
