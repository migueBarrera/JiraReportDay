import streamlit as st
import pandas as pd
import jira_report


def fetch_all_worklogs(client, project_key: str, author_list: list[str], days: int, date_start: str = None, date_end: str = None) -> list[dict]:
    """
    Obtiene los worklogs de Jira para una lista de usuarios,
    mostrando progreso en Streamlit.
    Retorna una lista de diccionarios con los worklogs.
    """
    all_worklogs = []
    progress_bar = st.progress(0, text="Iniciando búsqueda...")

    for idx, author_name in enumerate(author_list):
        progress_bar.progress(
            idx / len(author_list),
            text=f"Buscando worklogs de '{author_name}' ({idx + 1}/{len(author_list)})...",
        )
        worklogs_data = jira_report.get_worklogs_filtered(
            client,
            project_key=project_key,
            author_name=author_name,
            days=days,
            date_start=date_start,
            date_end=date_end,
        )
        for w in worklogs_data:
            w["usuario"] = author_name
        all_worklogs.extend(worklogs_data)

    progress_bar.progress(1.0, text="Completado.")
    return all_worklogs


def build_dataframe(worklogs: list[dict]) -> pd.DataFrame:
    """Convierte la lista de worklogs en un DataFrame limpio y ordenado."""
    df = pd.DataFrame(worklogs)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["usuario", "date", "key"], ascending=[True, False, False])
    return df
