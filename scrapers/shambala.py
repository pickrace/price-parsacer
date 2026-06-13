"""
Shambala (shambala.com.ua).

З файлу price-matching видно, що сайт використовує пошук з параметром ?q=
(посилання в файлі мають хвости типу ...?q=leatherman%20wave).
Менший сайт на CMS -> requests/BS4 має спрацювати без JS.

!!! СЕЛЕКТОРИ НИЖЧЕ — ПЛЕЙСХОЛДЕРИ. Перевір локально через DevTools
    (інструкція в README -> "Як знайти селектори").
"""

from __future__ import annotations

import urllib.parse

from bs4 import BeautifulSoup

from .base import Scraper


class ShambalaScraper(Scraper):
    name = "Shambala"
    base_url = "https://shambala.com.ua"
    requires_js = False

    def search_url(self, query: str) -> str:
        q = urllib.parse.quote(query)
        return f"{self.base_url}/search/?q={q}"

    def parse_search(self, soup: BeautifulSoup) -> str | None:
        # ПЕРЕВІРИТИ: контейнер картки товару в результатах пошуку.
        first = soup.select_one("a.product-card__link, .product-thumb a, .catalog-item a")
        return first.get("href") if first else None

    def parse_price(self, soup: BeautifulSoup) -> float | None:
        # ПЕРЕВІРИТИ: елемент ціни на сторінці товару.
        el = soup.select_one(".product-price, .price-new, [itemprop='price']")
        if el is None:
            return None
        # часто ціна лежить в атрибуті content (microdata)
        return self.clean_price(el.get("content") or el.get_text())
