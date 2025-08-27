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
    ["Values & Calculations", "Predicted Map", "Realtime Map", "Graphs"]
)

# ---------------- 1. VALUES TAB ---------------- #
if menu == "Values & Calculations":
    st.success("Values tab is displaying correctly")
    st.title("📊 Model Metrics & Calculations")

    METRICS_PATH = os.path.join("backend", "model", "metrics.json")

    if os.path.exists(METRICS_PATH):
        with open(METRICS_PATH, "r") as f:
            metrics = json.load(f)

        # Helper function: convert 0.x → xx (percentage style)
        def to_percent(value):
            try:
                return str(int(round(value * 100)))
            except:
                return str(value)

        # --- Show important regression metrics ---
        col1, col2, col3 = st.columns(3)
        col1.metric("MSE", f"{metrics.get('MSE', 0):.0f}")
        col2.metric("MAE", f"{metrics.get('MAE', 0):.0f}")
        col3.metric("R²", to_percent(metrics.get('R2', 0)))

        st.divider()

        # --- Show classification metrics ---
        st.subheader("📑 Classification Metrics")
        col4, col5, col6, col7 = st.columns(4)
        col4.metric("Accuracy", to_percent(metrics.get('Accuracy', 0)))
        col5.metric("Precision", to_percent(metrics.get('Precision', 0)))
        col6.metric("Recall", to_percent(metrics.get('Recall', 0)))
        col7.metric("F1-score", to_percent(metrics.get('F1-score', 0)))

        st.divider()

        # --- Full JSON table (formatted) ---
        st.subheader("📂 Full Metrics Report")
        display_metrics = {}
        for k, v in metrics.items():
            if k in ["MSE", "MAE"]:
                display_metrics[k] = [f"{v:.0f}"]
            else:
                display_metrics[k] = [to_percent(v)]
        st.dataframe(display_metrics, use_container_width=True)

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

# ---------------- 4. GRAPHS TAB ---------------- #
elif menu == "Graphs":
    st.success("Graphs tab is displaying correctly")
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
            st.image(path, use_column_width=True)
            st.divider()
        else:
            st.warning(f"⚠️ {filename} not found in {PLOTS_DIR}")
