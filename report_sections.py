import streamlit as st
import pandas as pd
import charts


def render_global_metrics(df: pd.DataFrame):
    """Muestra las métricas globales: total horas, usuarios y promedio."""
    total_hours = df["hours"].sum()
    num_users = df["usuario"].nunique()

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Horas", f"{total_hours:.2f} h")
    col_m2.metric("Usuarios", num_users)
    col_m3.metric("Promedio p/usuario", f"{total_hours / num_users:.2f} h")


def render_user_summary(df: pd.DataFrame):
    """Muestra gráficos de resumen por usuario (torta + barras)."""
    st.subheader("Resumen por Usuario")
    df_summary = df.groupby("usuario")["hours"].sum().reset_index()
    df_summary.columns = ["Usuario", "Horas"]
    df_summary = df_summary.sort_values("Horas", ascending=False)

    charts.setup_theme()

    col1, col2 = st.columns(2)
    with col1:
        charts.render_pie_chart(df_summary)
    with col2:
        charts.render_bar_chart(df_summary)


def render_daily_charts(df: pd.DataFrame, days: int):
    """Muestra el gráfico diario con pestañas por usuario."""
    st.subheader("Gráfico Diario")
    user_names = sorted(df["usuario"].unique().tolist())
    tabs = st.tabs(user_names)

    df_daily = df.groupby(["date", "usuario"])["hours"].sum().reset_index()

    for i, user_name in enumerate(user_names):
        with tabs[i]:
            df_user = df_daily[df_daily["usuario"] == user_name]
            charts.render_daily_chart(
                df_user, f"Horas por día - {user_name} (Últimos {days} días)"
            )


def render_detail_tables(df: pd.DataFrame, jira_url: str):
    """Muestra tablas de detalle de tareas con pestañas por usuario."""
    st.subheader("Detalle de Tareas")
    user_names = sorted(df["usuario"].unique().tolist())
    tabs = st.tabs(user_names)

    base = jira_url.rstrip("/")

    for i, user_name in enumerate(user_names):
        with tabs[i]:
            df_user = df[df["usuario"] == user_name]
            user_hours = df_user["hours"].sum()
            st.metric("Horas", f"{user_hours:.2f} h")
            _render_single_table(df_user, base)


def _render_single_table(dataframe: pd.DataFrame, jira_base_url: str):
    """Renderiza una tabla de detalle individual."""
    df_disp = dataframe.copy()
    df_disp["Fecha"] = df_disp["date"].dt.strftime("%Y-%m-%d")
    df_disp["url"] = df_disp["key"].apply(lambda k: f"{jira_base_url}/browse/{k}")
    df_disp = df_disp[["Fecha", "key", "url", "type", "summary", "hours"]]
    df_disp.columns = ["Fecha", "Clave", "Enlace", "Tipo", "Título", "Horas"]
    st.dataframe(
        df_disp,
        hide_index=True,
        width="stretch",
        column_config={
            "Enlace": st.column_config.LinkColumn(display_text="Abrir ↗"),
            "Horas": st.column_config.NumberColumn(format="%.2f h"),
        },
    )
