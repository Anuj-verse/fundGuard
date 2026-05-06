import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # switch via .env
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

def get_llm_client():
    if LLM_PROVIDER == "groq":
        from groq import Groq
        return Groq(api_key=os.environ.get("GROQ_API_KEY"))
    elif LLM_PROVIDER == "ollama":
        # For production/bank deployment only
        import ollama
        return ollama.Client(host=OLLAMA_HOST)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")

