# CDC Provisional Natality Dashboard (2025)

An interactive, pedagogical business analytics dashboard built with **Streamlit**, **pandas**, and **Plotly** to explore geographic, monthly, and sex-based patterns in provisional 2025 U.S. live birth counts.

---

## 📊 Project Overview

This dashboard was developed for undergraduate business analytics students to practice exploratory data analysis (EDA), data quality auditing, and dashboard UX design.

### Key Data Disclaimers
1. **Counts vs. Rates**: All figures in this dashboard represent raw **birth counts** (the number of live births recorded), **not population birth rates**. The dataset does not include census population denominators; therefore, differences between states primarily reflect state population sizes rather than fertility behavior.
2. **Provisional Data**: Figures are based on provisional 2025 CDC data, which are subject to continuous reporting updates.
3. **Source Attribution**: Centers for Disease Control and Prevention (CDC) / National Center for Health Statistics (NCHS) - Provisional Natality Data (2025).

---

## 📁 Repository Structure

```
cdc-births-2025/
├── app.py                      # Main Streamlit dashboard application
├── requirements.txt            # Python dependencies (streamlit, pandas, openpyxl, plotly)
├── README.md                   # Project overview and deployment guide
├── .gitignore                  # Git exclusions for Python and OS files
└── data/
    └── Provisional_Natality_2025_CDC.xlsx  # Untouched CDC raw dataset
```

---

## 🚀 Running Locally

1. **Clone or Download the Repository**:
   ```bash
   git clone <your-github-repo-url>
   cd cdc-births-2025
   ```

2. **Create and Activate a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Dashboard**:
   ```bash
   streamlit run app.py
   ```
   Open your browser to `http://localhost:8501`.

---

## ☁️ Deploying to Streamlit Community Cloud

1. Create a public GitHub repository named `cdc-births-2025`.
2. Push all project files (including `app.py`, `requirements.txt`, `README.md`, and the `data/` folder).
3. Navigate to [Streamlit Community Cloud](https://share.streamlit.io/).
4. Click **Create app** > **Deploy a public app from GitHub**.
5. Select your repository, branch (`main`), and set **Main file path** to `app.py`.
6. Click **Deploy!** Your live dashboard will be accessible worldwide in minutes.
