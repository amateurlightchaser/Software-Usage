# Software-Usage

A Streamlit web app to analyze monthly software usage from a system-generated `.xlsx` export.

## Features
- Upload an Excel file (`.xlsx`) directly in the browser
- Auto-detect likely columns for date, software name, and usage value
- Interactive charting similar to BI dashboards:
  - Overall usage share (donut chart)
  - Monthly usage trend (stacked area)
  - A series of monthly pie charts

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501`.

## Expected input
The app can adapt to many column names, but ideally your file includes:
- A date/month column (e.g., `date`, `month`, `period`)
- A software column (e.g., `software`, `application`, `app_name`)
- A numeric usage column (e.g., `usage_hours`, `usage_count`)

If no numeric usage column is selected, each row is counted as one usage event.
