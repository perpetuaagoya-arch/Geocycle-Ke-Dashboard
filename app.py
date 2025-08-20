import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import folium
from folium.plugins import MarkerCluster, HeatMap, MiniMap, Fullscreen, MeasureControl, Search
from streamlit_folium import st_folium
from html import escape as H

st.set_page_config(page_title="GeoCycle KE – Eldoret Waste Decision Support", layout="wide")

DEFAULT_CSV = os.environ.get("GEOCYCLE_CSV", "%CSV_DEFAULT_PATH%")

def load_data():
    if os.path.exists(DEFAULT_CSV):
        return pd.read_csv(DEFAULT_CSV)
    uploaded = st.sidebar.file_uploader("Upload the cleaned CSV", type=["csv"])
    if uploaded is not None:
        return pd.read_csv(uploaded)
    st.warning("Please upload the cleaned CSV to continue.")
    st.stop()

df = load_data()

for col in ["Latitude", "Longitude"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Latitude", "Longitude"])
df = df[(df["Latitude"].between(-90, 90)) & (df["Longitude"].between(-180, 180))]

expected_cols = [
    "Dumpsite Name","Ward","Latitude","Longitude","Waste Types",
    "Waste Management Actors","Reasons for Dumping","Proposed Interventions",
    "Community Interventions","Health & Burning Issues","Sources of Waste",
    "Size of Dumpsite","Frequency of Dumping","Status (Active/Inactive)",
    "Photo URL","_WasteCategory","_Alert","_ReasonsNormalized","_InterventionsNormalized"
]
missing = [c for c in expected_cols if c not in df.columns]
if missing:
    st.error("Your CSV is missing required columns: " + ", ".join(missing))
    st.stop()

st.sidebar.header("Filters")
wards = sorted([w for w in df["Ward"].dropna().unique()])
ward_sel = st.sidebar.multiselect("Ward", wards, default=wards)

status_vals = sorted([s for s in df["Status (Active/Inactive)"].dropna().unique()])
status_sel = st.sidebar.multiselect("Status", status_vals, default=status_vals)

alert_map = {"All": None, "Alert only": True, "Non-alert only": False}
alert_choice = st.sidebar.radio("Health/Burning Alert", list(alert_map.keys()), index=0)

wtypes_all = sorted([w for w in df["Waste Types"].fillna("").str.split(",").explode().str.strip().replace("", np.nan).dropna().unique()])
wtypes_sel = st.sidebar.multiselect("Waste Types (any of)", wtypes_all, default=[])

f = df.copy()
f = f[f["Ward"].isin(ward_sel)] if ward_sel else f
f = f[f["Status (Active/Inactive)"].isin(status_sel)] if status_sel else f

if alert_map[alert_choice] is True:
    f = f[f["_Alert"].astype(str).str.lower().isin(["1","true","yes"])]
elif alert_map[alert_choice] is False:
    f = f[~f["_Alert"].astype(str).str.lower().isin(["1","true","yes"])]

if wtypes_sel:
    import re
    patt = "|".join([rf"\b{re.escape(p)}\b" for p in wtypes_sel])
    f = f[f["Waste Types"].str.contains(patt, case=False, na=False)]

st.sidebar.markdown("---")
st.sidebar.write("**Sites after filters:**", len(f))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total dumpsites", len(df))
col2.metric("Visible (filtered)", len(f))
col3.metric("Alert sites", int(f["_Alert"].astype(str).str.lower().isin(["1","true","yes"]).sum()))
col4.metric("Wards covered", f["Ward"].replace({"": np.nan}).dropna().nunique())

c1, c2 = st.columns(2)
with c1:
    vc = (f["Waste Types"].fillna("")
          .str.split(",").explode().str.strip().replace("", np.nan).dropna())
    waste_counts = vc.value_counts().reset_index()
    waste_counts.columns = ["Waste Type", "Count"]
    if not waste_counts.empty:
        fig = px.bar(waste_counts, x="Waste Type", y="Count", title="Waste Types (count of mentions)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No waste type data to chart for current filters.")

with c2:
    status_counts = f["Status (Active/Inactive)"].fillna("Unknown").value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    fig2 = px.pie(status_counts, values="Count", names="Status", title="Status distribution")
    st.plotly_chart(fig2, use_container_width=True)

def is_http_url(u):
    return isinstance(u, str) and u.lower().startswith(("http://","https://"))

def popup_html(row):
    photo = str(row.get("Photo URL",""))
    hero = f"<img src='{H(photo)}' style='max-width:100%;border-radius:10px;margin-bottom:10px;'/>" if is_http_url(photo) else ""
    name = H(str(row.get("Dumpsite Name","Unnamed")).strip() or "Unnamed")
    ward = H(str(row.get("Ward","—")).strip() or "—")
    lat  = str(row.get("Latitude",""))
    lon  = str(row.get("Longitude",""))
    gmaps = f'<a href="https://maps.google.com/?q={lat},{lon}" target="_blank">Open in Google Maps</a>' if (lat and lon) else "—"

    def cell(label, key):
        v = str(row.get(key,"")).strip()
        if key == "Photo URL" and is_http_url(v):
            v_html = f'<a href="{H(v)}" target="_blank">{H(v)}</a>'
        else:
            v_html = H(v if v else "—")
        return f"<tr><th style='text-align:left;padding:4px 8px;color:#333;'>{H(label)}</th><td style='padding:4px 8px;'>{v_html}</td></tr>"

    core = ''.join([
        cell("Status (Active/Inactive)", "Status (Active/Inactive)"),
        cell("Size of Dumpsite","Size of Dumpsite"),
        cell("Frequency of Dumping","Frequency of Dumping"),
        cell("Ward","Ward"),
        cell("Waste Types","Waste Types"),
        cell("Waste Management Actors","Waste Management Actors"),
        cell("Sources of Waste","Sources of Waste"),
        cell("Reasons for Dumping","Reasons for Dumping"),
        cell("Proposed Interventions","Proposed Interventions"),
        cell("Community Interventions","Community Interventions"),
        cell("Health & Burning Issues","Health & Burning Issues"),
        cell("Photo URL","Photo URL"),
        f"<tr><th style='text-align:left;padding:4px 8px;color:#333;'>Map Link</th><td style='padding:4px 8px;'>{gmaps}</td></tr>"
    ])
    html = f'''
    <div style="max-width:420px">
      {hero}
      <div style="font-size:16px;font-weight:700;margin:4px 0 2px 0;">{name}</div>
      <div style="font-size:12px;color:#444;margin-bottom:8px;">Ward: {ward}</div>
      <table style="border-collapse:collapse;width:100%;font-size:12px;">{core}</table>
    </div>
    '''
    return folium.Popup(folium.IFrame(html=html, width=440, height=520), max_width=460)

st.subheader("Interactive Map")

if f.empty:
    st.info("No sites match the current filters.")
else:
    lat_center = f["Latitude"].mean()
    lon_center = f["Longitude"].mean()
    m = folium.Map(location=[lat_center, lon_center], zoom_start=12, control_scale=True)

    points_group = folium.FeatureGroup(name="Dumpsite Points", show=True).add_to(m)
    cluster = MarkerCluster(name="Clusters").add_to(points_group)

    for _, r in f.iterrows():
        try:
            lat, lon = float(r["Latitude"]), float(r["Longitude"])
        except:
            continue
        alert = str(r.get("_Alert","")).lower() in ("1","true","yes")
        color = "#d73027" if alert else "#2ca25f"
        folium.CircleMarker(
            location=[lat, lon],
            radius=8 if alert else 7,
            color=color, fill=True, fill_opacity=0.85, weight=2,
            tooltip=f"{r.get('Dumpsite Name','Unnamed')}",
            popup=popup_html(r)
        ).add_to(cluster)

    heat_group = folium.FeatureGroup(name="Density Heatmap", show=False).add_to(m)
    heat_points = []
    for _, r in f.iterrows():
        try:
            lat, lon = float(r["Latitude"]), float(r["Longitude"])
        except:
            continue
        alert = str(r.get("_Alert","")).lower() in ("1","true","yes")
        weight = 2.0 if alert else 1.0
        heat_points.append([lat, lon, weight])
    if heat_points:
        HeatMap(heat_points, radius=20, blur=15, max_zoom=16).add_to(heat_group)

    features = []
    for _, r in f.iterrows():
        try:
            lat, lon = float(r["Latitude"]), float(r["Longitude"])
        except:
            continue
        props = { "Dumpsite Name": str(r.get("Dumpsite Name","Unnamed")) }
        features.append({ "type":"Feature",
                          "properties": props,
                          "geometry":{"type":"Point","coordinates":[lon,lat]} })
    gj = folium.GeoJson({ "type":"FeatureCollection", "features": features },
                        name="Search Index").add_to(m)
    Search(layer=gj, search_label="Dumpsite Name", placeholder="Search dumpsite…",
           collapsed=False).add_to(m)

    MiniMap(toggle_display=True).add_to(m)
    Fullscreen().add_to(m)
    m.add_child(MeasureControl(primary_length_unit='kilometers'))
    folium.LayerControl(collapsed=False).add_to(m)

    legend_html = """<div style="position: fixed; bottom: 20px; left: 20px; z-index:9999;
 background: rgba(255,255,255,0.9); padding: 8px 10px; border: 1px solid #ccc; border-radius: 8px; font-size:12px;">
  <div style="font-weight:600; margin-bottom:6px;">Legend</div>
  <div><span style="display:inline-block;width:12px;height:12px;background:#d73027;border:1px solid #999;margin-right:6px;"></span>Alert (health/burning)</div>
  <div><span style="display:inline-block;width:12px;height:12px;background:#2ca25f;border:1px solid #999;margin-right:6px;"></span>Normal</div>
  <div style="margin-top:6px;color:#666;">Toggle “Density Heatmap” in the layer control.</div>
</div>
"""
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=None, height=620)

st.markdown("---")
st.caption("Open-source geospatial decision-support • Built with Streamlit, Folium, and Plotly • Data: Eldoret dumpsite survey")