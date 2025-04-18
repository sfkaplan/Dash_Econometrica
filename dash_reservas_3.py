import requests
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

requests.packages.urllib3.disable_warnings()

# Streamlit UI
st.title("📊 Visualización de Datos - BCRA")

# Dictionary mapping variable names to their respective IDs
variable_dict = {
    "Reservas Internacionales (USD mn)": 1,
    "Base Monetaria (ARS mn)": 15,
}

# User selection
selected_variable = st.selectbox("Seleccionar Indicador", list(variable_dict.keys()))

# Get the corresponding ID
variable_selection = variable_dict[selected_variable]
if variable_selection == 1:
    label = "Reservas Internacionales"
else:
    label = "Base Monetaria"

# API Request
url = f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/{variable_selection}?"
response = requests.get(url, verify=False)
aux = response.json()

# Extract data and convert to DataFrame
df1 = pd.DataFrame(aux["results"])[["fecha", "valor"]]

# Convert "fecha" to datetime
df1["fecha"] = pd.to_datetime(df1["fecha"])
print(df1)
df1.index = df1["fecha"]
df1.drop("fecha", axis=1, inplace=True)
print(df1)

# Sort by date
df1 = df1.sort_index()
df1.index = pd.to_datetime(df1.index)

# Custom date selector
start_date, end_date = st.date_input(
    "Seleccionar Rango de Fechas",
    [df1.index.min(), df1.index.max()]
)

# Convert to datetime for proper slicing
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

df = df1.loc[start_date:end_date]


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
csv = df_resampled.to_csv().encode('utf-8')
st.download_button("Download Data as CSV", csv, "bcra_data.csv", "text/csv")
