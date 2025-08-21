import os
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import MarkerCluster, HeatMap
import plotly.express as px

# -------------------
# PAGE SETUP
# -------------------
st.set_page_config(page_title="GeoCycle Eldoret Dashboard", layout="wide")
st.title("🌍 GeoCycle Eldoret Dashboard")

# -------------------
# LOAD DATA
# -------------------
csv_path = os.environ.get("GEOCYCLE_CSV", "./data/GeoCycle_Dashboard_Ready_Final.csv")

st.sidebar.header("📂 Data Source")
st.sidebar.write("CSV path:", csv_path)

if not os.path.exists(csv_path):
    st.error("CSV not found! Ensure file is at ./data/GeoCycle_Dashboard_Ready_Final.csv")
    st.stop()

try:
    df = pd.read_csv(csv_path)
except Exception as e:
    st.error(f"Failed to read CSV: {e}")
    st.stop()

st.success(f"Loaded {len(df)} rows and {len(df.columns)} columns from CSV")

# -------------------
# FILTERS (SIDEBAR)
# -------------------
wards = sorted(df["Ward"].dropna().unique())
statuses = sorted(df["Status (Active/Inactive)"].dropna().unique())

ward_filter = st.sidebar.multiselect("Filter by Ward", wards, default=wards)
status_filter = st.sidebar.multiselect("Filter by Status", statuses, default=statuses)
alert_only = st.sidebar.checkbox("🚨 Show only Alert sites (_Alert=True)", value=False)

df_filt = df[df["Ward"].isin(ward_filter) & df["Status (Active/Inactive)"].isin(status_filter)]
if alert_only and "_Alert" in df_filt.columns:
    df_filt = df_filt[df_filt["_Alert"] == True]

# -------------------
# KPIs
# -------------------
col1, col2, col3 = st.columns(3)
col1.metric("Total Sites", len(df))
col2.metric("Visible Sites", len(df_filt))
if "_Alert" in df_filt.columns:
    col3.metric("🚨 Alerts", int(df_filt["_Alert"].sum()))
else:
    col3.metric("🚨 Alerts", 0)

# -------------------
# MAP
# -------------------
st.subheader("🗺️ Map of Dumpsites")

if len(df_filt) == 0:
    st.warning("No sites match filters.")
else:
    m = folium.Map(
        location=[df_filt["Latitude"].mean(), df_filt["Longitude"].mean()],
        zoom_start=12
    )

    mc = MarkerCluster().add_to(m)

    def color_for(cat, alert=False):
        if alert: return "red"
        return {
            "Organic":"green","Plastic":"red","Paper":"orange","Glass":"blue",
            "Metal":"gray","E-waste":"black","Medical":"pink","Construction":"cadetblue",
            "Mixed":"purple","Others":"lightgray","Unknown":"beige"
        }.get(str(cat), "blue")

    for _, r in df_filt.iterrows():
        lat, lon = r["Latitude"], r["Longitude"]
        if pd.isna(lat) or pd.isna(lon): continue
        name = r.get("Dumpsite Name", "Unnamed")
        ward = r.get("Ward", "Unknown")
        photo = r.get("Photo URL", "")
        img = f'<br><img src="{photo}" width="240">' if isinstance(photo,str) and photo.startswith(("http://","https://")) else ""
        popup = (
            f"<b>Dumpsite:</b> {name}"
            f"<br><b>Ward:</b> {ward}"
            f"<br><b>Status:</b> {r.get('Status (Active/Inactive)','')}"
            f"<br><b>Waste Types:</b> {r.get('Waste Types','')}"
            f"<br><b>Actors:</b> {r.get('Waste Management Actors','')}"
            f"<br><b>Sources:</b> {r.get('Sources of Waste','')}"
            f"<br><b>Reasons:</b> {r.get('Reasons for Dumping','')}"
            f"<br><b>Proposed Interventions:</b> {r.get('Proposed Interventions','')}"
            f"<br><b>Community Interventions:</b> {r.get('Community Interventions','')}"
            f"<br><b>Health Issues:</b> {r.get('Health & Burning Issues','')}"
            f"<br><b>Size:</b> {r.get('Size of Dumpsite','')}"
            f"<br><b>Frequency:</b> {r.get('Frequency of Dumping','')}"
            f"{img}"
        )
        folium.Marker(
            [lat, lon],
            popup=popup,
            tooltip=name,
            icon=folium.Icon(
                color=color_for(r.get("_WasteCategory","Unknown"), bool(r.get("_Alert", False))),
                icon="exclamation-sign" if r.get("_Alert", False) else "trash",
                prefix="fa"
            )
        ).add_to(mc)

    # Heatmap toggle
    if st.sidebar.checkbox("Show Heatmap", value=False):
        HeatMap(
            data=df_filt[["Latitude","Longitude"]].dropna().values,
            radius=15, blur=10, min_opacity=0.4
        ).add_to(m)

    st_map = st_folium(m, width=1000, height=600)

# -------------------
# CHARTS
# -------------------
st.subheader("📊 Data Insights")

tab1, tab2 = st.tabs(["Waste Types", "Status"])

with tab1:
    if "Waste Types" in df_filt.columns:
        waste_counts = df_filt["Waste Types"].value_counts().reset_index()
        waste_counts.columns = ["Waste Type", "Count"]
        fig = px.bar(waste_counts, x="Waste Type", y="Count", title="Distribution of Waste Types")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    if "Status (Active/Inactive)" in df_filt.columns:
        status_counts = df_filt["Status (Active/Inactive)"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig2 = px.pie(status_counts, names="Status", values="Count", title="Active vs Inactive Sites")
        st.plotly_chart(fig2, use_container_width=True)

# -------------------
# RAW DATA
# -------------------
with st.expander("📑 View Data Table"):
    st.dataframe(df_filt)
