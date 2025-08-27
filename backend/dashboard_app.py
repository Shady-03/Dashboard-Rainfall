# backend/dashboard_app.py
import streamlit as st
import os
import json
from streamlit.components.v1 import html

# ---------------- STREAMLIT CONFIG ---------------- #
st.set_page_config(
    page_title="Rainfall Prediction",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CSS STYLING ---------------- #
st.markdown("""
    <style>
        /* General Styling */
        body {
            font-family: 'Segoe UI', sans-serif;
        }

        /* Card-like containers */
        .stImage > img, iframe {
            border: 2px solid #444;
            border-radius: 12px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
            margin-top: 10px;
            margin-bottom: 20px;
        }

        /* Section Titles */
        h1, h2, h3 {
            font-weight: 700;
            color: #e1e1e1;
        }

        /* Center text for subheaders */
        .subheader {
            text-align: center;
        }

        /* Toast positioning */
        .stToast {
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            z-index: 9999 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- APP START ---------------- #
st.toast("✅ Streamlit app loaded successfully", icon="🌧️")

# ---------------- SIDEBAR MENU ---------------- #
st.sidebar.title("📌 Dashboard Options")
menu = st.sidebar.radio(
    "Select View",
    ["Values & Calculations", "Predicted Map", "Realtime Map", "Graphs"]
)

# ---------------- 1. VALUES TAB ---------------- #
if menu == "Values & Calculations":
    st.title("🌧️ Rainfall Prediction")
    st.header("📊 Model Metrics & Calculations")

    METRICS_PATH = os.path.join("backend", "model", "metrics.json")

    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)

        def to_percent(value):
            try:
                return str(int(round(value * 100)))
            except:
                return str(value)

        # Regression metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("MSE", f"{metrics.get('MSE', 0):.0f}")
        col2.metric("MAE", f"{metrics.get('MAE', 0):.0f}")
        col3.metric("R²", to_percent(metrics.get('R2', 0)))

        st.divider()

        # Classification metrics
        st.subheader("📑 Classification Metrics")
        col4, col5, col6, col7 = st.columns(4)
        col4.metric("Accuracy", to_percent(metrics.get('Accuracy', 0)))
        col5.metric("Precision", to_percent(metrics.get('Precision', 0)))
        col6.metric("Recall", to_percent(metrics.get('Recall', 0)))
        col7.metric("F1-score", to_percent(metrics.get('F1-score', 0)))

    else:
        st.warning("⚠️ metrics.json not found. Please run training first.")

# ---------------- 2. PREDICTED MAP TAB ---------------- #
elif menu == "Predicted Map":
    st.title("🗺️ Predicted Rainfall Map")

    PREDICTED_MAP_PATH = os.path.join("static", "folium_dataset.html")

    if os.path.exists(PREDICTED_MAP_PATH):
        with open(PREDICTED_MAP_PATH, "r", encoding="utf-8") as f:
            folium_map = f.read()
        st.markdown("<div class='map-container'>", unsafe_allow_html=True)
        html(folium_map, height=600)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Predicted map not found. Run prediction first.")

# ---------------- 3. REALTIME MAP TAB ---------------- #
elif menu == "Realtime Map":
    st.title("🌍 Realtime Rainfall Map")

    REALTIME_MAP_PATH = os.path.join("static", "folium_realtime.html")

    if os.path.exists(REALTIME_MAP_PATH):
        with open(REALTIME_MAP_PATH, "r", encoding="utf-8") as f:
            folium_map = f.read()
        st.markdown("<div class='map-container'>", unsafe_allow_html=True)
        html(folium_map, height=600)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Realtime map not found. Run realtime collector first.")

# ---------------- 4. GRAPHS TAB ---------------- #
elif menu == "Graphs":
    st.title("📈 Training & Evaluation Graphs")

    PLOTS_DIR = os.path.join("backend", "model", "plots")

    plots = {
        "Actual vs Predicted": "actual_vs_pred.png",
        "Loss Curve": "loss_curve.png",
        "Confusion Matrix": "confusion_matrix.png"
    }

    for title, filename in plots.items():
        path = os.path.join(PLOTS_DIR, filename)
        if os.path.exists(path):
            st.subheader(title)
            # Center image with width control
            st.image(path, use_container_width=False, width=650)
            st.divider()
        else:
            st.warning(f"⚠️ {filename} not found in {PLOTS_DIR}")
