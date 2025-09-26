import math
import operator
from typing import Dict, Any
from .base import Tool


class CalculatorTool(Tool):
    """Инструмент для математических вычислений"""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Выполняет математические вычисления. Поддерживает базовые операции и функции."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Математическое выражение для вычисления",
                }
            },
            "required": ["expression"],
        }

    def execute(self, **kwargs) -> str:
        expression = kwargs.get("expression", "")

        if not expression:
            return "Ошибка: не предоставлено выражение для вычисления"

        try:
            # Безопасное вычисление математических выражений
            result = self._safe_eval(expression)
            return f"Результат: {result}"
        except Exception as e:
            return f"Ошибка вычисления: {str(e)}"

    def _safe_eval(self, expression: str) -> float:
        """Безопасное вычисление математических выражений"""
        # Разрешенные операции и функции
        safe_dict = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "__builtins__": {},
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "pi": math.pi,
            "e": math.e,
        }

        # Добавляем базовые операторы
        safe_dict.update(
            {
                "+": operator.add,
                "-": operator.sub,
                "*": operator.mul,
                "/": operator.truediv,
                "//": operator.floordiv,
                "**": operator.pow,
                "%": operator.mod,
            }
        )

        try:
            return eval(expression, {"__builtins__": {}}, safe_dict)
        except Exception as e:
            raise ValueError(f"Невозможно вычислить выражение '{expression}': {str(e)}")
