# 🏔️ Gorgany Price Monitor

Інструмент моніторингу цін конкурентів. Вводиш бренд + модель товару у форму —
застосунок паралельно опитує сайти конкурентів, витягує ціну і посилання,
та зберігає історію в Excel.

> **Освітній проєкт для портфоліо.** Користувач відповідає за дотримання
> Terms of Service сайтів та чинного законодавства. Зібрані дані не публікуються.

## Що це робить

1. Вводиш пошуковий запит (напр. `Turbat Shanta Pro 2`)
2. Скрейпери конкурентів паралельно шукають товар і витягують ціну
3. Результат показується таблицею і дописується рядком у `data/price_history.xlsx`
   (кожен запуск = новий рядок з датою → накопичується історія цін)

Поточні конкуренти: **Епіцентр, Rozetka, Shambala**.

## Стек

Python · Streamlit · requests · BeautifulSoup · openpyxl · ThreadPoolExecutor

## Запуск локально

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# пароль для входу:
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
#   відредагуй app_password у secrets.toml

streamlit run app.py
```

## ⚠️ Перед першим робочим запуском: перевір селектори

Селектори в `scrapers/*.py` позначені коментарем `ПЕРЕВІРИТИ` — це плейсхолдери.
Кожен сайт має свою верстку, тож їх треба підставити під реальний DOM:

1. Відкрий сайт конкурента, знайди будь-який товар
2. Правий клік на ціні → **Inspect / Перевірити**
3. Подивись на клас/тег елемента з ціною → встав у `parse_price`
4. Зроби пошук на сайті → Inspect на картці першого товару → встав у `parse_search`
5. Перевір окремо:
   ```python
   from scrapers.shambala import ShambalaScraper
   print(ShambalaScraper().run("Turbat Shanta 2"))
   ```

### Rozetka та Епіцентр потребують JS

Обидва — важкі SPA: ціна рендериться JavaScript-ом, тож `requests` дістає
порожній HTML. Тому в коді вони позначені `requires_js = True` і поки що
повертають статус `error` (чесно, без вигаданих цін).

Щоб увімкнути — встанови Playwright і перевизнач завантаження сторінки через
headless-браузер, тоді постав `requires_js = False`:

```bash
pip install playwright && playwright install chromium
```

**Shambala** — менший сайт на CMS, для нього `requests`/BS4 має вистачити
без Playwright. Тому почни з нього — найшвидший шлях до першої реальної ціни.

## Додати нового конкурента

1. Створи `scrapers/<name>.py` з підкласом `Scraper`
   (реалізуй `search_url`, `parse_search`, `parse_price`)
2. Додай клас у `ACTIVE_SCRAPERS` у `scrapers/__init__.py`

Колонки Excel та таблиця в UI оновляться автоматично.

## Деплой на Streamlit Community Cloud (безкоштовно)

1. Залий репозиторій на GitHub (приватний або публічний)
2. На [share.streamlit.io](https://share.streamlit.io) підключи репо → деплой автоматичний
3. Пароль додай через **Settings → Secrets** (вставити вміст `secrets.toml`)
4. Для приватного доступу — зроби застосунок private і додай дозволені email

## Етична поведінка скрейпера

Вшито в `base.py`: чесний User-Agent, перевірка `robots.txt`, затримка 1.5 с
між запитами, акуратна обробка 403/429 (не обходимо блокування). Якщо сайт
явно блокує — поважаємо це.

## Roadmap (свідомо відкладено)

- [ ] Playwright для Rozetka / Епіцентр
- [ ] Решта 12 конкурентів з майстер-файлу
- [ ] Аналітичний шар: gap до РРЦ, динаміка цін, де ми дорожчі/дешевші
- [ ] БД замість Excel (коли знадобиться історія в часі)
- [ ] Розклад (моніторинг 24/7)
