## 10. main.py (обновленная версия)


import os
import sys
import argparse

# import readline  # Для истории команд в Linux/Mac
from pathlib import Path

# Rich импорты для красивого UI
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeRemainingColumn,
)

from agent.core import AIAgent
from config.settings import settings

console = Console()


def setup_environment():
    """Настраивает рабочее окружение"""
    # Создаем необходимые директории
    directories = ["workspace", "memory", "logs"]
    for dir_name in directories:
        Path(dir_name).mkdir(exist_ok=True)

    console.print("✅ [green]Рабочее окружение настроено[/green]")


def check_ollama():
    """Упрощенная проверка доступности Ollama"""
    try:
        import ollama

        # Простая проверка связи
        try:
            # Пытаемся получить список моделей
            models = ollama.list()
            console.print("✅ [green]Ollama доступен[/green]")

            # Просто проверяем, что ответ получен (не проверяем конкретную модель)
            if models:
                console.print(
                    f"✅ [green]Модели загружены (всего: {len(models.get('models', []))})[/green]"
                )
                return True
            else:
                console.print("❌ [red]Не удалось получить список моделей[/red]")
                return False

        except Exception as e:
            console.print(f"❌ [red]Ollama не отвечает: {e}[/red]")
            console.print("💡 [yellow]Запустите Ollama: ollama serve[/yellow]")
            return False

    except ImportError:
        console.print("❌ [red]Библиотека ollama не установлена[/red]")
        return False


