# GeoCycle KE – Eldoret Waste Decision-Support Dashboard

An open-source geospatial dashboard that maps dumpsites in Eldoret with photos, names, and decision-ready fields (size, actors, reasons, interventions, health alerts).

## Features
- Clustered **point map** with **photo popups** and **Google Maps** links
- **Density heatmap** toggle for hotspot planning
- Sidebar **filters**: Ward, Status, Alerts, Waste Types
- **Search** by dumpsite name
- Summary **KPIs** and **charts** (Plotly)
- Works with your cleaned CSV

## Local setup
```bash
pip install -r requirements.txt
streamlit run app.py
```
By default the app loads: /mnt/data/GeoCycle_Dashboard_Ready_Final.csv

To use another CSV, set env var:
```bash
export GEOCYCLE_CSV=/path/to/GeoCycle_Dashboard_Ready_Final.csv
streamlit run app.py
```

## Deploy on Streamlit Cloud


1. Create a GitHub repo and add `app.py`, `requirements.txt`, and your CSV (or host it elsewhere).
2. Go to https://streamlit.io/cloud and link the repo.
3. Set an environment variable `GEOCYCLE_CSV` if your CSV is stored privately or at a different path.
4. Deploy. Done.

## Data schema (required columns)
Dumpsite Name, Ward, Latitude, Longitude, Waste Types, Waste Management Actors, Reasons for Dumping, Proposed Interventions, Community Interventions, Health & Burning Issues, Sources of Waste, Size of Dumpsite, Frequency of Dumping, Status (Active/Inactive), Photo URL, _WasteCategory, _Alert, _ReasonsNormalized, _InterventionsNormalized
