import streamlit as st
import pandas as pd
import numpy as np
import folium
import os
from streamlit_folium import st_folium
from sklearn.linear_model import LinearRegression

# ---------- PAGE ----------
st.set_page_config(page_title="River Monitoring", layout="wide")
st.title("River Pollution Monitoring System")

# ---------- LOAD DATA ----------
def load_dataset():
    local_path = "ganga.csv"
    full_path = r"C:\Users\Charvi\Desktop\Ganga dataset\ganga.csv"

    if os.path.exists(local_path):
        return pd.read_csv(local_path)
    elif os.path.exists(full_path):
        return pd.read_csv(full_path)
    else:
        st.error("❌ Dataset not found")
        st.stop()

# ---------- MODEL ----------
def load_model():
    df = load_dataset()
    df = df.dropna()

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

# ---------- 1 KM SPACED ZONES ----------
def generate_zones():
    # starting point (on river)
    base_lat = 25.3100
    base_lon = 83.0140

    points = []
    for i in range(8):
        lat = base_lat - (i * 0.009)   # ~1 km step south
        lon = base_lon + (i * 0.001)   # slight river bend
        points.append((lat, lon))

    zones = []
    for i, (lat, lon) in enumerate(points):

        ph = round(7 + np.random.uniform(-0.5, 0.5), 2)
        do = round(9 + np.random.uniform(-2, 2), 2)
        temp = round(25 + np.random.uniform(-3, 3), 2)
        orp = round(300 + np.random.uniform(-50, 50), 2)

        pred = model.predict([[ph, do, temp, orp]])[0]

        zones.append({
            "zone": chr(65+i),
            "lat": lat,
            "lon": lon,
            "ph": ph,
            "do": do,
            "temp": temp,
            "orp": orp,
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
st.subheader("🗺️ River Monitoring Map")

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

map_data = st_folium(m, width=900, height=400, returned_objects=["last_object_clicked"])

# ---------- CLICK ----------
if map_data and map_data["last_object_clicked"]:
    lat = map_data["last_object_clicked"]["lat"]
    lon = map_data["last_object_clicked"]["lng"]

    distances = [
        (i, (z["lat"] - lat)**2 + (z["lon"] - lon)**2)
        for i, z in enumerate(zones)
    ]

    st.session_state.selected_idx = min(distances, key=lambda x: x[1])[0]

# ---------- SELECTED ----------
z = zones[st.session_state.selected_idx]
status = get_status(z["pred"])

st.subheader("📊 Selected Zone")

col1, col2, col3 = st.columns(3)
col1.metric("pH", z["ph"])
col2.metric("DO", z["do"])
col3.metric("Temp", z["temp"])

col4, col5 = st.columns(2)
col4.metric("ORP", z["orp"])
col5.metric("Predicted Conductivity", z["pred"])

st.write("🚦 Water Status:", status)

# ---------- CHATBOT ----------
st.subheader("💬 Assistant")

prompt = st.text_input("Ask something...")

if prompt:
    p = prompt.lower()

    if "ph" in p:
        st.write(f"pH: {z['ph']}")
    elif "do" in p:
        st.write(f"DO: {z['do']}")
    elif "temperature" in p:
        st.write(f"Temperature: {z['temp']}")
    elif "drink" in p:
        st.write("✅ Drinkable" if status == "Safe" else "🚨 Not safe for drinking")
    elif "bath" in p:
        st.write("✅ Suitable for bathing" if status in ["Safe", "Moderate"] else "🚨 Not suitable for bathing")
    elif "pollution" in p or "predict" in p:
        st.write(f"Predicted Conductivity: {z['pred']} ({status})")
    else:
        st.write("Ask about pH, DO, temperature, drinking or bathing suitability.")