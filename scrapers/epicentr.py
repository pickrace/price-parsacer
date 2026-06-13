"""
Епіцентр (epicentrk.ua).

Великий маркетплейс, важкий фронтенд -> ціна найімовірніше рендериться через JS.
Тому requires_js = True (як і Rozetka). Коли дійдеш до Епіцентру — реалізуй
через Playwright (див. коментар у rozetka.py) і перемкни прапорець.

URL-патерн пошуку та селектори нижче — ПЕРЕВІРИТИ локально.
"""

from __future__ import annotations

import urllib.parse

from bs4 import BeautifulSoup

from .base import Scraper


class EpicentrScraper(Scraper):
    name = "Епіцентр"
    base_url = "https://epicentrk.ua"
    requires_js = True  # <- перемкни на False, коли реалізуєш Playwright

    def search_url(self, query: str) -> str:
        q = urllib.parse.quote(query)
        # ПЕРЕВІРИТИ патерн: можливо /ua/search/{query}/ замість ?q=
        return f"{self.base_url}/ua/search/?q={q}"

    def parse_search(self, soup: BeautifulSoup) -> str | None:
        first = soup.select_one("a.product-tile__title, .products-list a")
        return first.get("href") if first else None

    def parse_price(self, soup: BeautifulSoup) -> float | None:
        el = soup.select_one(".product-price__top, [itemprop='price']")
        if el is None:
            return None
        return self.clean_price(el.get("content") or el.get_text())
