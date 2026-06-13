"""
Rozetka (rozetka.com.ua).

УВАГА: Rozetka — це SPA з захистом від ботів. Ціна рендериться через JS,
тому requests/BS4 НЕ дістане її зі статичного HTML. Тому requires_js = True:
у поточному MVP скрейпер чесно повертає статус "error" з поясненням,
а не вигадує ціну.

Два шляхи зробити робочим (обери один, коли дійдеш до Rozetka):

  A) Playwright (рендеримо сторінку як браузер):
     - встанови:  pip install playwright && playwright install chromium
     - перевизнач run() через headless-браузер, бери ціну з відрендереного DOM.

  B) Внутрішній API Rozetka (швидше, без браузера):
     - пошук і картка товару віддаються через xl-catalog-api.rozetka.com.ua (JSON).
     - надійніше за парсинг HTML, але формат недокументований і може змінюватись.

Поки лишаємо як заглушку з правильними URL-патернами для пошуку.
"""

from __future__ import annotations

import urllib.parse

from bs4 import BeautifulSoup

from .base import Scraper


class RozetkaScraper(Scraper):
    name = "Rozetka"
    base_url = "https://rozetka.com.ua"
    requires_js = True  # <- перемкни на False, коли реалізуєш Playwright/API

    def search_url(self, query: str) -> str:
        q = urllib.parse.quote(query)
        return f"{self.base_url}/ua/search/?text={q}"

    def parse_search(self, soup: BeautifulSoup) -> str | None:
        # ПЕРЕВІРИТИ (актуально лише після переходу на Playwright):
        first = soup.select_one("a.product-link, .goods-tile__heading a")
        return first.get("href") if first else None

    def parse_price(self, soup: BeautifulSoup) -> float | None:
        # ПЕРЕВІРИТИ (актуально лише після переходу на Playwright):
        el = soup.select_one(".product-price__big, .product-prices__big")
        return self.clean_price(el.get_text()) if el else None
