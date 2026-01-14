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
        Ищет обработчик по началу текста.
        Возвращает: (handler, trigger, args_text) или (None, None, None)
        """
        if not text:
            return None, None, None

        # Сортируем триггеры по длине (обратно), чтобы длинные команды (.roast)
        # проверялись раньше коротких (.r), если они пересекаются.
        sorted_triggers = sorted(self.commands.keys(), key=len, reverse=True)

        for trigger in sorted_triggers:
            # Проверяем: либо точное совпадение, либо команда + пробел
            if text == trigger or text.startswith(trigger + " "):
                args_text = text[len(trigger):].strip()
                return self.commands[trigger], trigger, args_text

        return None, None, None

# Глобальный экземпляр реестра
registry = CommandRegistry()
