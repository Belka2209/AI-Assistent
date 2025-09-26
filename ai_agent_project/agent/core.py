import ollama
import json
import re
import traceback
from typing import List, Dict, Any, Optional, Tuple
from .tools.base import Tool
from .memory.memory import Memory
from config.settings import settings


class AIAgent:
    """Основной класс AI агента с архитектурой ReAct"""

    def __init__(self):
        self.llm_model = settings.llm_model
        self.memory = Memory()
        self.tools: Dict[str, Tool] = {}
        self.max_iterations = settings.max_iterations
        self.iteration_count = 0

        # Инициализируем инструменты
        self._initialize_tools()

        # Системный промпт
        self.system_prompt = self._create_system_prompt()

    def _initialize_tools(self):
        """Инициализирует все доступные инструменты"""
        try:
            from .tools.calculator import CalculatorTool
            from .tools.web_search import WebSearchTool
            from .tools.file_ops import FileOperationsTool
            from .tools.system import SystemInfoTool

            tool_classes = [
                CalculatorTool,
                WebSearchTool,
                FileOperationsTool,
                SystemInfoTool,
            ]

            for tool_class in tool_classes:
                tool_instance = tool_class()
                self.tools[tool_instance.name] = tool_instance

            print(f"✅ Загружено инструментов: {len(self.tools)}")

        except ImportError as e:
            print(f"❌ Ошибка загрузки инструментов: {e}")

    def _create_system_prompt(self) -> str:
        """Создает системный промпт с описанием инструментов"""

        tools_details = []
        for tool in self.tools.values():
            params_desc = []
            if tool.parameters.get("properties"):
                for param_name, param_info in tool.parameters["properties"].items():
                    param_type = param_info.get("type", "string")
                    param_desc = param_info.get("description", "")
                    required = param_name in tool.parameters.get("required", [])
                    req_text = " (обязательный)" if required else ""
                    params_desc.append(
                        f"    - {param_name} ({param_type}){req_text}: {param_desc}"
                    )

            tools_details.append(f"""
    **{tool.name}**
    Описание: {tool.description}
    Параметры:
    {chr(10).join(params_desc) if params_desc else "    - Нет параметров"}
    """)

        tools_description = "\n".join(tools_details)

        return f"""Ты - интеллектуальный AI агент. Твоя задача - помочь пользователю, используя доступные инструменты когда это необходимо.

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
{tools_description}

ВАЖНО! Отвечай ТОЛЬКО в формате JSON. Не добавляй никакого текста вне JSON.

ФОРМАТ ОТВЕТА:

Если нужен инструмент:
```json
{{
    "thought": "Объясни почему нужен этот инструмент",
    "action": "use_tool",
    "tool": "имя_инструмента",
    "parameters": {{
        "param1": "value1"
    }}
}}
Если можешь ответить напрямую:
{{
    "thought": "Объясни почему инструмент не нужен",
    "action": "direct_response", 
    "response": "Твой ответ"
}}
ПРИМЕР для запроса "сколько файлов в папке Загрузки":
{{
    "thought": "Пользователь хочет узнать количество файлов в папке Загрузки. Нужно использовать file_operations для получения списка файлов.",
    "action": "use_tool",
    "tool": "file_operations",
    "parameters": {{
        "operation": "list",
        "file_path": "Загрузка"
    }}
}}
ПРИМЕР для запроса "привет":
{{
    "thought": "Это простое приветствие, инструмент не нужен.",
    "action": "direct_response",
    "response": "Привет! Я ваш AI помощник. Чем могу помочь?"
}}
Отвечай ТОЛЬКО в этом формате!
"""

    def process_message(self, user_input: str) -> str:
        """Обрабатывает сообщение пользователя с архитектурой ReAct"""
        print(f"🔍 Анализирую запрос: '{user_input}'")
        # Добавляем запрос в память
        self.memory.add_message("user", user_input)

        # Контекст разговора
        context = self.memory.get_conversation_context()
        full_prompt = f"{context}\n\nТекущий запрос пользователя: {user_input}"

        self.iteration_count = 0
        intermediate_results = []

        # Цикл Reasoning + Acting
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            print(f"🔄 Итерация {self.iteration_count}/{self.max_iterations}")

            try:
                # Reasoning: получаем ответ от LLM
                llm_response = self._call_llm(full_prompt)
                print(f"🤖 Ответ LLM: {llm_response[:200]}...")

                # Парсим ответ LLM
                action_data = self._parse_llm_response(llm_response)

                if not action_data:
                    error_msg = "Не удалось распознать ответ LLM"
                    self.memory.add_message("assistant", error_msg)
                    return error_msg

                # Acting: выполняем действие
                if action_data["action"] == "direct_response":
                    # Прямой ответ - завершаем цикл
                    final_response = action_data["response"]
                    self.memory.add_message("assistant", final_response)
                    return final_response

                elif action_data["action"] == "use_tool":
                    # Используем инструмент
                    tool_name = action_data["tool"]
                    tool_params = action_data["parameters"]

                    print(
                        f"🛠️ Использую инструмент: {tool_name} с параметрами: {tool_params}"
                    )

                    # Выполняем инструмент
                    tool_result = self._execute_tool(tool_name, tool_params)
                    intermediate_results.append(f"Результат {tool_name}: {tool_result}")

                    print(f"📊 Результат инструмента: {tool_result[:200]}...")

                    # Обновляем промпт для следующей итерации
                    full_prompt += f"\n\nРезультат выполнения инструмента '{tool_name}': {tool_result}"
                    full_prompt += f"\nПроанализируй этот результат и определи, нужно ли выполнять дополнительные действия или можно дать окончательный ответ пользователю."

                    # Если это последняя итерация, возвращаем накопленные результаты
                    if self.iteration_count == self.max_iterations:
                        final_response = self._format_final_response(
                            intermediate_results, tool_name
                        )
                        self.memory.add_message("assistant", final_response, tool_name)
                        return final_response

                else:
                    error_msg = f"Неизвестное действие: {action_data['action']}"
                    self.memory.add_message("assistant", error_msg)
                    return error_msg

            except Exception as e:
                error_msg = f"Ошибка на итерации {self.iteration_count}: {str(e)}"
                print(f"❌ {error_msg}")
                self.memory.add_message("assistant", error_msg)
                return error_msg

            # Если вышли за пределы максимального количества итераций
            timeout_msg = (
                f"Достигнут лимит итераций ({self.max_iterations}). Накопленные результаты:\n"
                + "\n".join(intermediate_results)
            )
            self.memory.add_message("assistant", timeout_msg)
            return timeout_msg

    def _call_llm(self, prompt: str) -> str:
        """Вызывает LLM с промптом"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ]
            response = ollama.chat(
                model=self.llm_model,
                messages=messages,
                options={
                    "temperature": 0.1,  # Низкая температура для более предсказуемых ответов
                    "num_predict": 500,  # Ограничение длины ответа
                },
            )

            return response["message"]["content"]

        except Exception as e:
            raise Exception(f"Ошибка обращения к LLM: {str(e)}")

    def _parse_llm_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Парсит ответ LLM и извлекает структурированные данные"""
        print(f"🔧 [DEBUG] Получен ответ от LLM: {text}")  # Отладочное сообщение

        try:
            # Очищаем текст от лишних пробелов
            text = text.strip()

            # Сначала пробуем найти JSON в блоке кода
            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                print(f"🔧 [DEBUG] Найден JSON в блоке кода: {json_str}")
            else:
                # Если нет блока кода, ищем JSON в тексте
                json_match = re.search(r"(\{.*\})", text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    print(f"🔧 [DEBUG] Найден JSON в тексте: {json_str}")
                else:
                    # Если JSON не найден, пробуем парсить весь текст
                    json_str = text
                    print(f"🔧 [DEBUG] Пробуем парсить весь текст как JSON")

            # Парсим JSON
            data = json.loads(json_str)
            print(f"🔧 [DEBUG] Успешно распарсен JSON: {data}")

            # Валидация обязательных полей
            if "action" not in data:
                print("❌ [DEBUG] Отсутствует поле 'action'")
                return None

            if data["action"] == "direct_response":
                if "response" not in data:
                    print("❌ [DEBUG] Для direct_response отсутствует поле 'response'")
                    return None

                result = {
                    "action": "direct_response",
                    "thought": data.get("thought", "Прямой ответ"),
                    "response": data["response"],
                }
                print(f"✅ [DEBUG] Распознан direct_response: {result}")
                return result

            elif data["action"] == "use_tool":
                if "tool" not in data or "parameters" not in data:
                    print(
                        "❌ [DEBUG] Для use_tool отсутствуют поля 'tool' или 'parameters'"
                    )
                    return None

                result = {
                    "action": "use_tool",
                    "thought": data.get("thought", "Использование инструмента"),
                    "tool": data["tool"],
                    "parameters": data["parameters"],
                }
                print(f"✅ [DEBUG] Распознан use_tool: {result}")
                return result

            else:
                print(f"❌ [DEBUG] Неизвестное действие: {data['action']}")
                return None

        except json.JSONDecodeError as e:
            print(f"❌ [DEBUG] Ошибка парсинга JSON: {e}")
            print(f"🔧 [DEBUG] Текст который не удалось распарсить: {text}")
            return None
        except Exception as e:
            print(f"❌ [DEBUG] Общая ошибка парсинга: {e}")
            return None

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """Выполняет указанный инструмент"""
        if tool_name not in self.tools:
            return f"Ошибка: инструмент '{tool_name}' не найден"

        tool = self.tools[tool_name]

        try:
            # Валидация параметров
            required_params = tool.parameters.get("required", [])
            for param in required_params:
                if param not in parameters:
                    return f"Ошибка: отсутствует обязательный параметр '{param}'"

            # Выполнение инструмента
            result = tool.execute(**parameters)
            return result

        except Exception as e:
            error_details = f"Ошибка выполнения '{tool_name}': {str(e)}"
            print(f"❌ {error_details}")
            return error_details

    def _format_final_response(
        self, intermediate_results: List[str], last_tool: str
    ) -> str:
        """Форматирует окончательный ответ на основе накопленных результатов"""
        if not intermediate_results:
            return "Не удалось получить результаты выполнения."
        response = "Вот результаты выполнения:\n\n"
        for i, result in enumerate(intermediate_results, 1):
            response += f"{i}. {result}\n\n"

        response += f"Использован инструмент: {last_tool}"
        return response

    def list_tools(self) -> List[str]:
        """Возвращает список доступных инструментов"""
        return list(self.tools.keys())

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию об инструменте"""
        if tool_name not in self.tools:
            return None
        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        }

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Возвращает историю разговора"""
        return self.memory.get_recent_messages(20)

    def save_memory(self, file_path: str = "memory/conversation.json"):
        """Сохраняет память агента"""
        try:
            self.memory.save_to_file(file_path)
            return f"Память сохранена в {file_path}"
        except Exception as e:
            return f"Ошибка сохранения памяти: {str(e)}"

    def load_memory(self, file_path: str = "memory/conversation.json"):
        """Загружает память агента"""
        try:
            self.memory.load_from_file(file_path)
            return f"Память загружена из {file_path}"
        except Exception as e:
            return f"Ошибка загрузки памяти: {str(e)}"
