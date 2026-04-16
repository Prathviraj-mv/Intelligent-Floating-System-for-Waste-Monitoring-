import streamlit as st
import random
import folium
from streamlit_folium import st_folium

# ---------- PAGE ----------
st.set_page_config(page_title="River Monitoring", layout="wide")
st.title("💧 River Pollution Monitoring System")

# ---------- FUNCTIONS ----------
def classify(z):
    if z['tds'] > 700:
        return "Severely Polluted"
    elif z['tds'] > 500 or z['ph'] < 6.5 or z['ph'] > 8.5:
        return "Polluted"
    else:
        return "Safe"

def get_color(z):
    status = classify(z)
    if status == "Severely Polluted":
        return "red"
    elif status == "Polluted":
        return "orange"
    return "green"

def generate_zones():
    points = [
        (28.72, 77.24),
        (28.70, 77.235),
        (28.68, 77.23),
        (28.66, 77.225),
        (28.64, 77.22),
        (28.62, 77.215),
        (28.60, 77.22),
        (28.58, 77.225)
    ]

    zones = []
    for i, (lat, lon) in enumerate(points):
        zones.append({
            "zone": chr(65+i),
            "distance": f"{i}-{i+1} km",
            "lat": lat,
            "lon": lon,
            "ph": round(random.uniform(6.0, 9.0), 2),
            "tds": random.randint(100, 900)
        })
    return zones

# ---------- SESSION ----------
if "zones" not in st.session_state:
    st.session_state.zones = generate_zones()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

zones = st.session_state.zones

# ---------- SIDEBAR ----------
st.sidebar.title("📍 Zone Navigation")

zone_names = [f"Zone {z['zone']} ({z['distance']})" for z in zones]
selected_name = st.sidebar.radio("Select Zone:", zone_names)

selected_zone = zones[zone_names.index(selected_name)]

if st.sidebar.button("🔄 Refresh Data"):
    st.session_state.zones = generate_zones()
    st.rerun()

# ---------- MAP ----------
st.subheader("🗺️ Monitoring Map")

center = [zones[len(zones)//2]["lat"], zones[len(zones)//2]["lon"]]
m = folium.Map(location=center, zoom_start=13)

for z in zones:
    folium.CircleMarker(
        location=[z["lat"], z["lon"]],
        radius=8,
        color=get_color(z),
        fill=True,
        fill_opacity=0.9,
        popup=f"Zone {z['zone']} | TDS: {z['tds']} | pH: {z['ph']} | {classify(z)}"
    ).add_to(m)

st_folium(m, width=900, height=500)

# ---------- DETAILS ----------
st.subheader("📊 Selected Zone")

col1, col2 = st.columns(2)

col1.metric("Zone", selected_zone['zone'])
col1.metric("Distance", selected_zone['distance'])

col2.metric("pH", selected_zone['ph'])
col2.metric("TDS", selected_zone['tds'])

status = classify(selected_zone)

if status != "Safe":
    st.error(f"🚨 {status}")
else:
    st.success("✅ Safe")

# ---------- CHAT BUTTON ----------
if st.button("💬 Open Chatbot"):
    st.session_state.chat_open = not st.session_state.chat_open

# ---------- CHATBOT ----------
if st.session_state.chat_open:

    st.subheader("🤖 Assistant")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Ask about water quality...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        p = prompt.lower()

        response = "Try asking about pH, TDS, or zone status."

        # ---------- pH ONLY ----------
        if "ph" in p:
            found = False
            for z in zones:
                if f"zone {z['zone'].lower()}" in p:
                    response = f"Zone {z['zone']} pH: {z['ph']}"
                    found = True
                    break
            if not found:
                avg_ph = round(sum(z['ph'] for z in zones) / len(zones), 2)
                response = f"Average pH: {avg_ph}"

        # ---------- TDS ONLY ----------
        elif "tds" in p:
            found = False
            for z in zones:
                if f"zone {z['zone'].lower()}" in p:
                    response = f"Zone {z['zone']} TDS: {z['tds']} ppm"
                    found = True
                    break
            if not found:
                avg_tds = int(sum(z['tds'] for z in zones) / len(zones))
                response = f"Average TDS: {avg_tds} ppm"

        # ---------- STATUS ----------
        elif "status" in p or "polluted" in p or "safe" in p:
            for z in zones:
                if f"zone {z['zone'].lower()}" in p:
                    response = f"Zone {z['zone']} is {classify(z)}"
                    break

        # ---------- DRINKABILITY ----------
        elif "drink" in p:
            unsafe = any(classify(z) != "Safe" for z in zones)
            if unsafe:
                response = "🚨 Water is NOT safe for drinking."
            else:
                response = "✅ Water is safe for drinking."

        # ---------- WORST ----------
        elif "worst" in p:
            worst = max(zones, key=lambda x: x['tds'])
            response = f"Zone {worst['zone']} is most polluted."

        # ---------- BEST ----------
        elif "best" in p:
            best = min(zones, key=lambda x: x['tds'])
            response = f"Zone {best['zone']} is cleanest."

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun(

        )