"""
Реєстр активних скрейперів + паралельний запуск.

Щоб додати конкурента: напиши клас-підклас Scraper в окремому файлі
і додай його в ACTIVE_SCRAPERS. Більше нічого міняти не треба.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .base import ScrapeResult, Scraper
from .epicentr import EpicentrScraper
from .rozetka import RozetkaScraper
from .shambala import ShambalaScraper

# Порядок тут = порядок колонок у результаті.
ACTIVE_SCRAPERS: list[type[Scraper]] = [
    EpicentrScraper,
    RozetkaScraper,
    ShambalaScraper,
]


def scrape_all(query: str) -> list[ScrapeResult]:
    """Запускає всі активні скрейпери паралельно для одного запиту."""
    scrapers = [cls() for cls in ACTIVE_SCRAPERS]
    with ThreadPoolExecutor(max_workers=len(scrapers)) as pool:
        results = list(pool.map(lambda s: s.run(query), scrapers))
    # зберегти порядок ACTIVE_SCRAPERS
    by_name = {r.competitor: r for r in results}
    return [by_name[s.name] for s in scrapers]


__all__ = ["scrape_all", "ScrapeResult", "ACTIVE_SCRAPERS"]
