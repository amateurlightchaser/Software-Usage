from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Monthly Software Usage Analysis", layout="wide")


def normalize_columns(columns: list[str]) -> list[str]:
    return [str(col).strip().lower().replace(" ", "_") for col in columns]


def infer_date_column(df: pd.DataFrame) -> Optional[str]:
    keyword_matches = [
        col
        for col in df.columns
        if any(keyword in col for keyword in ["date", "month", "period", "time"])
    ]
    if keyword_matches:
        return keyword_matches[0]

    for col in df.columns:
        converted = pd.to_datetime(df[col], errors="coerce")
        if converted.notna().mean() > 0.7:
            return col
    return None


def infer_software_column(df: pd.DataFrame) -> Optional[str]:
    preferred = ["software", "application", "app", "product", "tool", "name"]
    for key in preferred:
        for col in df.columns:
            if key in col:
                return col

    object_cols = [col for col in df.columns if df[col].dtype == "object"]
    return object_cols[0] if object_cols else None


def infer_usage_column(df: pd.DataFrame, excluded: set[str]) -> Optional[str]:
    preferred = ["usage", "hours", "count", "duration", "time", "qty", "quantity"]
    for key in preferred:
        for col in df.columns:
            if col in excluded:
                continue
            if key in col and pd.api.types.is_numeric_dtype(df[col]):
                return col

    numeric_cols = [
        col
        for col in df.columns
        if pd.api.types.is_numeric_dtype(df[col]) and col not in excluded
    ]
    return numeric_cols[0] if numeric_cols else None


def prepare_data(raw_df: pd.DataFrame, date_col: str, software_col: str, usage_col: Optional[str]) -> pd.DataFrame:
    df = raw_df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, software_col])

    if usage_col:
        df[usage_col] = pd.to_numeric(df[usage_col], errors="coerce").fillna(0)
    else:
        usage_col = "usage_count"
        df[usage_col] = 1

    df["month"] = df[date_col].dt.to_period("M").astype(str)
    return df[["month", software_col, usage_col]].rename(
        columns={software_col: "software", usage_col: "usage"}
    )


def draw_dashboard(usage_df: pd.DataFrame) -> None:
    monthly_usage = usage_df.groupby(["month", "software"], as_index=False)["usage"].sum()
    overall_usage = usage_df.groupby("software", as_index=False)["usage"].sum().sort_values("usage", ascending=False)

    st.subheader("Usage Overview")
    left, right = st.columns([1, 1])

    with left:
        pie = px.pie(
            overall_usage,
            names="software",
            values="usage",
            title="Overall Software Usage Share",
            hole=0.35,
        )
        st.plotly_chart(pie, use_container_width=True)

    with right:
        trend = px.area(
            monthly_usage,
            x="month",
            y="usage",
            color="software",
            title="Monthly Usage Trend by Software",
        )
        trend.update_xaxes(type="category")
        st.plotly_chart(trend, use_container_width=True)

    st.subheader("Monthly Pie Charts")
    months = sorted(monthly_usage["month"].unique())
    if not months:
        st.warning("No month values found after processing.")
        return

    columns_per_row = 2
    for row_start in range(0, len(months), columns_per_row):
        row_months = months[row_start : row_start + columns_per_row]
        row_columns = st.columns(columns_per_row)
        for idx, month in enumerate(row_months):
            month_data = monthly_usage[monthly_usage["month"] == month]
            fig = px.pie(
                month_data,
                names="software",
                values="usage",
                title=f"{month} Usage Breakdown",
                hole=0.25,
            )
            row_columns[idx].plotly_chart(fig, use_container_width=True)


def main() -> None:
    st.title("📊 Monthly Software Usage Analyzer")
    st.caption(
        "Upload your system-generated XLSX file to automatically analyze software usage by month."
    )

    uploaded_file = st.file_uploader("Upload XLSX file", type=["xlsx"])
    if not uploaded_file:
        st.info("Upload an Excel file to begin analysis.")
        return

    xls = pd.ExcelFile(uploaded_file)
    sheet_name = st.selectbox("Select worksheet", xls.sheet_names)
    raw_df = xls.parse(sheet_name=sheet_name)

    if raw_df.empty:
        st.error("The selected sheet is empty.")
        return

    raw_df.columns = normalize_columns(list(raw_df.columns))

    st.subheader("Raw Data Preview")
    st.dataframe(raw_df.head(20), use_container_width=True)

    inferred_date = infer_date_column(raw_df)
    inferred_software = infer_software_column(raw_df)
    inferred_usage = infer_usage_column(raw_df, excluded={col for col in [inferred_date, inferred_software] if col})

    st.subheader("Column Mapping")
    all_columns = list(raw_df.columns)
    date_col = st.selectbox("Date / Month column", all_columns, index=all_columns.index(inferred_date) if inferred_date in all_columns else 0)
    software_col = st.selectbox(
        "Software name column",
        all_columns,
        index=all_columns.index(inferred_software) if inferred_software in all_columns else 0,
    )
    usage_options = ["(Count each row as 1 usage)"] + all_columns
    default_usage_index = usage_options.index(inferred_usage) if inferred_usage in usage_options else 0
    usage_selection = st.selectbox("Usage value column", usage_options, index=default_usage_index)
    usage_col = None if usage_selection == "(Count each row as 1 usage)" else usage_selection

    prepared_df = prepare_data(raw_df, date_col=date_col, software_col=software_col, usage_col=usage_col)

    if prepared_df.empty:
        st.error("No valid rows found after parsing date/software columns.")
        return

    total_usage = prepared_df["usage"].sum()
    total_software = prepared_df["software"].nunique()
    total_months = prepared_df["month"].nunique()

    metrics = st.columns(3)
    metrics[0].metric("Total Usage", f"{total_usage:,.2f}" if isinstance(total_usage, float) else f"{total_usage:,}")
    metrics[1].metric("Unique Software", total_software)
    metrics[2].metric("Months Covered", total_months)

    draw_dashboard(prepared_df)


if __name__ == "__main__":
    main()
