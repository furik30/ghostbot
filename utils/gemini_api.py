import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from config import GEMINI_API_KEY, MODEL_NAME

logger = logging.getLogger("GeminiAPI")

try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Gemini: {e}")

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    safety_settings=safety_settings
)

async def generate_text(contents: list, system_instruction: str = None) -> str:
    """
    Новый метод: принимает список контента (текст, картинки, аудио).
    contents: list of [str, dict(mime_type, data)]
    """
    try:
        final_contents = []
        
        if system_instruction:
            final_contents.append(f"System Instruction: {system_instruction}\n\n")
            
        final_contents.extend(contents)
        
        response = await model.generate_content_async(final_contents)
        return response.text
    except Exception as e:
        logger.error(f"Gemini generation error: {e}")
        return f"⚠️ Gemini Error: {str(e)}"