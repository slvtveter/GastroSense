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

# Tried in order, best quality first. Most Gemini text models on the free tier
# share a tiny ~20 RPD quota, so a 150-question test run burns through several
# of them in minutes. gemini-3.1-flash-lite (500 RPD) and the two Gemma models
# (1.5K RPD each) have far higher daily caps and sit at the end of the chain as
# deep reserves - lower quality, but still better than showing the user a raw
# "out of capacity" error. Model ids must match genai.list_models() exactly
# (e.g. "gemini-3-flash-preview", not "gemini-3-flash") - re-verify with
# list_models() whenever quotas/availability change.
GEMINI_MODEL_CANDIDATES = [
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
]


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
        Do not cite sources inline or after individual sentences. If you used the retrieved context, add a single short citation at the very end of your whole answer, in plain round parentheses (not square brackets), listing only the human-readable titles, e.g. (источник: Menu analysis, Restaurant overview). Never include raw source ids like "database:menu_analysis". If the answer didn't rely on the retrieved context, omit the citation entirely.

        Context:
        {context}

        User question:
        {query}
        """

        # 3. Отправляем в Gemini: при любой ошибке (квота, рейт-лимит, неверное
        # имя модели и т.п.) пробуем следующую модель в цепочке, а не сдаемся
        # сразу. С 7 моделями в списке часть имен/квот может оказаться
        # недействительной или измениться - цепочка должна быть отказоустойчивой
        # к этому, а не только к ошибкам квоты.
        # Per-call timeout so one slow/throttled model can't stall the whole
        # request. Without it, when the high-quality models are rate-limited,
        # each one can take ~10s to fail and the chain stacks up to a 60s+ wait
        # before reaching a model that still has quota. Capping each attempt
        # keeps the worst case bounded and failover snappy.
        last_error: Exception | None = None
        for index, model in enumerate(self.models):
            try:
                response = model.generate_content(prompt, request_options={"timeout": 12})
                return response.text or "Couldn't generate a response."
            except Exception as e:
                last_error = e
                print(f"DEBUG: {GEMINI_MODEL_CANDIDATES[index]} failed ({e}), trying next model.")
                continue

        if _is_quota_error(last_error):
            return (
                "The AI assistant is temporarily at capacity (all models hit their request "
                "quota). Please try again in a minute."
            )
        return "The AI assistant ran into an unexpected error. Please try again shortly."

# Создаем глобальный экземпляр
agent_manager = AgentManager()
