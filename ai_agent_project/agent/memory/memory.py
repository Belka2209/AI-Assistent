from typing import List, Dict, Any
import json
import datetime


class Memory:
    """Класс для управления памятью агента"""

    def __init__(self, max_messages: int = 100):
        self.max_messages = max_messages
        self.messages: List[Dict[str, Any]] = []
        self.conversation_history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, tool_used: str = None):
        """Добавляет сообщение в память"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat(),
            "tool_used": tool_used,
        }

        self.messages.append(message)
        self.conversation_history.append(message)

        # Ограничиваем размер памяти
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Возвращает последние сообщения"""
        return self.messages[-count:] if self.messages else []

    def get_conversation_context(self) -> str:
        """Возвращает контекст разговора для LLM"""
        if not self.conversation_history:
            return ""

        context = "Контекст предыдущего разговора:\n"
        for msg in self.conversation_history[-5:]:  # Последние 5 сообщений
            role = "Пользователь" if msg["role"] == "user" else "Ассистент"
            context += f"{role}: {msg['content']}\n"
            if msg.get("tool_used"):
                context += f"(Использован инструмент: {msg['tool_used']})\n"

        return context

    def save_to_file(self, file_path: str):
        """Сохраняет память в файл"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "messages": self.messages,
                    "conversation_history": self.conversation_history,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    def load_from_file(self, file_path: str):
        """Загружает память из файла"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.messages = data.get("messages", [])
                self.conversation_history = data.get("conversation_history", [])
        except FileNotFoundError:
            print("Файл памяти не найден, создается новая память")
