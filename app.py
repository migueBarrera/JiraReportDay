import os
import streamlit as st
import calendar
from datetime import datetime, date
from dotenv import load_dotenv
import jira_report
import data_loader
import report_sections

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="Reporte de Horas Jira",
    page_icon="⏱️",
    layout="wide"
)

st.title("⏱️ Reporte de Horas Jira")

# Sidebar para configuración
with st.sidebar:
    st.header("Configuración")
    
    jira_url = st.text_input("Jira URL", value=os.getenv("JIRA_URL", ""), placeholder="https://tu-jira.example.com")
    jira_token = st.text_input("Personal Access Token", value="", type="password", help="Tu Token Personal (PAT).")
    
    st.markdown("---")
    st.subheader("Filtros")
    project_key = st.text_input("Clave Proyecto", value=os.getenv("JIRA_PROJECT", ""), help="Ej: MOV, PROJ")
    
    default_users = os.getenv("JIRA_USER", "")
    authors_input = st.text_area(
        "Usuarios (uno por línea)",
        value=default_users,
        height=120,
        help="Introduce los nombres de usuario de Jira, uno por línea (ej. ANBORARI, JLOPEZ)"
    )
    
    # Selector de periodo
    period_mode = st.radio("Periodo", ["Días", "Mes"], horizontal=True)
    date_start = None
    date_end = None
    if period_mode == "Días":
        days = st.slider("Días a analizar", min_value=1, max_value=90, value=30)
    else:
        today = date.today()
        months = []
        for i in range(12):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            month_date = date(y, m, 1)
            months.append(month_date)
        month_labels = {d.strftime("%B %Y").capitalize(): d for d in months}
        selected_label = st.selectbox("Mes a analizar", list(month_labels.keys()))
        selected_month = month_labels[selected_label]
        last_day = calendar.monthrange(selected_month.year, selected_month.month)[1]
        date_start = selected_month.strftime("%Y-%m-%d")
        date_end = date(selected_month.year, selected_month.month, last_day).strftime("%Y-%m-%d")
        # days se usa para mostrar el rango real del mes
        days = last_day
    
    st.markdown("---")
    st.caption("v1.1.0")

# Parsear lista de usuarios
author_list = [a.strip() for a in authors_input.splitlines() if a.strip()] if authors_input else []

if st.button("Generar Reporte", type="primary"):
    if not jira_url or not jira_token or not project_key or not author_list:
        st.error("Faltan datos. URL, Token, Proyecto y al menos un Usuario son obligatorios.")
    else:
        try:
            client = jira_report.JiraAPIClient(url=jira_url, token=jira_token)
            
            # Cargar datos
            all_worklogs = data_loader.fetch_all_worklogs(
                client, project_key, author_list, days,
                date_start=date_start, date_end=date_end
            )
            
            if not all_worklogs:
                st.warning("No se encontraron horas registradas en el periodo seleccionado para los usuarios indicados.")
            else:
                df = data_loader.build_dataframe(all_worklogs)
                
                # Renderizar secciones
                report_sections.render_global_metrics(df)
                report_sections.render_user_summary(df)
                report_sections.render_daily_charts(df, days)
                report_sections.render_detail_tables(df, jira_url)
                    
        except Exception as e:
            err_msg = str(e)
            if "401" in err_msg:
                st.error("Error de Autenticación (401). Verifica tu Token. El token puede haber expirado.")
            elif "404" in err_msg:
                st.error("Error 404. URL no encontrada.")
            else:
                st.error(f"Error: {err_msg}")
