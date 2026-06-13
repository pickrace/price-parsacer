"""
Streamlit UI для моніторингу цін конкурентів Gorgany.

Запуск локально:   streamlit run app.py
Авторизація:       простий пароль зі st.secrets (див. .streamlit/secrets.toml.example)

Для MVP свідомо НЕ робимо: БД, розклад, складну аналітику. Тільки:
ввід запиту -> паралельний скрейпінг -> таблиця -> збереження в Excel.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from scrapers import scrape_all
from storage import DATA_FILE, append_results

st.set_page_config(page_title="Gorgany Price Monitor", page_icon="🏔️")

# ---- проста авторизація --------------------------------------------------
# Один спільний пароль на застосунок. Для портфоліо достатньо; якщо захочеш
# кілька користувачів з логами — заміни на streamlit-authenticator (див. README).
def _check_auth() -> bool:
    if st.session_state.get("authed"):
        return True
    pwd = st.text_input("Пароль", type="password")
    if not pwd:
        st.stop()
    if pwd == st.secrets.get("app_password"):
        st.session_state["authed"] = True
        return True
    st.error("Невірний пароль")
    st.stop()


_check_auth()

# ---- інтерфейс -----------------------------------------------------------
st.title("🏔️ Моніторинг цін конкурентів")
st.caption("Введи бренд + модель так, як шукав би на сайті (напр. «Turbat Shanta 2»).")

col1, col2 = st.columns([3, 1])
query = col1.text_input("Пошуковий запит", placeholder="Turbat Shanta Pro 2")
brand = col2.text_input("Бренд (опц.)", placeholder="Turbat")

if st.button("🔍 Шукати", type="primary", disabled=not query.strip()):
    with st.spinner("Опитую конкурентів..."):
        results = scrape_all(query.strip())

    # таблиця результатів
    rows = []
    for r in results:
        rows.append({
            "Конкурент": r.competitor,
            "Ціна": r.price if r.status == "ok" else "—",
            "Статус": {"ok": "✅", "not_found": "🔍 не знайдено",
                       "blocked": "🚫 блок", "error": "⚠️ помилка"}.get(r.status, r.status),
            "Посилання": r.url or "",
            "Деталі": r.note,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # збереження в історію
    path = append_results(query.strip(), brand.strip(), results)
    st.success(f"Збережено в історію: {path.name}")

# ---- завантаження історії ------------------------------------------------
if DATA_FILE.exists():
    with open(DATA_FILE, "rb") as f:
        st.download_button(
            "⬇️ Завантажити історію (Excel)",
            f,
            file_name="price_history.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
