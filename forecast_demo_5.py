import streamlit as st
import pandas as pd
import numpy as np
import joblib
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
import altair as alt
import datetime

# Load data & models
test_df = pd.read_csv("C:\\Curso Pronóstico\\2025\\test_power_consumption.csv", parse_dates=['dt'])
X_test_rf = np.load("C:\\Curso Pronóstico\\2025\\test_power_consumption_rf.npy")
X_test_lstm = np.load("C:\\Curso Pronóstico\\2025\\test_power_consumption_lstm.npy")

arma_model = joblib.load("arma_model.pkl")
rf_model = joblib.load("rf_model.pkl")
lstm_model = load_model("lstm_model.keras", compile=False)

# Load scaler
scaler = joblib.load("scaler.pkl")

# Forecasts (full length)
arma_preds = arma_model.forecast(steps=len(test_df))
rf_preds = rf_model.predict(X_test_rf)
lstm_preds = lstm_model.predict(X_test_lstm).flatten()
lstm_preds_inversed = scaler.inverse_transform(lstm_preds.reshape(-1, 1)).flatten()

# App UI
st.title("Pronóstico de Ventas Minoristas")

model_choice = st.selectbox("Elegir un Modelo", ["ARMA", "Random Forest", "LSTM"])
forecast_type = st.radio("Forecast type", ["Pronóstico Puntual (por minute)", "Pronóstico Acumulado"])

st.subheader("Seleccionar fecha inicial y final (con hora y minutos)")

# Get min and max datetime from the dataset
min_dt = test_df['dt'].min()
max_dt = test_df['dt'].max()

# Select date
start_date = st.date_input("Fecha Inicial", value=min_dt.date(), min_value=min_dt.date(), max_value=max_dt.date())
start_time = st.time_input("Hora/Minuto", value=datetime.time(0, 0))

end_date = st.date_input("Fecha Final", value=min_dt.date(), min_value=min_dt.date(), max_value=max_dt.date())
end_time = st.time_input("Hora/Minuto", value=datetime.time(23, 59))

# Combine into full datetime
start_dt = datetime.datetime.combine(start_date, start_time)
end_dt = datetime.datetime.combine(end_date, end_time)

# Filter dataframe
mask = (test_df['dt'] >= start_dt) & (test_df['dt'] <= end_dt)
filtered_df = test_df[mask]

# Prevent empty selections
if filtered_df.empty:
    st.warning("No data available in the selected datetime range.")
    st.stop()

# Get position indices for slicing predictions
start_pos = test_df.index.get_loc(filtered_df.index[0])
end_pos = test_df.index.get_loc(filtered_df.index[-1]) + 1

# Slice forecasts
if model_choice == "ARMA":
    preds = arma_preds[start_pos:end_pos]
elif model_choice == "Random Forest":
    preds = rf_preds[start_pos:end_pos]
elif model_choice == "LSTM":
    preds = lstm_preds_inversed[start_pos:end_pos]

# Get actual values
actual = test_df['Global_active_power'].iloc[start_pos:end_pos].values

# Apply cumulative forecast
if forecast_type == "Cumulative forecast":
    preds = np.cumsum(preds) + test_df['Global_active_power'].iloc[start_pos]

# Prepare chart dataframe
n = min(len(filtered_df), len(preds), len(actual))
chart_df = pd.DataFrame({
    'Datetime': filtered_df['dt'].values[:n],
    'Actual': actual[:n],
    'Forecast': preds[:n]
})

# Altair line chart with y-axis label
chart = alt.Chart(chart_df).transform_fold(
    ['Actual', 'Forecast'],
    as_=['Series', 'Value']
).mark_line().encode(
    x='Datetime:T',
    y=alt.Y('Value:Q', title='USD mn'),
    color='Series:N'
).properties(
    width=800,
    height=400
)

st.altair_chart(chart, use_container_width=True)
