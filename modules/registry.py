from typing import Callable, Dict, List, Any
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
        """
        Ищет обработчик в тексте.
        1. Сначала проверяет префикс (команда в начале).
        2. Затем ищет команду внутри текста (инфикс/постфикс).

        Возвращает: (handler, trigger, args_text) или (None, None, None)
        """
        if not text:
            return None, None, None

        # Сортируем триггеры по длине (обратно)
        sorted_triggers = sorted(self.commands.keys(), key=len, reverse=True)

        # 1. Проверка префикса (стандартный режим)
        for trigger in sorted_triggers:
            if text == trigger or text.startswith(trigger + " "):
                args_text = text[len(trigger):].strip()
                return self.commands[trigger], trigger, args_text

        # 2. Проверка инфикса/постфикса (специальный режим, например для .fix)
        # Ищем триггер, окруженный пробелами, или в конце строки с пробелом перед ним.
        for trigger in sorted_triggers:
            # Варианты: " .cmd ", " .cmd" (конец), ".cmd" (если весь текст - команда, но это попало бы в п.1)
            # Мы ищем " " + trigger
            search_pattern = " " + trigger
            if search_pattern in text:
                 # Если найдено, мы возвращаем ВЕСЬ текст как аргумент,
                 # так как модуль (например text_fixer) должен сам разбить его.
                 # Это важно для логики "Текст .fix Инструкция"
                 return self.commands[trigger], trigger, text

        return None, None, None

# Глобальный экземпляр реестра
registry = CommandRegistry()
