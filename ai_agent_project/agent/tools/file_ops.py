import os
import json
from typing import Dict, Any
from .base import Tool


class FileOperationsTool(Tool):
    """Инструмент для работы с файлами"""

    @property
    def name(self) -> str:
        return "file_operations"

    @property
    def description(self) -> str:
        return "Читает, записывает и управляет файлами на локальной системе."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Тип операции: read, write, list",
                    "enum": ["read", "write", "list"],
                },
                "file_path": {"type": "string", "description": "Путь к файлу"},
                "content": {
                    "type": "string",
                    "description": "Содержимое для записи (только для операции write)",
                },
            },
            "required": ["operation", "file_path"],
        }

    def execute(self, **kwargs) -> str:
        operation = kwargs.get("operation", "")
        file_path = kwargs.get("file_path", "")
        content = kwargs.get("content", "")

        if not operation or not file_path:
            return "Ошибка: не предоставлены обязательные параметры"

        # Безопасность: ограничиваем доступ к определенным директориям
        safe_path = self._get_safe_path(file_path)

        try:
            if operation == "read":
                return self._read_file(safe_path)
            elif operation == "write":
                return self._write_file(safe_path, content)
            elif operation == "list":
                return self._list_directory(safe_path)
            else:
                return f"Неизвестная операция: {operation}"
        except Exception as e:
            return f"Ошибка операции с файлом: {str(e)}"

    def _get_safe_path(self, file_path: str) -> str:
        """Обеспечивает безопасный путь в пределах рабочей директории"""
        # Нормализуем путь (заменяем обратные слеши на прямые, убираем лишние точки)
        file_path = file_path.replace("\\", "/").replace("../", "").replace("./", "")

        base_dir = os.path.abspath("workspace")
        os.makedirs(base_dir, exist_ok=True)

        # Если путь абсолютный, делаем его относительным к workspace
        if os.path.isabs(file_path):
            file_path = file_path.lstrip("/").lstrip("\\")

        full_path = os.path.abspath(os.path.join(base_dir, file_path))

        # Проверяем, что путь остается внутри workspace
        if not full_path.startswith(base_dir):
            raise PermissionError("Доступ за пределы рабочей директории запрещен")

        return full_path

    def _read_file(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _write_file(self, file_path: str, content: str) -> str:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Файл успешно записан: {file_path}"

    def _list_directory(self, dir_path: str) -> str:
        if not os.path.isdir(dir_path):
            return f"Путь не является директорией: {dir_path}"

        items = os.listdir(dir_path)
        result = []
        for item in items:
            full_path = os.path.join(dir_path, item)
            if os.path.isdir(full_path):
                result.append(f"[DIR] {item}")
            else:
                result.append(f"[FILE] {item}")

        return "\n".join(result) if result else "Директория пуста"
