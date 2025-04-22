import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os

# Formatter for dollar amounts
usd_formatter = FuncFormatter(lambda x, _: f"${x:,.0f}")

# Helper function to remove outliers using the IQR method
def remove_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[column] >= lower) & (df[column] <= upper)]

# --- Streamlit UI ---
st.title("Análisis de Propiedades en Venta")

tipo_propiedad = st.selectbox("Selecciona el tipo de propiedad:", ["Departamentos", "Casas"])

# Load file based on selection
nombre_archivo = f"{tipo_propiedad.lower()}.xlsx"

# Verifica si el archivo existe
if not os.path.exists(nombre_archivo):
    st.error(f"No se encontró el archivo: {nombre_archivo}")
else:
    df = pd.read_excel(nombre_archivo)

    # Calcula Precio por m2
    df["Precio_m2"] = df["Precio_USD"] / df["Superficie_m2"]

    # Mostrar selector para tipo de propiedad dentro del archivo
    tipos_disponibles = df["habitaciones"].dropna().unique()
    tipo_seleccionado = st.selectbox("Selecciona tipo de propiedad:", tipos_disponibles)

    df_filtrado = df[df["habitaciones"] == tipo_seleccionado]

    # Checkbox para eliminar outliers
    eliminar_outliers = st.checkbox("Eliminar outliers")

    if eliminar_outliers:
        df_filtrado = remove_outliers_iqr(df_filtrado, "Superficie_m2")

    # Mostrar tablas con estadísticas descriptivas
    st.subheader("Estadísticas Descriptivas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Precio (USD)**")
        st.dataframe(df_filtrado["Precio_USD"].describe().round(2))
    with col2:
        st.markdown("**Superficie (m²)**")
        st.dataframe(df_filtrado["Superficie_m2"].describe().round(2))
    with col3:
        st.markdown("**Precio por m² (USD)**")
        st.dataframe(df_filtrado["Precio_m2"].describe().round(2))

    # Tipo de visualización
    tipo_visual = st.radio("Selecciona tipo de visualización:", ["Precios", "Superficie", "Precio por m²", "Precios y Superficie"])

    if tipo_visual == "Precios":
        st.subheader("Histograma de Precios (USD)")
        fig, ax = plt.subplots()
        sns.histplot(df_filtrado["Precio_USD"], kde=True, ax=ax)
        ax.set_xlabel("Precio (USD)")
        ax.set_ylabel("Frecuencia")
        ax.xaxis.set_major_formatter(usd_formatter)
        st.pyplot(fig)

    elif tipo_visual == "Superficie":
        st.subheader("Histograma de Superficie (m²)")
        fig, ax = plt.subplots()
        sns.histplot(df_filtrado["Superficie_m2"], kde=True, ax=ax)
        ax.set_xlabel("Superficie (m²)")
        ax.set_ylabel("Frecuencia")
        st.pyplot(fig)

    elif tipo_visual == "Precio por m²":
        st.subheader("Histograma de Precio por m²")
        fig, ax = plt.subplots()
        sns.histplot(df_filtrado["Precio_m2"], kde=True, ax=ax)
        ax.set_xlabel("Precio por m² (USD)")
        ax.set_ylabel("Frecuencia")
        ax.xaxis.set_major_formatter(usd_formatter)
        st.pyplot(fig)

    elif tipo_visual == "Precios y Superficie":
        st.subheader("Relación entre Precio y Superficie")
        fig, ax = plt.subplots()
        sns.scatterplot(data=df_filtrado, x="Superficie_m2", y="Precio_USD", ax=ax)
        sns.regplot(data=df_filtrado, x="Superficie_m2", y="Precio_USD", scatter=False, ax=ax, color='red')
        ax.set_xlabel("Superficie (m²)")
        ax.set_ylabel("Precio (USD)")
        ax.yaxis.set_major_formatter(usd_formatter)
        st.pyplot(fig)
