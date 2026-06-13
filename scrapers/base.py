"""
Базовий клас для всіх скрейперів конкурентів.

Кожен конкурент = окремий підклас, який реалізує:
  - search_url(query)        -> URL сторінки результатів пошуку
  - parse_search(html)       -> URL першого товару (або None)
  - parse_price(html)        -> ціна як float (або None)

Решта (HTTP-запити, ввічливі затримки, robots.txt, нормалізація ціни)
живе тут і не дублюється між конкурентами.
"""

from __future__ import annotations

import logging
import re
import time
import urllib.parse
import urllib.robotparser
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Чесний User-Agent: ми не маскуємось під Googlebot чи реальний браузер.
# (Якщо сайт повертає 403 — це сигнал, що нас не хочуть. Поважаємо.)
USER_AGENT = "GorganyPriceMonitor/0.1 (educational portfolio project)"

REQUEST_TIMEOUT = 15      # сек на запит
POLITE_DELAY = 1.5        # сек між запитами до одного сайту


@dataclass
class ScrapeResult:
    """Результат для одного конкурента."""
    competitor: str
    price: float | None
    url: str | None
    status: str            # "ok" | "not_found" | "blocked" | "error"
    note: str = ""


class Scraper(ABC):
    # Перевизначається в підкласах:
    name: str = "Base"
    base_url: str = ""
    # True -> ціна рендериться через JS, requests/BS4 не вистачить (треба Playwright).
    requires_js: bool = False

    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._robots: urllib.robotparser.RobotFileParser | None = None

    # ---- методи, які РЕАЛІЗУЄ кожен конкурент --------------------------------

    @abstractmethod
    def search_url(self, query: str) -> str:
        """URL сторінки результатів пошуку для запиту."""

    @abstractmethod
    def parse_search(self, soup: BeautifulSoup) -> str | None:
        """Витягнути URL першого релевантного товару зі сторінки пошуку."""

    @abstractmethod
    def parse_price(self, soup: BeautifulSoup) -> float | None:
        """Витягнути ціну зі сторінки товару."""

    # ---- спільна логіка ------------------------------------------------------

    def run(self, query: str) -> ScrapeResult:
        """Повний цикл: пошук -> сторінка товару -> ціна. Ніколи не кидає виняток."""
        if self.requires_js:
            return ScrapeResult(
                self.name, None, None, "error",
                "Потребує JS-рендеру (Playwright). requests/BS4 не дістане ціну.",
            )
        try:
            if not self._allowed(self.search_url(query)):
                return ScrapeResult(self.name, None, None, "blocked",
                                    "Заборонено в robots.txt")

            search_soup = self._get(self.search_url(query))
            if search_soup is None:
                return ScrapeResult(self.name, None, None, "blocked",
                                    "Сторінку пошуку не вдалось завантажити")

            product_url = self.parse_search(search_soup)
            if not product_url:
                return ScrapeResult(self.name, None, None, "not_found",
                                    "Товар у результатах пошуку не знайдено")

            product_url = urllib.parse.urljoin(self.base_url, product_url)

            if not self._allowed(product_url):
                return ScrapeResult(self.name, None, product_url, "blocked",
                                    "Сторінка товару заборонена в robots.txt")

            product_soup = self._get(product_url)
            if product_soup is None:
                return ScrapeResult(self.name, None, product_url, "blocked",
                                    "Сторінку товару не вдалось завантажити")

            price = self.parse_price(product_soup)
            if price is None:
                return ScrapeResult(self.name, None, product_url, "error",
                                    "Знайшов товар, але не зміг розпарсити ціну")

            return ScrapeResult(self.name, price, product_url, "ok")

        except Exception as exc:  # навмисно широко: один впалий сайт не валить решту
            logger.exception("Помилка скрейпера %s", self.name)
            return ScrapeResult(self.name, None, None, "error", str(exc)[:200])

    def _get(self, url: str) -> BeautifulSoup | None:
        """Ввічливий GET з затримкою. Повертає soup або None (за блокування/помилки)."""
        time.sleep(POLITE_DELAY)
        resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 403 or resp.status_code == 429:
            logger.warning("%s повернув %s для %s", self.name, resp.status_code, url)
            return None
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def _allowed(self, url: str) -> bool:
        """Перевірка robots.txt для нашого User-Agent."""
        if self._robots is None:
            self._robots = urllib.robotparser.RobotFileParser()
            robots_url = urllib.parse.urljoin(self.base_url, "/robots.txt")
            try:
                self._robots.set_url(robots_url)
                self._robots.read()
            except Exception:
                # Немає robots.txt або не прочитався -> не блокуємо, але логуємо.
                logger.info("robots.txt недоступний для %s", self.name)
                return True
        return self._robots.can_fetch(USER_AGENT, url)

    @staticmethod
    def clean_price(text: str | None) -> float | None:
        """'13 500 ₴' / '2\u00a0365 грн' / '1 205.00' -> 1205.0. Повертає None, якщо не вийшло."""
        if not text:
            return None
        # лишаємо тільки цифри, кому/крапку
        cleaned = re.sub(r"[^\d.,]", "", text.replace("\u00a0", "").replace(" ", ""))
        if not cleaned:
            return None
        # 1.234,56 (євроформат) або 1,234.56 — нормалізуємо до крапки
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            cleaned = cleaned.replace(",", ".")
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return None
