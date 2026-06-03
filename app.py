from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.analysis import generate_manager_analysis
from src.config import settings
from src.extraction import extract_requirements
from src.filtering import filter_and_rank_cars
from src.storage import REQUIRED_COLUMNS, load_cars_csv, save_lead
from src.utils import build_download_markdown, format_rub


DEMO_DATASETS = {
    "Demo база: 35 авто": Path("data/sample_cars.csv"),
    "Тестовая база: 30 авто": Path("data/test_cars_30.csv"),
}

DEMO_REQUESTS = [
    "Хочу премиальный кроссовер до 8 млн, можно из Кореи или Европы, важны комфорт и ликвидность. Китай пока не рассматриваю.",
    "Нужен большой семейный автомобиль до 7 млн, желательно свежий, с богатой комплектацией и без лишних рисков.",
    "Хочу статусный седан до 10 млн, чтобы выглядел дорого и был комфортным для поездок по городу.",
]


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg: #eef1f5;
                --surface: #ffffff;
                --surface-soft: #f7f8fa;
                --ink: #171b22;
                --muted: #667085;
                --line: #d7dce3;
                --red: #c92828;
                --red-dark: #9f2020;
                --red-soft: #fff2f2;
                --green: #157347;
                --blue: #2457a6;
            }

            .stApp {
                background: var(--bg);
            }

            .block-container {
                max-width: 1260px;
                padding: 22px 34px 54px;
            }

            html, body, p, li, label, button, input, textarea {
                font-family: Arial, "Helvetica Neue", sans-serif;
                letter-spacing: 0;
            }

            h1, h2, h3 {
                color: var(--ink) !important;
                letter-spacing: 0 !important;
            }

            h1 {
                font-size: 32px !important;
                line-height: 1.12 !important;
                font-weight: 800 !important;
                margin: 0 0 10px !important;
            }

            h2 {
                font-size: 22px !important;
                line-height: 1.25 !important;
                font-weight: 800 !important;
            }

            h3 {
                font-size: 17px !important;
                line-height: 1.3 !important;
                font-weight: 750 !important;
            }

            .app-hero {
                background: var(--surface);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 22px 24px 18px;
                margin-bottom: 16px;
                box-shadow: 0 8px 24px rgba(16, 24, 40, 0.06);
            }

            .hero-grid {
                display: grid;
                grid-template-columns: minmax(0, 1fr) 280px;
                gap: 22px;
                align-items: start;
            }

            .eyebrow {
                display: inline-block;
                color: var(--red);
                font-size: 12px;
                font-weight: 800;
                text-transform: uppercase;
                margin-bottom: 8px;
            }

            .hero-copy {
                color: var(--muted);
                font-size: 16px;
                line-height: 1.5;
                max-width: 760px;
                margin: 0;
            }

            .hero-panel {
                background: #fbfcfd;
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 14px;
            }

            .hero-panel-title {
                color: var(--ink);
                font-size: 14px;
                font-weight: 800;
                margin-bottom: 8px;
            }

            .hero-panel-text {
                color: var(--muted);
                font-size: 13px;
                line-height: 1.4;
            }

            .step-row {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 10px;
                margin-top: 18px;
                padding-top: 16px;
                border-top: 1px solid var(--line);
            }

            .step-card {
                background: var(--surface-soft);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 12px 14px;
                min-height: 78px;
            }

            .step-num {
                color: var(--red);
                font-size: 12px;
                font-weight: 800;
                margin-bottom: 5px;
            }

            .step-title {
                color: var(--ink);
                font-size: 15px;
                font-weight: 800;
                margin-bottom: 3px;
            }

            .step-text {
                color: var(--muted);
                font-size: 13px;
                line-height: 1.35;
            }

            .section-title {
                color: var(--ink);
                font-size: 20px;
                font-weight: 800;
                margin: 0 0 4px;
            }

            .section-subtitle {
                color: var(--muted);
                font-size: 14px;
                margin: 0 0 14px;
            }

            .metric-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 10px;
                margin: 8px 0 12px;
            }

            .metric-box {
                background: var(--surface);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 13px 14px;
                min-height: 86px;
            }

            .metric-label {
                color: var(--muted);
                font-size: 12px;
                font-weight: 800;
                text-transform: uppercase;
                margin-bottom: 8px;
            }

            .metric-value {
                color: var(--ink);
                font-size: 20px;
                line-height: 1.15;
                font-weight: 850;
            }

            .chip-row {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin: 10px 0 0;
            }

            .chip {
                display: inline-flex;
                align-items: center;
                background: #fff;
                border: 1px solid var(--line);
                border-radius: 999px;
                color: #344054;
                font-size: 13px;
                font-weight: 650;
                padding: 6px 10px;
            }

            .chip-red {
                background: var(--red-soft);
                border-color: #f0b7b7;
                color: var(--red-dark);
            }

            .car-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 12px;
                margin: 10px 0 18px;
            }

            .car-card {
                background: var(--surface);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 15px;
                min-height: 194px;
                box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
            }

            .car-title {
                color: var(--ink);
                font-size: 18px;
                font-weight: 850;
                line-height: 1.25;
                margin-bottom: 5px;
            }

            .car-meta {
                color: var(--muted);
                font-size: 13px;
                margin-bottom: 11px;
            }

            .car-price {
                color: var(--red);
                font-size: 21px;
                font-weight: 850;
                margin-bottom: 11px;
            }

            .car-price-large {
                color: var(--red);
                font-size: 30px;
                line-height: 1.1;
                font-weight: 900;
                margin: 14px 0 18px;
                white-space: nowrap;
            }

            .car-facts {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 6px 10px;
                color: #344054;
                font-size: 13px;
            }

            .score-pill {
                display: inline-block;
                color: var(--green);
                background: #ecfdf3;
                border: 1px solid #b7ebce;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 800;
                padding: 4px 8px;
                margin-top: 12px;
            }

            .empty-state {
                background: #fff;
                border: 1px dashed #c2c8d0;
                border-radius: 8px;
                color: var(--muted);
                padding: 18px;
                font-size: 14px;
            }

            div[data-testid="stVerticalBlockBorderWrapper"] > div {
                background: var(--surface);
                border-color: var(--line) !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 14px rgba(16, 24, 40, 0.04);
            }

            [data-testid="stWidgetLabel"] p,
            [data-testid="stMarkdownContainer"] p,
            [data-testid="stFileUploader"] p {
                color: var(--ink);
            }

            textarea,
            input {
                background: #ffffff !important;
                color: var(--ink) !important;
                border-color: #bfc7d2 !important;
                border-radius: 7px !important;
            }

            textarea::placeholder,
            input::placeholder {
                color: #8a94a3 !important;
                opacity: 1 !important;
            }

            .stButton > button,
            .stDownloadButton > button {
                border-radius: 7px !important;
                min-height: 44px;
                font-weight: 800;
            }

            .stButton > button[kind="primary"] {
                background: var(--red) !important;
                border-color: var(--red) !important;
                color: #ffffff !important;
            }

            .stButton > button[kind="primary"]:hover {
                background: var(--red-dark) !important;
                border-color: var(--red-dark) !important;
            }

            [data-testid="stSidebar"] {
                background: #11151b;
                border-right: 1px solid #2a3038;
            }

            [data-testid="stSidebar"] h3,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] p {
                color: #f4f6f8 !important;
            }

            [data-testid="stSidebar"] div[data-baseweb="select"] > div,
            [data-testid="stSidebar"] input {
                background: #171c24 !important;
                border-color: #303844 !important;
                color: #f4f6f8 !important;
            }

            [data-testid="stSidebar"] .stButton > button {
                background: #f4f6f8 !important;
                color: #11151b !important;
                border-color: #f4f6f8 !important;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid var(--line);
                border-radius: 8px;
                overflow: hidden;
            }

            @media (max-width: 920px) {
                .hero-grid,
                .step-row,
                .metric-grid,
                .car-grid {
                    grid-template-columns: 1fr;
                }

                .block-container {
                    padding-left: 18px;
                    padding-right: 18px;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _read_uploaded_or_demo(uploaded_file, dataset_path: Path, use_demo: bool) -> pd.DataFrame:
    if uploaded_file is not None:
        return load_cars_csv(uploaded_file)
    if use_demo:
        return load_cars_csv(dataset_path)
    raise ValueError("Загрузите CSV или включите demo CSV в боковой панели.")


def _translate_country(value: object) -> str:
    mapping = {
        "korea": "Корея",
        "china": "Китай",
        "europe": "Европа",
        "japan": "Япония",
    }
    return mapping.get(str(value).strip().lower(), str(value))


def _translate_body_type(value: object) -> str:
    mapping = {
        "suv": "кроссовер",
        "sedan": "седан",
        "minivan": "минивэн",
        "wagon": "универсал",
        "liftback": "лифтбек",
    }
    return mapping.get(str(value).strip().lower(), str(value))


def _translate_priority(value: object) -> str:
    mapping = {
        "comfort": "комфорт",
        "liquidity": "ликвидность",
        "reliability": "надежность",
        "status": "статус",
        "dynamics": "динамика",
        "family": "семейный формат",
        "low_risk": "низкий риск",
        "equipment": "комплектация",
    }
    return mapping.get(str(value).strip().lower(), str(value))


def _apply_demo_request() -> None:
    demo_request = st.session_state.get("demo_request", "")
    if demo_request:
        st.session_state["client_request"] = demo_request


def _render_sidebar() -> tuple[bool, Path, str, int, str]:
    with st.sidebar:
        st.markdown("### Параметры")
        model = st.selectbox(
            "Модель Groq",
            options=[settings.groq_model_main, settings.groq_model_fast],
            index=0,
        )
        top_n = st.slider("Количество вариантов", min_value=3, max_value=7, value=5)
        use_demo_csv = st.toggle("Использовать demo CSV", value=True)
        dataset_label = st.selectbox("Demo база", options=list(DEMO_DATASETS.keys()), index=0)
        dataset_path = DEMO_DATASETS[dataset_label]
        st.divider()
        st.selectbox(
            "Готовый запрос",
            options=[""] + DEMO_REQUESTS,
            key="demo_request",
            on_change=_apply_demo_request,
        )

    return use_demo_csv, dataset_path, dataset_label, top_n, model


def _render_header(dataset_label: str, top_n: int) -> None:
    st.markdown(
        f"""
        <div class="app-hero">
            <div class="hero-grid">
                <div>
                    <span class="eyebrow">Каталог и AI-подбор</span>
                    <h1>Auto Import AI Assistant</h1>
                    <p class="hero-copy">
                        Рабочее место менеджера: принять запрос клиента, выбрать CSV-базу,
                        отфильтровать предложения и подготовить понятный ответ для Telegram.
                    </p>
                    <div class="chip-row">
                        <span class="chip chip-red">Факты берет из CSV</span>
                        <span class="chip">Бюджет считает Python</span>
                        <span class="chip">LLM пишет резюме</span>
                    </div>
                </div>
                <div class="hero-panel">
                    <div class="hero-panel-title">Текущая сессия</div>
                    <div class="hero-panel-text">{dataset_label}<br>Показываем top {top_n} вариантов</div>
                </div>
            </div>
            <div class="step-row">
                <div class="step-card">
                    <div class="step-num">01</div>
                    <div class="step-title">Запрос клиента</div>
                    <div class="step-text">Свободный текст: бюджет, страна, кузов, приоритеты.</div>
                </div>
                <div class="step-card">
                    <div class="step-num">02</div>
                    <div class="step-title">CSV с авто</div>
                    <div class="step-text">Demo-база или файл менеджера с актуальными предложениями.</div>
                </div>
                <div class="step-card">
                    <div class="step-num">03</div>
                    <div class="step-title">Подбор и ответ</div>
                    <div class="step-text">Таблица, короткий лист, риски и сообщение клиенту.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_input_form() -> tuple[str, object, bool]:
    with st.container(border=True):
        st.markdown('<div class="section-title">Входящие данные</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Заполните запрос и выберите источник предложений. Demo CSV можно оставить включенным.</div>',
            unsafe_allow_html=True,
        )
        left, right = st.columns([1.45, 1], gap="large")
        with left:
            client_request = st.text_area(
                "Запрос клиента",
                key="client_request",
                height=154,
                placeholder="Например: нужен семейный SUV до 8 млн, свежий, с хорошей ликвидностью...",
            )
        with right:
            uploaded_file = st.file_uploader("CSV с автомобилями", type=["csv"])
            with st.expander("Формат CSV", expanded=False):
                st.code(",".join(REQUIRED_COLUMNS), language="csv")

        analyze = st.button("Проанализировать запрос", type="primary", use_container_width=True)

    return client_request, uploaded_file, analyze


def _render_requirements(requirements) -> None:
    countries = ", ".join(_translate_country(country) for country in requirements.countries) if requirements.countries else "не указаны"
    priorities = ", ".join(_translate_priority(priority) for priority in requirements.priorities) if requirements.priorities else "не указаны"
    mileage = f"{requirements.max_mileage_km:,} км".replace(",", " ") if requirements.max_mileage_km else "не указан"
    year = str(requirements.min_year) if requirements.min_year else "не указан"
    body_type = _translate_body_type(requirements.body_type) if requirements.body_type else "не указан"

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-label">Бюджет</div>
                <div class="metric-value">{format_rub(requirements.budget_rub)}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Кузов</div>
                <div class="metric-value">{body_type}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Год от</div>
                <div class="metric-value">{year}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Пробег до</div>
                <div class="metric-value">{mileage}</div>
            </div>
        </div>
        <div class="chip-row">
            <span class="chip">Страны: {countries}</span>
            <span class="chip">Приоритеты: {priorities}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_car_cards(ranked_cars: pd.DataFrame) -> None:
    if ranked_cars.empty:
        st.markdown(
            '<div class="empty-state">Подходящих автомобилей не найдено. Расширьте бюджет или ослабьте ограничения.</div>',
            unsafe_allow_html=True,
        )
        return

    top_rows = ranked_cars.to_dict(orient="records")
    cards_per_row = 3
    for start in range(0, len(top_rows), cards_per_row):
        row_chunk = top_rows[start : start + cards_per_row]
        columns = st.columns(cards_per_row, gap="large")
        for column, car in zip(columns, row_chunk, strict=False):
            price = format_rub(int(car["total_price_rub"]))
            mileage = f"{int(car['mileage_km']):,} км".replace(",", " ")
            country = _translate_country(car["country"])
            body_type = _translate_body_type(car["body_type"])
            with column:
                with st.container(border=True):
                    st.markdown(f"### {car['brand']} {car['model']}")
                    st.caption(f"{country} · {body_type} · {car['year']}")
                    st.markdown(f'<div class="car-price-large">{price}</div>', unsafe_allow_html=True)
                    st.write(f"Пробег: {mileage}")
                    st.write(f"Привод: {car['drivetrain']}")
                    st.write(f"Комфорт: {car['comfort']}/5")
                    st.write(f"Ликвидность: {car['liquidity']}/5")
        if len(row_chunk) < cards_per_row:
            for column in columns[len(row_chunk) :]:
                with column:
                    st.empty()


def _render_waiting_state() -> None:
    with st.container(border=True):
        st.markdown('<div class="section-title">Готово к работе</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="empty-state">Выберите demo-запрос в боковой панели или введите свой текст, затем нажмите кнопку анализа.</div>',
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="Auto Import AI Assistant",
        page_icon="🚗",
        layout="wide",
    )
    _inject_styles()

    use_demo_csv, dataset_path, dataset_label, top_n, model = _render_sidebar()
    _render_header(dataset_label if use_demo_csv else "Пользовательский CSV", top_n)
    client_request, uploaded_file, analyze = _render_input_form()

    if not analyze:
        _render_waiting_state()
        return

    if not client_request.strip():
        st.error("Введите текст запроса клиента.")
        return

    try:
        cars_df = _read_uploaded_or_demo(uploaded_file, dataset_path, use_demo_csv)
    except Exception as exc:
        st.error(str(exc))
        return

    try:
        with st.spinner("Извлекаю требования из текста клиента..."):
            requirements = extract_requirements(client_request, model=model)

        with st.spinner("Фильтрую и ранжирую автомобили Python-кодом..."):
            ranked_cars = filter_and_rank_cars(cars_df, requirements).head(top_n)

        with st.spinner("Готовлю менеджерский AI-анализ..."):
            analysis_md = generate_manager_analysis(
                client_request=client_request,
                requirements=requirements,
                top_cars=ranked_cars,
                model=model,
            )

        save_lead(client_request, requirements, ranked_cars)
    except Exception as exc:
        st.error(f"Не удалось обработать запрос: {exc}")
        return

    cars_tab, analysis_tab = st.tabs(["Подбор авто", "AI-анализ"])

    with cars_tab:
        with st.container(border=True):
            st.markdown('<div class="section-title">Подходящие автомобили</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="section-subtitle">Показано вариантов: {len(ranked_cars)}. Количество меняется слайдером в боковой панели.</div>',
                unsafe_allow_html=True,
            )
            _render_car_cards(ranked_cars)

    with analysis_tab:
        with st.container(border=True):
            st.markdown('<div class="section-title">AI-анализ менеджеру</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-subtitle">Извлеченные требования включены сюда как контекст для менеджера.</div>',
                unsafe_allow_html=True,
            )
            _render_requirements(requirements)
            st.divider()
            st.markdown(analysis_md)
            download_md = build_download_markdown(client_request, requirements, ranked_cars, analysis_md)
            st.download_button(
                "Скачать результат в Markdown",
                data=download_md,
                file_name="auto_import_analysis.md",
                mime="text/markdown",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()
