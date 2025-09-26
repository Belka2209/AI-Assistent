import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки приложения"""

    def __init__(self):
        self.llm_model = os.getenv("LLM_MODEL", "llama3.2:latest")
        self.max_iterations = int(os.getenv("MAX_ITERATIONS", "10"))
        self.enable_web_search = (
            os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"
        )

        # Настройки UI
        self.enable_rich_ui = os.getenv("ENABLE_RICH_UI", "true").lower() == "true"


settings = Settings()
