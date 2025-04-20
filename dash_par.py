import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from io import BytesIO

requests.packages.urllib3.disable_warnings()

# Streamlit UI
st.title("📊 Visualización de Datos - Inflación & Actividad")

# Dictionary mapping variable names to their respective IDs
variable_dict = {
    "IMAEP": "actividad",
    "Inflación": "infla"
}

# User selection
selected_variable = st.selectbox("Seleccionar Indicador", list(variable_dict.keys()))

# Define label for chart title
label = "Inflación" if variable_dict[selected_variable] == "infla" else "IMAEP"

# Function to fetch IMAEP data from BCP
@st.cache_data
def get_imaep_data():
    bcp_URL = "https://github.com/sfkaplan/Dash_Econometrica/raw/refs/heads/main/anexo.xlsx"
    df = pd.read_excel(bcp_URL, sheet_name="CUADRO 9", skiprows=9)
    dates = df.iloc[1:-3, 1]
    data = df.iloc[1:-3, 2:]
    df2 = pd.DataFrame(data)
    df2.columns = df.columns[2:]
    df2.index = pd.to_datetime(dates)
    df2 = df2.dropna()  # Remove NaN values
    return df2

# Function to fetch inflation data from BCP
@st.cache_data
def get_inf_data():
    inf_URL = "https://github.com/sfkaplan/Dash_Econometrica/raw/refs/heads/main/anexo.xlsx"
    df = pd.read_excel(inf_URL, sheet_name="CUADRO 14", skiprows=10)
    dates = df.iloc[1:-3, 0]
    data = df.iloc[1:-3, 1:-3]
    df2 = pd.DataFrame(data)
    df2.columns = df.columns[1:-3]
    df2.index = pd.to_datetime(dates)
    df2 = df2.dropna()  # Remove NaN values
    return df2

# Fetch data based on user selection
df1 = get_inf_data() if variable_dict[selected_variable] == "infla" else get_imaep_data()

# Custom date selector
start_date, end_date = st.date_input(
    "Seleccionar Rango de Fechas",
    [df1.index.min(), df1.index.max()]
)

# Detect selected indicator type
is_inflation = variable_dict[selected_variable] == "infla"
is_activity = variable_dict[selected_variable] == "actividad"

# Category selector
available_categories = df1.columns.tolist()
selected_category = st.selectbox("Seleccionar categoría", available_categories)

# Choose type of chart
if is_inflation or is_activity:
    chart_type = st.radio("Tipo de visualización", ["Niveles", "Interanual", "Mensual"])
else:
    allowed_mom_categories = [
        "IMAEP Serie Desestacionalizada",
        "IMAEP sin Agri. ni Bin. Serie Desestacionalizada"
    ]
    if any(cat in available_categories for cat in allowed_mom_categories):
        chart_type = st.radio("Tipo de visualización", ["Interanual", "Mensual"])
    else:
        chart_type = "Interanual"

# Filter data by selected date range
df_filtered = df1.loc[start_date:end_date]

# Prepare data for plotting
if chart_type == "Niveles":
    df_plot = df_filtered[selected_category]
    chart_title = f"{selected_category} - Niveles"
elif chart_type == "Interanual":
    df_plot = df_filtered[selected_category].pct_change(12) * 100
    chart_title = f"{selected_category} - Variación Interanual"
elif chart_type == "Mensual":
    df_plot = df_filtered[selected_category].pct_change(1) * 100
    chart_title = f"{selected_category} - Variación Mensual"

df_plot = df_plot.dropna()

# Plot
if chart_type == "Niveles":
    fig = px.line(
        x=df_plot.index,
        y=df_plot.values,
        labels={"x": "Fecha", "y": "Nivel"},
        title=chart_title
    )
else:
    fig = px.bar(
        x=df_plot.index,
        y=df_plot.values,
        labels={"x": "Fecha", "y": "Variación (%)"},
        title=chart_title
    )

st.plotly_chart(fig, use_container_width=True)
