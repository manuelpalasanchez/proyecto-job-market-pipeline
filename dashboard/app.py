import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import pytz
from collections import Counter

load_dotenv()

st.set_page_config(
    page_title="Tech Job Market Dashboard",
    layout="wide"
)
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_engine():
    if os.getenv("USE_NEON", "false").lower() == "true":
        db_url = (
            f"postgresql://{os.getenv('NEON_USER')}:{os.getenv('NEON_PASSWORD')}"
            f"@{os.getenv('NEON_HOST')}:{os.getenv('NEON_PORT')}/{os.getenv('NEON_DB')}?sslmode=require"
        )
    else:
        db_url = (
            f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
            f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        )
    return create_engine(db_url)

@st.cache_data(ttl=3600)
def load_data():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM jobs", engine)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    return df

df = load_data()

st.title("Mercado laboral tech en España")


with st.sidebar:
    st.markdown("## Filtros")
    st.markdown("---")

    fuentes_disponibles = sorted(df["source"].dropna().unique().tolist())
    fuentes_sel = st.multiselect("Fuente", fuentes_disponibles, default=fuentes_disponibles)

    fecha_min = df["created_at"].min().date()
    fecha_max = df["created_at"].max().date()
    fecha_hoy = pd.Timestamp.now(tz=pytz.UTC).date()
    fecha_rango = st.date_input(
        "Rango de fechas",
        value=(fecha_hoy - pd.Timedelta(days=60), fecha_hoy),
        min_value=fecha_min,
        max_value=fecha_hoy
    )

    ciudades = ["Todas"] + sorted(df["location"].dropna().unique().tolist())
    ciudad_sel = st.selectbox("Ciudad", ciudades)

    st.caption(f"Última actualización: {df['extracted_at'].max().strftime('%d/%m/%Y %H:%M')}")


    tipos_contrato = sorted(df["contract_type"].dropna().unique().tolist())
    contratos_sel = st.multiselect("Tipo de contrato", tipos_contrato, default=tipos_contrato)

    tiempos_contrato = sorted(df["contract_time"].dropna().unique().tolist())
    tiempo_sel = st.multiselect("Jornada laboral", tiempos_contrato, default=tiempos_contrato)
   


dff = df.copy()

if fuentes_sel:
    dff = dff[dff["source"].isin(fuentes_sel)]

if ciudad_sel != "Todas":
    dff = dff[dff["location"] == ciudad_sel]

if len(fecha_rango) == 2:
    fecha_inicio = pd.Timestamp(fecha_rango[0], tz="UTC")
    fecha_fin = pd.Timestamp(fecha_rango[1], tz="UTC")
    dff = dff[
        dff["created_at"].isna() |
        ((dff["created_at"] >= fecha_inicio) & (dff["created_at"] <= fecha_fin))
    ]

if contratos_sel:
    dff = dff[dff["contract_type"].isin(contratos_sel) | dff["contract_type"].isna()]

if tiempo_sel:
    dff = dff[dff["contract_time"].isin(tiempo_sel) | dff["contract_time"].isna()]



k1, k2, k3, k4 = st.columns(4)
k1.metric("Total ofertas", len(dff))
k2.metric("Fuentes activas", dff["source"].nunique())
k3.metric("Ciudades", dff["location"].nunique())
k4.metric("Con salario", dff["salary_min"].notna().sum())

col_izq, col_der = st.columns([1, 1])

with col_izq:
    st.markdown("#### Ofertas por ubicación")
    mapa_df = dff[dff["latitud"].notna() & dff["longitud"].notna()].copy()
    mapa_grouped = mapa_df.groupby(["location", "latitud", "longitud"]).size().reset_index(name="count")
    fig_mapa = px.scatter_map(
        mapa_grouped,
        lat="latitud",
        lon="longitud",
        size="count",
        color="count",
        hover_name="location",
        hover_data={"count": True, "latitud": False, "longitud": False},
        color_continuous_scale=["#93C5FD", "#1D4ED8"],
        size_max=50,
        zoom=4,
        center={"lat": 40.4, "lon": -3.7},
        map_style="carto-positron",
        labels={"count": "Ofertas"}
    )
    fig_mapa.update_layout(
        coloraxis_showscale=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=350
    )
    st.plotly_chart(fig_mapa, use_container_width=True)

    st.markdown("#### Tendencia temporal")
    trend = dff[dff["created_at"].notna()].copy()
    trend["fecha"] = trend["created_at"].dt.date
    trend_grouped = trend.groupby("fecha").size().reset_index(name="ofertas")
    fig_trend = px.line(
        trend_grouped, x="fecha", y="ofertas",
        markers=True,
        labels={"fecha": "", "ofertas": "Ofertas"}
    )
    fig_trend.update_traces(line_color="#1D4ED8", marker_color="#1D4ED8")
    fig_trend.update_layout(
        hovermode="x unified",
        height=280,
        margin={"t": 10, "b": 10}
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_der:
    st.markdown("#### Tecnologías más demandadas")
    tags_series = dff["tags"].dropna().str.split(",").explode().str.strip().str.lower()
    tags_series = tags_series[~tags_series.isin(["", "unknown", "it-jobs"])]
    tag_counts = Counter(tags_series).most_common(15)
    tags_df = pd.DataFrame(tag_counts, columns=["tecnologia", "count"])
    fig_tags = px.bar(
        tags_df,
        x="count",
        y="tecnologia",
        orientation="h",
        labels={"count": "Menciones", "tecnologia": ""},
        color="count",
        color_continuous_scale=["#93C5FD", "#1D4ED8"]
    )
    fig_tags.update_layout(
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
        height=650,
        margin={"t": 10, "b": 10}
    )
    st.plotly_chart(fig_tags, use_container_width=True)



with st.expander("Ver todas las ofertas", expanded=False):
    tabla_df = dff[[
        "title", "company", "location", "source",
        "contract_type", "salary_min", "salary_max",
        "tags", "url", "created_at"
    ]].copy()

    tabla_df["created_at"] = pd.to_datetime(tabla_df["created_at"]).dt.strftime("%d/%m/%Y").fillna("—")
    tabla_df["salario"] = tabla_df.apply(
        lambda r: f"{int(r.salary_min):,}€ - {int(r.salary_max):,}€"
        if pd.notna(r.salary_min) and pd.notna(r.salary_max) else "—", axis=1
    )
    tabla_df = tabla_df.drop(columns=["salary_min", "salary_max"])

    st.dataframe(
        tabla_df,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "url": st.column_config.LinkColumn("Enlace", display_text="Ver oferta"),
            "title": "Título",
            "company": "Empresa",
            "location": "Ciudad",
            "source": "Fuente",
            "contract_type": "Contrato",
            "tags": "Tecnologías",
            "created_at": "Publicada",
            "salario": "Salario",
        }
    )