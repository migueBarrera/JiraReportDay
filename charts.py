import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd


def setup_theme():
    """Configura el tema global de seaborn."""
    sns.set_theme(style="whitegrid", palette="muted")


def render_pie_chart(df_user_summary: pd.DataFrame):
    """Gráfico de torta con distribución de horas por usuario."""
    fig, ax = plt.subplots(figsize=(2.5, 2))
    colors = sns.color_palette("pastel", len(df_user_summary))
    ax.pie(
        df_user_summary['Horas'], labels=df_user_summary['Usuario'],
        autopct='%1.1f%%', colors=colors, startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1},
        textprops={'fontsize': 6}
    )
    ax.set_title("Distribución de Horas", fontsize=7, fontweight='bold')
    fig.tight_layout(pad=0.3)
    st.pyplot(fig, use_container_width=False)
    plt.close(fig)


def render_bar_chart(df_user_summary: pd.DataFrame):
    """Gráfico de barras con total de horas por usuario."""
    fig, ax = plt.subplots(figsize=(2.5, 2))
    sns.barplot(
        data=df_user_summary, x='Usuario', y='Horas',
        hue='Usuario', palette="deep", ax=ax, legend=False
    )
    ax.set_title("Total Horas por Usuario", fontsize=7, fontweight='bold')
    ax.set_ylabel("Horas", fontsize=6)
    ax.set_xlabel("")
    ax.tick_params(labelsize=6)
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f', fontsize=6)
    fig.tight_layout(pad=0.3)
    st.pyplot(fig, use_container_width=False)
    plt.close(fig)


def render_daily_chart(df_chart: pd.DataFrame, title: str):
    """Gráfico de barras diario para un usuario."""
    df_grp = df_chart.groupby('date')['hours'].sum().reset_index().sort_values('date')
    fig, ax = plt.subplots(figsize=(7, 2.5))
    color = sns.color_palette("deep", 1)[0]
    ax.bar(range(len(df_grp)), df_grp['hours'], color=color, width=0.7, edgecolor='white', linewidth=0.5)
    ax.set_xticks(range(len(df_grp)))
    # Etiquetas de horas en cada barra
    for i, h in enumerate(df_grp['hours']):
        if h > 0:
            ax.text(i, h + 0.05, f'{h:.1f}', ha='center', va='bottom', fontsize=7, fontweight='bold')
    tick_labels = [d.strftime('%d/%m') for d in df_grp['date']]
    ax.set_title(title, fontsize=10, fontweight='bold')
    ax.set_ylabel("Horas", fontsize=8)
    ax.set_xlabel("Fecha", fontsize=8)
    ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=7)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=False)
    plt.close(fig)
