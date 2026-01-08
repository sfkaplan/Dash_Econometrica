import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

# Function to load Excel file
@st.cache_data
def load_data(tipo):
    if tipo == "Departamento":
        return pd.read_excel("https://github.com/sfkaplan/Dash_Econometrica/raw/refs/heads/main/departamentos.xlsx")
    elif tipo == "Casa":
        return pd.read_excel("https://github.com/sfkaplan/Dash_Econometrica/raw/refs/heads/main/casas.xlsx")
    else:
        return pd.DataFrame()

# USD formatter for y-axes
usd_formatter = FuncFormatter(lambda x, _: f"${x:,.0f}")


# PYG formatter (for metrics)
def pyg_format(x: float, decimals: int = 1) -> str:
    """Format numbers using '.' as thousands separator and ',' as decimal separator."""
    try:
        s = f"{float(x):,.{decimals}f}"
    except (TypeError, ValueError):
        return ""
    # Python default: ',' thousands and '.' decimal -> swap to '.' thousands and ',' decimal
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

def pv_annuity(payment: float, r: float, n: int) -> float:
    """Present value of an annuity (payments at end of each year)."""
    if n <= 0 or payment <= 0:
        return 0.0
    if r <= 0:
        return float(payment) * n
    return float(payment) * (1 - (1 + r) ** (-n)) / r

# Sidebar - Select type of property
st.sidebar.title("Filtros")
tipo_propiedad = st.sidebar.selectbox("Tipo de propiedad", ["Departamento", "Casa"])

# Load corresponding file
df = load_data(tipo_propiedad)

# Create new column: Precio por m²
df["Precio_m2"] = df["Precio_USD"] / df["Superficie_m2"]

# Property type selector based on 'habitaciones'
tipos_disponibles = df["habitaciones"].dropna().unique().tolist()
tipo_seleccionado = st.sidebar.selectbox("Tipo específico", ["Todos"] + tipos_disponibles)

# Filter if user selects a specific property subtype
df_filtrado = df.copy()
if tipo_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["habitaciones"] == tipo_seleccionado]

# Show stats tables
st.subheader("Estadísticas descriptivas")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Precio en USD**")
    st.dataframe(df_filtrado["Precio_USD"].describe().round(2))

with col2:
    st.markdown("**Superficie (m²)**")
    st.dataframe(df_filtrado["Superficie_m2"].describe().round(2))

with col3:
    st.markdown("**Precio por m² (USD/m²)**")
    st.dataframe(df_filtrado["Precio_m2"].describe().round(2))


# Selector de tipo de gráfico
tipo_visual = st.selectbox(
    "¿Qué querés visualizar?",
    ["Precios", "Superficie", "Precio por m²", "Precios y Superficie"]
)

# Plotting
st.subheader("Visualización")
plt.style.use('seaborn-v0_8')

if tipo_visual == "Precios":
    fig, ax = plt.subplots()
    sns.histplot(df_filtrado["Precio_USD"], bins=20, kde=True, ax=ax)
    ax.set_title("Distribución de Precios (USD)")
    ax.set_xlabel("Precio (USD)")
    ax.set_ylabel("Frecuencia")
    ax.xaxis.set_major_formatter(usd_formatter)
    st.pyplot(fig)

elif tipo_visual == "Superficie":
    fig, ax = plt.subplots()
    sns.histplot(df_filtrado["Superficie_m2"], bins=20, kde=True, ax=ax, color='orange')
    ax.set_title("Distribución de Superficies (m²)")
    ax.set_xlabel("Superficie (m²)")
    ax.set_ylabel("Frecuencia")
    st.pyplot(fig)

elif tipo_visual == "Precio por m²":
    fig, ax = plt.subplots()
    sns.histplot(df_filtrado["Precio_m2"], bins=20, kde=True, ax=ax, color='green')
    ax.set_title("Distribución de Precio por m²")
    ax.set_xlabel("USD por m²")
    ax.set_ylabel("Frecuencia")
    ax.xaxis.set_major_formatter(usd_formatter)
    st.pyplot(fig)

