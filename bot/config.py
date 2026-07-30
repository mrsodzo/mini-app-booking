import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str
    database_url: str = "sqlite:///./data/bot.db"
    admin_chat_id: Optional[int] = None
    webapp_url: str = "https://your-netlify-app.netlify.app"

    @classmethod
    def from_env(cls) -> "Settings":
        admin_chat_id = os.getenv("ADMIN_CHAT_ID")
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            database_url=os.getenv("DATABASE_URL", "sqlite:///./data/bot.db"),
            admin_chat_id=int(admin_chat_id) if admin_chat_id else None,
            webapp_url=os.getenv("WEBAPP_URL", "https://your-netlify-app.netlify.app"),
        )


settings = Settings.from_env()