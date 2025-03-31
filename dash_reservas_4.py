import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from io import BytesIO

requests.packages.urllib3.disable_warnings()

# Streamlit UI
st.title("📊 Visualización de Datos - BCRA & INDEC")

# Dictionary mapping variable names to their respective IDs
variable_dict = {
    "Reservas Internacionales (USD mn)": 1,
    "Base Monetaria (ARS mn)": 15,
    "Inflación Mensual (%)": "inflacion",
}

# User selection
selected_variable = st.selectbox("Seleccionar Indicador", list(variable_dict.keys()))

# Check if Inflation Rate is selected
if variable_dict[selected_variable] == "inflacion":
    label = "Inflación Mensual (%)"
else:
    variable_selection = variable_dict[selected_variable]
    label = selected_variable  # Keeps the original indicator label

# Function to fetch inflation data from INDEC
@st.cache_data
def get_inflation_data():
    INDEC_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_aperturas.xls"
    response = requests.get(INDEC_URL)
    with BytesIO(response.content) as excel_file:
        df = pd.read_excel(excel_file)  # Adjust skiprows if needed
    dates = df.iloc[4, 1:].T
    inflation = df.iloc[7, 1:].T
    df2 = pd.DataFrame(inflation)
    df2.columns = ["Inflación Mensual (%)"]
    df2.index = pd.to_datetime(dates)
    df2 = df2.dropna()  # Remove NaN values
    return df2

# Fetch data based on user selection
if variable_dict[selected_variable] == "inflacion":
    df1 = get_inflation_data()
else:
    # API Request
    url = f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/{variable_selection}?"
    response = requests.get(url, verify=False)
    aux = response.json()

    # Extract data and convert to DataFrame
    df1 = pd.DataFrame(aux["results"])[["fecha", "valor"]]

    # Convert "fecha" to datetime
    df1["fecha"] = pd.to_datetime(df1["fecha"])
    df1.set_index("fecha", inplace=True)

# Sort by date
df1 = df1.sort_index()

# Custom date selector
start_date, end_date = st.date_input(
    "Seleccionar Rango de Fechas",
    [df1.index.min(), df1.index.max()]
)

# Convert to datetime for proper slicing
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

df = df1.loc[start_date:end_date]

# If the user selects inflation, only show a bar chart
if variable_dict[selected_variable] == "inflacion":
    aux = df.index.strftime("%b %Y")  # Convert to "Mar 2025" format
    fig = px.bar(df.reset_index(),  x=aux, y=df.columns[0],  title="Inflación Mensual (%)",labels={"index": "Fecha", df.columns[0]: "Inflación (%)"})
    st.plotly_chart(fig)
else:
    # Options for aggregation and transformation
    aggregation = st.selectbox("Seleccionar Unidad de Tiempo", ["Diaria", "Semanal", "Mensual", "Trimestral", "Anual"])
    transformation = st.selectbox("Ver Tipo de Serie", ["Niveles", "Cambio Porcentual"])

    # Resampling logic
    if aggregation == "Diaria":
        df_resampled = df
    elif aggregation == "Semanal":
        df_resampled = df.resample('W').last()
    elif aggregation == "Mensual":
        df_resampled = df.resample('M').last()
    elif aggregation == "Trimestral":
        df_resampled = df.resample('Q').last()
    elif aggregation == "Anual":
        df_resampled = df.resample('Y').last()

    # Apply percentage change if selected
    if transformation == "Cambio Porcentual":
        df_resampled = df_resampled.pct_change() * 100

    # Plot the data
    fig = px.line(
        df_resampled, 
        x=df_resampled.index, 
        y=df_resampled.columns,
        title=f"{label}: {aggregation} ({transformation})"
    )
    st.plotly_chart(fig)

# Export Data
csv = df.to_csv().encode('utf-8')
st.download_button("Download Data as CSV", csv, "bcra_data.csv", "text/csv")
