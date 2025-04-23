import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

@st.cache_data
def load_data():
    file_path = "For Phyton.xlsx"
    if not os.path.exists(file_path):
        st.error("❌ Excel file 'For Phyton.xlsx' not found. Please ensure it's in the same directory.")
        st.stop()

    xls = pd.ExcelFile(file_path)
    table_df = xls.parse("Table")
    item_df = xls.parse("Item sizes per meter")
    speed_df = xls.parse("Machine speed")
    hours_df = xls.parse("Shift hours")
    holiday_df = xls.parse("Holidays")
    
    # Convert Holiday Date column to datetime
    holiday_df["Date"] = pd.to_datetime(holiday_df["Date"])
    
    return table_df, item_df, speed_df, hours_df, holiday_df

@st.cache_data
def calculate_schedule(table_df, item_df, speed_df, hours_df, holiday_df, start_date, availability):
    item_m3_per_meter = item_df.set_index("Batch")["M3"].to_dict()
    speed_m_per_min = speed_df.iloc[0]["Speed"]
    daily_hours = hours_df.iloc[0]["Hours"]
    minutes_per_day = daily_hours * 60

    results = []

    current_date = pd.to_datetime(start_date)
    holidays = set(holiday_df["Date"])

    for _, row in table_df.iterrows():
        batch = row["Batch"]
        volume_m3 = row["Volume [m3]"]

        # Skip if item not available
        if batch not in availability:
            continue

        m3_per_meter = item_m3_per_meter.get(batch, 1)
        meters_needed = volume_m3 / m3_per_meter
        total_minutes = meters_needed / speed_m_per_min
        days_needed = int(total_minutes // minutes_per_day) + 1

        for _ in range(days_needed):
            while current_date in holidays or current_date.weekday() >= 5:  # Skip weekends/holidays
                current_date += timedelta(days=1)

            results.append({
                "Date": current_date.date(),
                "Batch": batch,
                "Planned Volume [m3]": min(volume_m3, m3_per_meter * speed_m_per_min * minutes_per_day)
            })

            volume_m3 -= m3_per_meter * speed_m_per_min * minutes_per_day
            current_date += timedelta(days=1)

    return pd.DataFrame(results)

# Load the data
table_df, item_df, speed_df, hours_df, holiday_df = load_data()

# Batch selector
available_batches = sorted(table_df["Batch"].unique())
selected_batches = st.multiselect("✅ Select batches to schedule", available_batches, default=available_batches)

# Start date
start_date = st.date_input("📅 Select production start date", datetime.today())

# Schedule button
if st.button("📊 Generate Schedule"):
    with st.spinner("Calculating production schedule..."):
        result_df = calculate_schedule(
            table_df[table_df["Batch"].isin(selected_batches)],
            item_df,
            speed_df,
            hours_df,
            holiday_df,
            start_date,
            selected_batches
        )

        st.success("✅ Schedule generated!")
        st.dataframe(result_df)

       csv = result_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Schedule CSV", csv, "production_schedule.csv", "text/csv")
