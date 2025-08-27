# backend/dashboard_app.py
import streamlit as st
import os
import json
from streamlit.components.v1 import html

# ---------------- STREAMLIT CONFIG ---------------- #
st.set_page_config(
    page_title="Rainfall Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- APP START ---------------- #
st.write("✅ Streamlit app loaded successfully")

# ---------------- SIDEBAR MENU ---------------- #
st.sidebar.title("📌 Dashboard Options")
menu = st.sidebar.radio(
    "Select View",
    ["Values & Calculations", "Predicted Map", "Realtime Map"]
)

# ---------------- 1. VALUES TAB ---------------- #
if menu == "Values & Calculations":
    st.success("Values tab is displaying correctly")
    st.title("📊 Model Metrics & Calculations")

    METRICS_PATH = os.path.join("backend", "model", "metrics.json")

    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)

        col1, col2, col3 = st.columns(3)
        col1.metric("RMSE", f"{metrics.get('rmse', 0):.2f}")
        col2.metric("MAE", f"{metrics.get('mae', 0):.2f}")
        col3.metric("R² Score", f"{metrics.get('r2', 0):.2f}")
    else:
        st.warning("⚠️ metrics.json not found. Please run training first.")

# ---------------- 2. PREDICTED MAP TAB ---------------- #
elif menu == "Predicted Map":
    st.success("Predicted Map tab is displaying correctly")
    st.title("🗺️ Predicted Rainfall Map")

    PREDICTED_MAP_PATH = os.path.join("static", "folium_dataset.html")

    if os.path.exists(PREDICTED_MAP_PATH):
        with open(PREDICTED_MAP_PATH, "r", encoding="utf-8") as f:
            folium_map = f.read()
        html(folium_map, height=600)
    else:
        st.warning("⚠️ Predicted map not found. Run prediction first.")

# ---------------- 3. REALTIME MAP TAB ---------------- #
elif menu == "Realtime Map":
    st.success("Realtime Map tab is displaying correctly")
    st.title("🌍 Realtime Rainfall Map")

    REALTIME_MAP_PATH = os.path.join("static", "folium_realtime.html")

    if os.path.exists(REALTIME_MAP_PATH):
        with open(REALTIME_MAP_PATH, "r", encoding="utf-8") as f:
            folium_map = f.read()
        html(folium_map, height=600)
    else:
        st.warning("⚠️ Realtime map not found. Run realtime collector first.")
