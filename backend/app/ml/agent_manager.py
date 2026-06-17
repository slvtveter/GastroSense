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

# Tried in order. gemini-2.5-flash is the better model but has a tiny free-tier
# daily quota (20 RPD); gemini-3.1-flash-lite is a step down in quality but has
# a much higher daily quota (500 RPD), so it's a sane fallback once the first
# model's quota is exhausted instead of just failing for the rest of the day.
GEMINI_MODEL_CANDIDATES = ["gemini-2.5-flash", "gemini-3.1-flash-lite"]


def _is_quota_error(error: Exception) -> bool:
    message = str(error).lower()
    return "429" in message or "quota" in message or "rate" in message


class AgentManager:
    def __init__(self):
        self.name = "RAG-Analyst-Agent"
        api_key = os.getenv("GEMINI_API_KEY")
        if genai and api_key:
            # Strip quotes if they were accidentally added in .env
            api_key = api_key.strip('"').strip("'")
            genai.configure(api_key=api_key)
            self.models = [genai.GenerativeModel(name) for name in GEMINI_MODEL_CANDIDATES]
        else:
            self.models = []
            print("WARNING: Gemini is unavailable during AgentManager init.")

    async def process_query(self, query: str):
        # 1. RAG: Ищем контекст в наших данных
        # The corpus is now ~7 rollup chunks total (one per data domain)
        # instead of ~90 per-row chunks, so top_k=8 effectively returns
        # everything relevant instead of gambling on which 5 chunks rank highest.
        context = rag_engine.build_context(query, top_k=8)

        if not self.models:
            return (
                "Gemini isn't configured yet. Here's what RAG found:\n\n"
                f"{context}"
            )

        # 2. Формируем промпт для Gemini
        prompt = f"""
        You are an expert restaurant analyst for GastroSense.
        Reply in the same language the user's question is written in (English or Russian), concisely and to the point.
        Use only the relevant context from the RAG retrieval below. If the context doesn't have enough data, say so plainly instead of making up numbers.
        Where possible, cite sources in the format [source:title].

        Context:
        {context}

        User question:
        {query}
        """

        # 3. Отправляем в Gemini, при квоте/рейт-лимите пробуем следующую модель
        last_error: Exception | None = None
        for index, model in enumerate(self.models):
            try:
                response = model.generate_content(prompt)
                return response.text or "Couldn't generate a response."
            except Exception as e:
                last_error = e
                is_last_candidate = index == len(self.models) - 1
                if _is_quota_error(e) and not is_last_candidate:
                    print(f"DEBUG: {GEMINI_MODEL_CANDIDATES[index]} hit quota, falling back to next model.")
                    continue
                print(f"DEBUG: AI Error: {e}")
                break

        return f"AI error: {last_error}. Check your API key."

# Создаем глобальный экземпляр
agent_manager = AgentManager()
