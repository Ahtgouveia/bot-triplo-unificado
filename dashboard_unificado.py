import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from streamlit_autorefresh import st_autorefresh

# ============================
# CONFIGURAÇÃO DA PÁGINA
# ============================

st.set_page_config(
    page_title="Dashboard Bot Triplo Premium",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Dashboard Unificado — Bot Triplo Premium")
st.markdown("Atualiza automaticamente a cada 30 segundos ou quando o bot gerar novos dados.")

# ============================
# AJUSTE DE FUSO HORÁRIO UTC-3
# ============================

def agora_brasil():
    return datetime.utcnow() - timedelta(hours=3)

# ============================
# AUTO-REFRESH INTELIGENTE
# ============================

st_autorefresh(interval=30000, key="refresh")

def timestamp_mais_recente(df, coluna):
    if len(df) == 0:
        return None
    return df[coluna].max()

# ============================
# CARREGAR ARQUIVOS
# ============================

def carregar_alertas():
    if not os.path.exists("alertas.csv"):
        return pd.DataFrame(columns=["data", "symbol", "tipo", "preco", "volume", "extra"])

    df = pd.read_csv("alertas.csv", header=None)

    # Força os nomes corretos
    df.columns = ["data", "symbol", "tipo", "preco", "volume", "extra"]

    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    return df


def carregar_trendscore():
    if not os.path.exists("trendscore.csv"):
        return pd.DataFrame(columns=["timestamp", "symbol", "trend_score", "sma1", "sma2", "preco3"])

    df = pd.read_csv("trendscore.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df


df_alertas = carregar_alertas()
df_ts = carregar_trendscore()

# ============================
# AUTO-UPDATE (SEM RERUN)
# ============================

ts_alertas = timestamp_mais_recente(df_alertas, "data")
ts_ts = timestamp_mais_recente(df_ts, "timestamp")

if "ultimo_update" not in st.session_state:
    st.session_state["ultimo_update"] = datetime.min

if ts_alertas and ts_alertas > st.session_state["ultimo_update"]:
    st.session_state["ultimo_update"] = ts_alertas

if ts_ts and ts_ts > st.session_state["ultimo_update"]:
    st.session_state["ultimo_update"] = ts_ts

# ============================
# ABAS PRINCIPAIS
# ============================

aba_geral, aba_alertas, aba_ts, aba_ativo = st.tabs(
    ["🏠 Dashboard Geral", "📘 Alertas", "🔥 TrendScore 3.0", "🔍 Análise por Ativo"]
)

# ============================
# 1) DASHBOARD GERAL
# ============================

with aba_geral:
    st.header("📊 Visão Geral do Sistema")

    col1, col2, col3, col4 = st.columns(4)

    agora = agora_brasil()

    with col1:
        if len(df_alertas) > 0:
            st.metric(
                "Alertas Hoje",
                df_alertas[df_alertas["data"].dt.date == agora.date()].shape[0]
            )
        else:
            st.metric("Alertas Hoje", 0)

    with col2:
        if len(df_alertas) > 0:
            st.metric(
                "Alertas na Semana",
                df_alertas[df_alertas["data"] >= agora - timedelta(days=7)].shape[0]
            )
        else:
            st.metric("Alertas na Semana", 0)

    with col3:
        if len(df_alertas) > 0:
            st.metric(
                "Alertas no Mês",
                df_alertas[df_alertas["data"] >= agora - timedelta(days=30)].shape[0]
            )
        else:
            st.metric("Alertas no Mês", 0)

    with col4:
        if len(df_ts) > 0:
            top10_media = (
                df_ts.sort_values("timestamp", ascending=False)
                .groupby("symbol").tail(1)
                .sort_values("trend_score", ascending=False)
                .head(10)["trend_score"]
                .mean()
            )
            st.metric("TrendScore Médio (Top 10)", round(top10_media, 2))
        else:
            st.metric("TrendScore Médio (Top 10)", "—")

    st.subheader("📈 Distribuição de Alertas por Tipo")
    if len(df_alertas) > 0:
        graf = df_alertas.groupby("tipo").size().reset_index(name="quantidade")
        st.bar_chart(graf, x="tipo", y="quantidade")
    else:
        st.info("Nenhum alerta disponível.")

    st.subheader("🏆 Top 10 TrendScore da Rodada")
    if len(df_ts) > 0:
        ultimos_ts = df_ts.sort_values("timestamp").groupby("symbol").tail(1)
        top10 = ultimos_ts.sort_values("trend_score", ascending=False).head(10)
        st.dataframe(top10, width="stretch")
    else:
        st.info("Nenhum TrendScore disponível.")

    st.subheader("🏅 Ranking Unificado de Ativos")
    if len(df_alertas) > 0:
        ranking_unificado = (
            df_alertas.groupby("symbol")
            .size()
            .reset_index(name="alertas_totais")
            .sort_values("alertas_totais", ascending=False)
        )
        st.dataframe(ranking_unificado.head(20), width="stretch")
    else:
        st.info("Nenhum alerta para gerar ranking.")

# ============================
# 2) ABA DE ALERTAS
# ============================

with aba_alertas:
    st.header("📘 Alertas — SMA1, SMA2 e Preço3")

    if len(df_alertas) == 0:
        st.warning("Nenhum alerta encontrado ainda.")
    else:
        periodo = st.selectbox(
            "Período:",
            ["Hoje", "Últimas 24h", "Últimas 48h", "Semana", "Mês", "Personalizado"]
        )

        agora = agora_brasil()

        if periodo == "Hoje":
            inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        elif periodo == "Últimas 24h":
            inicio = agora - timedelta(hours=24)
        elif periodo == "Últimas 48h":
            inicio = agora - timedelta(hours=48)
        elif periodo == "Semana":
            inicio = agora - timedelta(days=agora.weekday())
        elif periodo == "Mês":
            inicio = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif periodo == "Personalizado":
            inicio = st.date_input("Data inicial:")
            inicio = datetime.combine(inicio, datetime.min.time())

        df_filtro = df_alertas[df_alertas["data"] >= inicio]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("SMA1 Alta", df_filtro[df_filtro["tipo"] == "SMA1_alta"].shape[0])
            st.metric("SMA1 Baixa", df_filtro[df_filtro["tipo"] == "SMA1_baixa"].shape[0])

        with col2:
            st.metric("SMA2 Alta", df_filtro[df_filtro["tipo"] == "SMA2_alta"].shape[0])
            st.metric("SMA2 Baixa", df_filtro[df_filtro["tipo"] == "SMA2_baixa"].shape[0])

        with col3:
            st.metric("Preço3 Alta", df_filtro[df_filtro["tipo"] == "Preco3_alta"].shape[0])
            st.metric("Preço3 Baixa", df_filtro[df_filtro["tipo"] == "Preco3_baixa"].shape[0])

        st.subheader("📊 Ranking — Moedas mais alertadas")
        ranking = (
            df_filtro.groupby("symbol")
            .size()
            .reset_index(name="alertas")
            .sort_values("alertas", ascending=False)
        )
        st.dataframe(ranking.head(20), width="stretch")

# ============================
# 3) ABA TRENDSCORE
# ============================

with aba_ts:
    st.header("🔥 TrendScore 3.0")

    if len(df_ts) == 0:
        st.warning("Nenhum TrendScore disponível.")
    else:
        ultimos = df_ts.sort_values("timestamp").groupby("symbol").tail(1)

        st.subheader("🏆 Top 10 TrendScore")
        top10 = ultimos.sort_values("trend_score", ascending=False).head(10)
        st.dataframe(top10, width="stretch")

        st.subheader("🔥 Heatmap de Tendência")
        heatmap = ultimos.pivot_table(
            index="symbol",
            values="trend_score",
            aggfunc="mean"
        )
        st.dataframe(
            heatmap.style.background_gradient(cmap="RdYlGn"),
            width="stretch"
        )

        st.subheader("📚 Histórico Completo")
        st.dataframe(df_ts.sort_values("timestamp", ascending=False), width="stretch")

# ============================
# 4) ABA ANÁLISE POR ATIVO
# ============================

with aba_ativo:
    st.header("🔍 Análise Avançada por Ativo")

    ativos = sorted(set(df_alertas["symbol"].dropna().unique()) | set(df_ts["symbol"].dropna().unique()))

    if len(ativos) == 0:
        st.info("Nenhum ativo disponível.")
    else:
        ativo = st.selectbox("Escolha o ativo:", ativos)

        df_a = df_alertas[df_alertas["symbol"] == ativo]
        df_t = df_ts[df_ts["symbol"] == ativo]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### 📘 Alertas Recentes — {ativo}")
            if len(df_a) > 0:
                st.dataframe(
                    df_a.sort_values("data", ascending=False).head(30),
                    width="stretch"
                )
            else:
                st.info("Nenhum alerta para este ativo.")

        with col2:
            st.markdown(f"### 🔥 TrendScore Recentes — {ativo}")
            if len(df_t) > 0:
                st.dataframe(
                    df_t.sort_values("timestamp", ascending=False).head(30),
                    width="stretch"
                )
            else:
                st.info("Nenhum TrendScore para este ativo.")

        if len(df_t) > 0:
            st.subheader("📈 Evolução do TrendScore")
            graf_ts = df_t[["timestamp", "trend_score"]].set_index("timestamp")
            st.line_chart(graf_ts, width="stretch")

        df_preco3 = df_a[df_a["tipo"].str.contains("Preco3", na=False)]
        if len(df_preco3) > 0:
            st.subheader("📈 Evolução do Preço (alertas Preço3)")
            graf_preco = df_preco3[["data", "preco"]].set_index("data")
            st.line_chart(graf_preco, width="stretch")