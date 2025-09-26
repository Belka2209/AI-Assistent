from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json


class Tool(ABC):
    """Базовый класс для всех инструментов"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя инструмента"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Описание инструмента для LLM"""
        pass

    @property
    def parameters(self) -> Dict[str, Any]:
        """Параметры инструмента в формате JSON Schema"""
        return {"type": "object", "properties": {}, "required": []}

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Выполнить инструмент с переданными параметрами"""
        pass

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"
