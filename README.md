# Infection Cluster Detection App

A FastAPI web application for uploading hospital transfer & microbiology records, detecting possible infection clusters, and visualizing them interactively.

![screenshot](docs/screenshot.png)

---

## Features

- 📂 **File Upload** – Ingest patient transfer and microbiology CSV files.
- 🧮 **Cluster Detection** – Builds contact networks with `networkx` and groups temporally / spatially related positives.
- 📊 **Cluster Dashboard**
  - Summary statistics (total clusters, infections, patients)
  - Stacked bar chart of infections per ward
  - Per-infection cluster listing
- 🔗 **Cluster Detail** – Shows:
  - Timeline (first/last positive, timespan)
  - Locations
  - Interactive network graph (via [vis-network](https://visjs.org/)) for contact edges
- 📁 **Sample Data** – Quickly explore with the provided `sample_data/` folder.
