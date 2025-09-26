import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, Any
from .base import Tool
from config.settings import settings


class WebSearchTool(Tool):
    """Инструмент для поиска информации в интернете"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Ищет информацию в интернете используя поисковые системы."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос"},
                "max_results": {
                    "type": "integer",
                    "description": "Максимальное количество результатов",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs) -> str:
        if not settings.enable_web_search:
            return "Веб-поиск отключен в настройках. Включите ENABLE_WEB_SEARCH=true в .env файле."

        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        if not query:
            return "Ошибка: не предоставлен поисковый запрос"

        try:
            # Пробуем разные методы поиска
            results = self._search_duckduckgo(query, max_results)
            if results and "не найдены" not in results:
                return results

            # Если DuckDuckGo не сработал, пробуем альтернативный метод
            results = self._search_google_style(query, max_results)
            return results

        except Exception as e:
            return f"Ошибка поиска: {str(e)}. Веб-поиск может быть заблокирован или требуется VPN."

    def _search_duckduckgo(self, query: str, max_results: int) -> str:
        """Поиск через DuckDuckGo с улучшенными заголовками"""
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://html.duckduckgo.com",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        data = {
            "q": query,
            "b": "",
        }

        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Ищем результаты в новой структуре DuckDuckGo
            for result in soup.find_all("div", class_="result", limit=max_results):
                title_elem = result.find("a", class_="result__a")
                snippet_elem = result.find("a", class_="result__snippet")

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    snippet = (
                        snippet_elem.get_text(strip=True)
                        if snippet_elem
                        else "Описание отсутствует"
                    )
                    results.append(f"• {title}: {snippet}")

            if results:
                return f"Результаты поиска по запросу '{query}':\n" + "\n".join(results)
            else:
                return "Результаты не найдены. Попробуйте другой запрос или проверьте подключение к интернету."

        except Exception as e:
            return f"Ошибка DuckDuckGo: {str(e)}"

    def _search_google_style(self, query: str, max_results: int) -> str:
        """Альтернативный метод поиска (имитация)"""
        # В реальном приложении здесь можно использовать API поиска
        # Пока возвращаем информационное сообщение
        return f"""По техническим причинам веб-поиск временно недоступен.

Для запроса "{query}" рекомендуем:

1. Проверить подключение к интернету
2. Включить VPN если требуется
3. Использовать прямые источники:
   - Курс доллара: banki.ru, cbr.ru
   - Новости: yandex.ru/news
   - Погода: gismeteo.ru

Или уточните запрос для более точной помощи."""

    def _search_news_api(self, query: str, max_results: int) -> str:
        """Метод для использования News API (требуется API ключ)"""
        # Это пример для будущего расширения
        api_key = "YOUR_NEWS_API_KEY"  # Нужно получить на newsapi.org
        if api_key == "YOUR_NEWS_API_KEY":
            return "Для работы поиска новостей требуется API ключ News API."

        url = f"https://newsapi.org/v2/everything?q={query}&pageSize={max_results}&apiKey={api_key}"

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if data["status"] == "ok":
                articles = data["articles"]
                results = []
                for article in articles:
                    title = article["title"]
                    description = article["description"] or "Описание отсутствует"
                    results.append(f"• {title}: {description}")

                return f"Новости по запросу '{query}':\n" + "\n".join(results)
            else:
                return "Ошибка при получении новостей"

        except Exception as e:
            return f"Ошибка News API: {str(e)}"

    def execute(self, **kwargs) -> str:
        if not settings.enable_web_search:
            return "Веб-поиск отключен в настройках."

        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        if not query:
            return "Ошибка: не предоставлен поисковый запрос"

        try:
            # Пробуем разные методы с прокси
            results = self._search_with_proxy(query, max_results)
            return results

        except Exception as e:
            return f"Ошибка поиска: {str(e)}. Попробуйте включить VPN."

    def _search_with_proxy(self, query: str, max_results: int) -> str:
        """Поиск с использованием прокси/VPN"""

        # Список бесплатных прокси (может меняться)
        free_proxies = [
            {"http": "http://138.68.60.8:8080"},
            {"http": "http://45.77.98.190:3128"},
            {"http": "http://51.158.68.68:8811"},
        ]

        for proxy in free_proxies:
            try:
                print(f"🔧 Пробую прокси: {proxy}")
                results = self._try_search_with_proxy(query, max_results, proxy)
                if results and "не найдены" not in results:
                    return f"✅ Найдено через прокси:\n{results}"
            except Exception as e:
                print(f"❌ Прокси не сработал: {e}")
                continue

        return "Не удалось выполнить поиск через доступные прокси. Рекомендуется установить VPN расширение в браузере."

    def _try_search_with_proxy(self, query: str, max_results: int, proxy: dict) -> str:
        """Попытка поиска через конкретный прокси"""
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/x-www-form-urlencoded",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }

        data = {"q": query}

        response = requests.post(
            url, headers=headers, data=data, proxies=proxy, timeout=10
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = []

        for result in soup.find_all("div", class_="result", limit=max_results):
            title_elem = result.find("a", class_="result__a")
            snippet_elem = result.find("a", class_="result__snippet")

            if title_elem:
                title = title_elem.get_text(strip=True)
                snippet = (
                    snippet_elem.get_text(strip=True)
                    if snippet_elem
                    else "Описание отсутствует"
                )
                results.append(f"• {title}: {snippet}")

        if results:
            return "\n".join(results)
        else:
            return "Результаты не найдены"
