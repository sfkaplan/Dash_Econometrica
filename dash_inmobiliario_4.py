import streamlit as st
import pandas as pd
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
