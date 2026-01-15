import re
from typing import List

def clean_html(text: str) -> str:
    """
    Cleans up HTML tags from the text:
    - Replaces <br>, <br/>, <br /> with newlines.
    - Removes all other HTML tags.
    """
    if not text:
        return ""

    # Заменяем <br> на \n
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # Удаляем остальные теги
    text = re.sub(r'<[^>]+>', '', text)

    return text

def split_text(text: str, limit: int = 4000) -> List[str]:
    """
    Разбивает текст на части, не превышающие лимит.
    """
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        # Пытаемся найти перенос строки перед лимитом
        split_at = text.rfind('\n', 0, limit)
        if split_at == -1:
            # Если нет переноса, ищем пробел
            split_at = text.rfind(' ', 0, limit)

        if split_at == -1:
            # Если нет ни пробелов, ни переносов, режем жестко
            split_at = limit

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip() # Убираем пробел/перенос в начале следующего чанка

    return chunks
