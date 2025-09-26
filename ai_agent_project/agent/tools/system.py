import platform
import psutil
import datetime
from typing import Dict, Any
from .base import Tool


class SystemInfoTool(Tool):
    """Инструмент для получения информации о системе"""

    @property
    def name(self) -> str:
        return "system_info"

    @property
    def description(self) -> str:
        return "Предоставляет информацию о системе: использование CPU, памяти, диска и т.д."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "description": "Тип информации: cpu, memory, disk, all",
                    "enum": ["cpu", "memory", "disk", "all"],
                }
            },
            "required": ["info_type"],
        }

    def execute(self, **kwargs) -> str:
        info_type = kwargs.get("info_type", "all")

        try:
            if info_type == "cpu":
                return self._get_cpu_info()
            elif info_type == "memory":
                return self._get_memory_info()
            elif info_type == "disk":
                return self._get_disk_info()
            elif info_type == "all":
                return self._get_all_info()
            else:
                return f"Неизвестный тип информации: {info_type}"
        except Exception as e:
            return f"Ошибка получения информации о системе: {str(e)}"

    def _get_cpu_info(self) -> str:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        return f"CPU: {cpu_count} ядер, использование: {cpu_percent}%"

    def _get_memory_info(self) -> str:
        memory = psutil.virtual_memory()
        return f"Память: использовано {memory.percent}% ({memory.used // 1024 // 1024}MB / {memory.total // 1024 // 1024}MB)"

    def _get_disk_info(self) -> str:
        disk = psutil.disk_usage("/")
        return f"Диск: использовано {disk.percent}% ({disk.used // 1024 // 1024}MB / {disk.total // 1024 // 1024}MB)"

    def _get_all_info(self) -> str:
        cpu_info = self._get_cpu_info()
        memory_info = self._get_memory_info()
        disk_info = self._get_disk_info()

        return f"Информация о системе:\n{cpu_info}\n{memory_info}\n{disk_info}"