elif tipo_visual == "Precios y Superficie":
    st.subheader("Precio vs. Superficie")

    eliminar_outliers = st.checkbox("Eliminar outliers en superficie (m²)", value=True)

    df_plot = df_filtrado.copy()

    if eliminar_outliers:
        Q1 = df_plot["Superficie_m2"].quantile(0.25)
        Q3 = df_plot["Superficie_m2"].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df_plot = df_plot[
            (df_plot["Superficie_m2"] >= lower_bound) &
            (df_plot["Superficie_m2"] <= upper_bound)
        ]

    fig, ax = plt.subplots()
    sns.scatterplot(data=df_plot, x="Superficie_m2", y="Precio_USD", ax=ax)
    sns.regplot(data=df_plot, x="Superficie_m2", y="Precio_USD", scatter=False, ax=ax, color="red")
    ax.set_title("Precio vs. Superficie" + (" (sin outliers)" if eliminar_outliers else ""))
    ax.set_xlabel("Superficie (m²)")
    ax.set_ylabel("Precio (USD)")
    ax.yaxis.set_major_formatter(usd_formatter)
    st.pyplot(fig)

# -----------------------
# MÓDULO: CÁLCULO DE ALQUILER (PYG)
# -----------------------
st.subheader("Cálculo de alquiler (Guaraníes)")

with st.expander("Ingresar alquiler anual, años y tasa de descuento", expanded=False):
    c1, c2, c3 = st.columns(3)

    with c1:
        alquiler_anual_pyg = st.number_input(
            "Alquiler anual (PYG)",
            min_value=0.0,
            value=0.0,
            step=100000.0,
            format="%.0f",
            help="Monto anual del alquiler expresado en guaraníes."
        )

    with c2:
        anios_alquiler = st.number_input(
            "Número de años",
            min_value=0,
            value=1,
            step=1,
            help="Cantidad de años a alquilar."
        )

    with c3:
        tasa_desc_pct = st.number_input(
            "Tasa de interés anual (%)",
            min_value=0.0,
            value=10.0,
            step=0.5,
            format="%.2f",
            help="Tasa anual usada para descontar los flujos de alquiler."
        )

    r = tasa_desc_pct / 100.0
    n = int(anios_alquiler)

    total_nominal_pyg = float(alquiler_anual_pyg) * n
    total_descontado_pyg = pv_annuity(float(alquiler_anual_pyg), float(r), n)

    m1, m2 = st.columns(2)
    with m1:
        st.metric("Total nominal (PYG)", pyg_format(total_nominal_pyg, 1))
    with m2:
        st.metric("Total descontado (valor presente) (PYG)", pyg_format(total_descontado_pyg, 1))

    # (Opcional) tabla de flujos anuales y flujos descontados
    if n > 0 and float(alquiler_anual_pyg) > 0:
        years = np.arange(1, n + 1)
        flujo = np.full_like(years, float(alquiler_anual_pyg), dtype=float)
        factor_desc = (1 + r) ** (-years) if r > 0 else np.ones_like(years, dtype=float)
        flujo_desc = flujo * factor_desc

        df_flujos = pd.DataFrame({
            "Año": years,
            "Flujo (PYG)": flujo,
            "Factor descuento": factor_desc,
            "Flujo descontado (PYG)": flujo_desc
        })

        st.caption("Detalle: flujos anuales y valor descontado")
        st.dataframe(
            df_flujos.style.format({
                "Flujo (PYG)": "{:,.1f}",
                "Factor descuento": "{:.6f}",
                "Flujo descontado (PYG)": "{:,.1f}",
            }),
            use_container_width=True
        )

# -----------------------
# MÓDULO: CÁLCULO DE RENTA PARA INMUEBLE
# -----------------------
st.subheader("Cálculo de renta para inmueble")

with st.expander("Cálculo de renta para inmueble", expanded=False):
    c1, c2 = st.columns(2)

    with c1:
        precio_inmueble_pyg = st.number_input(
            "Precio del inmueble (PYG)",
            min_value=0.0,
            value=0.0,
            step=1000000.0,
            format="%.0f",
            help="Precio del inmueble expresado en guaraníes."
        )

    with c2:
        renta_pretendida_pct = st.number_input(
            "Renta pretendida (%)",
            min_value=0.0,
            value=5.0,
            step=0.25,
            format="%.2f",
            help="Rendimiento anual objetivo como porcentaje del precio del inmueble (por ej. 5%)."
        )

    alquiler_anual_requerido = float(precio_inmueble_pyg) * (float(renta_pretendida_pct) / 100.0)

    st.metric("Alquiler anual requerido (PYG)", pyg_format(alquiler_anual_requerido, 1))
    st.caption("Cálculo: alquiler anual requerido = precio del inmueble × renta pretendida.")
