# backend/dashboard_app.py
import streamlit as st

# ---------------- STREAMLIT CONFIG ---------------- #
st.set_page_config(
    page_title="🌧️ Rainfall Monitoring Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- APP START ---------------- #
st.write("✅ Streamlit app loaded successfully")

# ---------------- SIDEBAR MENU ---------------- #
st.sidebar.title("📊 Dashboard Options")
menu = st.sidebar.radio(
    "Select View",
    ["Values & Calculations", "Predicted Map", "Realtime Map"]
)

# ---------------- 1. VALUES TAB ---------------- #
if menu == "Values & Calculations":
    st.success("📊 Values tab is displaying correctly")
    st.title("📈 Placeholder for Values & Calculations")
    st.write("This is where metrics will appear.")

# ---------------- 2. PREDICTED MAP TAB ---------------- #
elif menu == "Predicted Map":
    st.success("🗺️ Predicted Map tab is displaying correctly")
    st.title("🗺️ Placeholder for Predicted Map")
    st.write("This is where the folium map will appear.")

# ---------------- 3. REALTIME MAP TAB ---------------- #
elif menu == "Realtime Map":
    st.success("⏱️ Realtime Map tab is displaying correctly")
    st.title("⏱️ Placeholder for Realtime Map")
    st.write("This is where the realtime map will appear.")
