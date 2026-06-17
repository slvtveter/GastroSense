import os
from dotenv import load_dotenv
from app.ml.rag_engine import rag_engine
try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled at runtime
    genai = None

# Force load dotenv here just in case
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class AgentManager:
    def __init__(self):
        self.name = "RAG-Analyst-Agent"
        api_key = os.getenv("GEMINI_API_KEY")
        if genai and api_key:
            # Strip quotes if they were accidentally added in .env
            api_key = api_key.strip('"').strip("'")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
            print("WARNING: Gemini is unavailable during AgentManager init.")

    async def process_query(self, query: str):
        # 1. RAG: Ищем контекст в наших данных
        context = rag_engine.build_context(query, top_k=5)

        if not self.model:
            return (
                "Gemini пока не настроен. Вот что нашёл RAG:\n\n"
                f"{context}"
            )
        
        # 2. Формируем промпт для Gemini
        prompt = f"""
        Ты - эксперт-аналитик ресторана GastroSense.
        Отвечай по-русски, кратко и по делу.
        Используй только релевантный контекст из RAG. Если данных в контексте недостаточно, так и скажи и не выдумывай цифры.
        По возможности ссылайся на источники в формате [source:title].
        
        Контекст:
        {context}

        Вопрос пользователя:
        {query}
        """
        
        # 3. Отправляем в Gemini
        try:
            response = self.model.generate_content(prompt)
            return response.text or "Не удалось сформировать ответ."
        except Exception as e:
            error_msg = str(e)
            print(f"DEBUG: AI Error: {error_msg}")
            return f"Ошибка AI: {error_msg}. Проверьте ваш API ключ."

# Создаем глобальный экземпляр
agent_manager = AgentManager()
