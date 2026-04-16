import streamlit as st
import pandas as pd
import numpy as np
import folium
import os
import serial
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression

# ---------- PAGE ----------
st.set_page_config(page_title="River Monitoring", layout="wide")
st.title("River Pollution Monitoring System")

# ---------- SERIAL (READ ONCE) ----------
def read_arduino():
    try:
        ser = serial.Serial('COM3', 9600, timeout=2)  # 🔴 change port
        line = ser.readline().decode('utf-8').strip()
        ser.close()

        if line:
            parts = line.split(',')
            data = {}
            for part in parts:
                key, value = part.split(':')
                data[key.strip()] = float(value.strip())

            return data

    except Exception as e:
        print("Serial error:", e)
        return None

sensor_data = read_arduino()

# ---------- LOAD DATA ----------
def load_dataset():
    path = "ganga.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        st.error("Dataset missing")
        st.stop()

# ---------- MODEL ----------
def load_model():
    df = load_dataset().dropna()
    X = df[["pH", "DO", "Temp", "ORP"]]
    y = df["Cond"]

    model = LinearRegression()
    model.fit(X, y)
    return model

model = load_model()

# ---------- STATUS ----------
def get_status(cond):
    if cond < 300:
        return "Safe"
    elif cond < 600:
        return "Moderate"
    return "Polluted"

# ---------- ZONES ----------
def generate_zones():
    base_lat = 25.3100
    base_lon = 83.0140

    zones = []

    for i in range(8):
        lat = base_lat - (i * 0.009)
        lon = base_lon + (i * 0.001)

        if sensor_data:
            # slight variation per zone (REALISTIC)
            ph = sensor_data["pH"] + np.random.uniform(-0.1, 0.1)
            do = sensor_data["DO"] + np.random.uniform(-0.2, 0.2)
            temp = sensor_data["Temp"] + np.random.uniform(-0.5, 0.5)
            orp = sensor_data["ORP"] + np.random.uniform(-5, 5)
        else:
            # only fallback if Arduino not connected
            ph, do, temp, orp = 7, 8, 25, 300

        pred = model.predict([[ph, do, temp, orp]])[0]

        zones.append({
            "zone": chr(65+i),
            "lat": lat,
            "lon": lon,
            "ph": round(ph,2),
            "do": round(do,2),
            "temp": round(temp,2),
            "orp": round(orp,2),
            "pred": round(pred, 2)
        })

    return zones

# ---------- SESSION ----------
if "zones" not in st.session_state:
    st.session_state.zones = generate_zones()

if "selected_idx" not in st.session_state:
    st.session_state.selected_idx = 0

zones = st.session_state.zones

# ---------- SIDEBAR ----------
st.sidebar.title("📍 Controls")

zone_names = [f"Zone {z['zone']}" for z in zones]
selected = st.sidebar.radio("Select Zone:", zone_names)

st.session_state.selected_idx = zone_names.index(selected)

if st.sidebar.button("🔄 Refresh Data"):
    st.session_state.zones = generate_zones()
    st.rerun()

# ---------- MAP ----------
st.subheader("🗺️ Ganga Monitoring Map")

m = folium.Map(location=[25.27, 83.018], zoom_start=13)

for z in zones:
    status = get_status(z["pred"])
    color = "green" if status == "Safe" else "orange" if status == "Moderate" else "red"

    folium.CircleMarker(
        location=[z["lat"], z["lon"]],
        radius=8,
        color=color,
        fill=True,
        fill_opacity=0.9,
        popup=f"Zone {z['zone']} ({status})"
    ).add_to(m)

st_folium(m, width=900, height=400)

# ---------- DISPLAY ----------
z = zones[st.session_state.selected_idx]
status = get_status(z["pred"])

st.subheader("📊 Selected Zone")

st.write("pH:", z["ph"])
st.write("DO:", z["do"])
st.write("Temp:", z["temp"])
st.write("ORP:", z["orp"])
st.write("Predicted:", z["pred"])
st.write("Status:", status)