def print_welcome(agent: AIAgent = None):
    """Выводит приветственное сообщение"""
    tools_count = len(agent.list_tools()) if agent else "?"

    welcome_text = f"""
# 🧠 AI Agent с инструментами

**Модель:** `{settings.llm_model}`
**Доступно инструментов:** `{tools_count}`
**Макс. итераций:** `{settings.max_iterations}`

## 🛠️ Доступные инструменты:
- **calculator** - Математические вычисления
- **web_search** - Поиск в интернете {"✅" if settings.enable_web_search else "❌"}
- **file_operations** - Работа с файлами
- **system_info** - Информация о системе

## 💡 Примеры запросов:
- "Посчитай (45 * 78 + 123) / 5"
- "Найди информацию о искусственном интеллекте"
- "Создай файл notes.txt с текстом 'Мои заметки'"
- "Покажи использование памяти и CPU"
- "Прочитай содержимое файла example.txt"

## ⌨️ Команды:
- `/help` - показать эту справку
- `/tools` - список инструментов
- `/memory` - история разговора
- `/save` - сохранить память
- `/load` - загрузить память
- `/clear` - очистить экран
- `/exit` - выйти
"""

    console.print(
        Panel(
            Markdown(welcome_text),
            title="🎯 AI Agent System",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def print_tools_list(agent: AIAgent):
    """Выводит подробный список инструментов"""
    # Проверяем, что агент полностью инициализирован
    if not hasattr(agent, "tools") or not agent.tools:
        console.print("❌ [red]Инструменты еще не загружены[/red]")
        return

    table = Table(
        title="🛠️ Доступные инструменты", show_header=True, header_style="bold magenta"
    )
    table.add_column("Инструмент", style="cyan", width=20)
    table.add_column("Описание", style="white")
    table.add_column("Параметры", style="green")

    for tool_name in agent.list_tools():
        tool_info = agent.get_tool_info(tool_name)
        if tool_info:
            params = []
            if tool_info["parameters"].get("properties"):
                for param_name, param_info in tool_info["parameters"][
                    "properties"
                ].items():
                    param_type = param_info.get("type", "string")
                    params.append(f"{param_name} ({param_type})")

            params_str = ", ".join(params) if params else "нет"
            table.add_row(tool_name, tool_info["description"], params_str)

    console.print(table)


def print_tools_list(agent: AIAgent):
    """Выводит подробный список инструментов"""
    table = Table(
        title="🛠️ Доступные инструменты", show_header=True, header_style="bold magenta"
    )
    table.add_column("Инструмент", style="cyan", width=20)
    table.add_column("Описание", style="white")
    table.add_column("Параметры", style="green")

    for tool_name in agent.list_tools():
        tool_info = agent.get_tool_info(tool_name)
        if tool_info:
            params = []
            if tool_info["parameters"].get("properties"):
                for param_name, param_info in tool_info["parameters"][
                    "properties"
                ].items():
                    param_type = param_info.get("type", "string")
                    params.append(f"{param_name} ({param_type})")

            params_str = ", ".join(params) if params else "нет"
            table.add_row(tool_name, tool_info["description"], params_str)

    console.print(table)


def print_conversation_history(agent: AIAgent):
    """Выводит историю разговора"""
    history = agent.get_conversation_history()

    if not history:
        console.print("📝 [yellow]История разговора пуста[/yellow]")
        return

    table = Table(
        title="📚 История разговора", show_header=True, header_style="bold green"
    )
    table.add_column("Роль", style="cyan", width=10)
    table.add_column("Сообщение", style="white")
    table.add_column("Инструмент", style="yellow", width=15)

    for msg in history[-10:]:  # Последние 10 сообщений
        role = "👤 Пользователь" if msg.get("role") == "user" else "🤖 Агент"
        content = (
            msg.get("content", "")[:100] + "..."
            if len(msg.get("content", "")) > 100
            else msg.get("content", "")
        )
        tool = msg.get("tool_used", "")

        table.add_row(role, content, tool)

    console.print(table)


def setup_argparse() -> argparse.Namespace:
    """Настраивает парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="AI Agent с инструментами - автономная система ИИ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py                          # Запуск с настройками по умолчанию
  python main.py --model mistral         # Использовать модель Mistral
  python main.py --no-rich               # Текстовый режим без Rich
  python main.py --max-iterations 5      # Ограничить количество итераций
        """,
    )

    parser.add_argument(
        "--model",
        default=settings.llm_model,
        help=f"Модель LLM (по умолчанию: {settings.llm_model})",
    )
    parser.add_argument(
        "--no-rich", action="store_true", help="Отключить богатый UI (Rich)"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=settings.max_iterations,
        help=f"Максимальное количество итераций (по умолчанию: {settings.max_iterations})",
    )
    parser.add_argument(
        "--simple", action="store_true", help="Простой режим (минимальный UI)"
    )

    return parser.parse_args()


def main():
    """Основная функция"""
    args = setup_argparse()

    # Обновляем настройки из аргументов
    settings.llm_model = args.model
    settings.max_iterations = args.max_iterations
    if args.no_rich or args.simple:
        settings.enable_rich_ui = False

    console.print(f"🚀 [bold]Запуск AI Agent[/bold]")
    console.print(
        f"📊 Модель: {settings.llm_model}, Итерации: {settings.max_iterations}"
    )

    # Настройка окружения
    setup_environment()

    # Проверка Ollama
    if not check_ollama():
        console.print("❌ [red]Не удалось инициализировать Ollama[/red]")
        sys.exit(1)

    # Инициализация агента с прогресс-баром
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("Инициализация AI агента...", total=100)

        for i in range(100):
            progress.update(task, advance=1)
            import time

            time.sleep(0.02)

        agent = AIAgent()

    console.print("✅ [bold green]AI Agent успешно инициализирован![/bold green]")

    # Проверяем, что инструменты загружены
    if hasattr(agent, "tools") and agent.tools:
        console.print(f"✅ [green]Загружено инструментов: {len(agent.tools)}[/green]")
    else:
        console.print("❌ [red]Инструменты не загружены[/red]")

    # Приветственное сообщение (передаем агента только если он готов)
    if settings.enable_rich_ui and not args.simple:
        print_welcome(agent)
    else:
        console.print("💡 Введите запрос или '/help' для справки")

    # Основной цикл взаимодействия
    while True:
        try:
            # Ввод пользователя с кастомным приглашением
            try:
                user_input = console.input("\n[bold cyan]>>> [/bold cyan]").strip()
            except EOFError:
                console.print("\n👋 До свидания!")
                break

            if not user_input:
                continue

            # Обработка специальных команд
            if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                console.print("👋 [yellow]Завершение работы...[/yellow]")
                break

            elif user_input.lower() in ["/help", "help"]:
                print_welcome(agent)
                continue

            elif user_input.lower() in ["/tools", "/instruments"]:
                # Проверяем, что агент готов
                if hasattr(agent, "list_tools"):
                    print_tools_list(agent)
                else:
                    console.print("❌ [red]Агент еще не готов[/red]")
                continue

            elif user_input.lower() in ["/memory", "/history"]:
                if hasattr(agent, "get_conversation_history"):
                    print_conversation_history(agent)
                else:
                    console.print("❌ [red]Память агента не доступна[/red]")
                continue

            elif user_input.lower() == "/save":
                if hasattr(agent, "save_memory"):
                    result = agent.save_memory()
                    console.print(f"💾 [green]{result}[/green]")
                else:
                    console.print("❌ [red]Функция сохранения не доступна[/red]")
                continue

            elif user_input.lower() == "/load":
                if hasattr(agent, "load_memory"):
                    result = agent.load_memory()
                    console.print(f"📥 [green]{result}[/green]")
                else:
                    console.print("❌ [red]Функция загрузки не доступна[/red]")
                continue

            elif user_input.lower() == "/clear":
                console.clear()
                continue

            elif user_input.lower() == "/debug":
                if hasattr(agent, "iteration_count"):
                    console.print(f"🔧 [yellow]Отладочная информация:[/yellow]")
                    console.print(f"   Итераций за сессию: {agent.iteration_count}")
                    if hasattr(agent, "get_conversation_history"):
                        console.print(
                            f"   Размер памяти: {len(agent.get_conversation_history())} сообщений"
                        )
                continue

            # Обработка обычного запроса
            console.print("🔍 [blue]Анализирую запрос...[/blue]")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeRemainingColumn(),
                transient=True,
            ) as progress:
                task = progress.add_task("Обработка запроса...", total=100)

                # Имитация прогресса с реальной работой
                response = None
                for i in range(100):
                    if i == 50:  # Наполовину - выполняем реальную работу
                        try:
                            response = agent.process_message(user_input)
                        except Exception as e:
                            response = f"❌ Ошибка обработки запроса: {str(e)}"
                    progress.update(task, advance=1)
                    time.sleep(0.01)

            # Вывод результата
            if settings.enable_rich_ui and not args.simple:
                console.print(
                    Panel(
                        Markdown(response),
                        title="[bold green]🤖 Результат[/bold green]",
                        border_style="green",
                        padding=(1, 2),
                    )
                )
            else:
                console.print(f"\n🤖 Агент: {response}")

            console.print("─" * 80)

        except KeyboardInterrupt:
            console.print("\n⏹️ [yellow]Прервано пользователем[/yellow]")
            continue
        except Exception as e:
            console.print(f"❌ [red]Критическая ошибка: {str(e)}[/red]")
            if settings.enable_rich_ui:
                console.print_exception()
            continue


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"💥 [bold red]Фатальная ошибка: {str(e)}[/bold red]")
        sys.exit(1)
