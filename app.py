import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Production Planning", layout="wide")

# --- Load data ---
@st.cache_data
def load_data(file_path="For Phyton.xlsx"):
    if not os.path.exists(file_path):
        st.error("❌ Excel file not found. Make sure it's named 'For Phyton.xlsx' and in the same folder.")
        st.stop()

    xls = pd.ExcelFile(file_path)
    table_df = xls.parse("Table")
    item_df = xls.parse("Item sizes per meter")
    speed_df = xls.parse("Speed")
    hours_df = xls.parse("Hours per day")
    holiday_df = xls.parse("Holidays")

    holiday_df['Date'] = pd.to_datetime(holiday_df['Date'])

    return table_df, item_df, speed_df, hours_df, holiday_df

# --- Load everything ---
table_df, item_df, speed_df, hours_df, holiday_df = load_data()

# --- User input ---
st.title("🛠️ Production Planning with Shift Calendar")

start_date = st.date_input("📅 Select production start date", value=datetime.today())
availability = st.slider("🕒 Availability %", min_value=10, max_value=100, value=100, step=10)

# --- Processing ---
def calculate_schedule(table_df, item_df, speed_df, hours_df, holiday_df, start_date, availability):
    # Prepare references
    item_m3_per_meter = item_df.set_index("Batch")["M3"].to_dict()
    speed_m_per_min = speed_df.iloc[0]["Speed"]  # Assuming one row
    total_available_per_shift = hours_df.set_index("Shift")["Hours"].to_dict()
    holidays = set(holiday_df['Date'])

    # Convert percentages
    availability_factor = availability / 100

    # Prepare task list
    tasks = []
    for _, row in table_df.iterrows():
        item = row["Item"]
        size = row["Size"]
        batch = row["Batch"]
        meters = row["Meters"]

        m3_per_meter = item_m3_per_meter.get(batch, 0)
        total_m3 = meters * m3_per_meter
        time_required_hrs = (meters / speed_m_per_min) / 60  # meters / m/min = minutes

        tasks.append({
            "Item": item,
            "Size": size,
            "Batch": batch,
            "Meters": meters,
            "Hours Needed": time_required_hrs
        })

    # Schedule
    current_date = pd.to_datetime(start_date)
    schedule = []

    for task in tasks:
        hours_remaining = task["Hours Needed"]

        while hours_remaining > 0:
            if current_date in holidays:
                current_date += timedelta(days=1)
                continue

            for shift in ["Day", "Night"]:
                if hours_remaining <= 0:
                    break

                hours_available = total_available_per_shift.get(shift, 0) * availability_factor
                hours_used = min(hours_remaining, hours_available)

                schedule.append({
                    "Date": current_date.date(),
                    "Shift": shift,
                    "Item": task["Item"],
                    "Batch": task["Batch"],
                    "Meters": task["Meters"],
                    "Hours Used": round(hours_used, 2)
                })

                hours_remaining -= hours_used

            current_date += timedelta(days=1)

    return pd.DataFrame(schedule)

# --- Run calculation ---
if st.button("📊 Generate Schedule"):
    result_df = calculate_schedule(table_df, item_df, speed_df, hours_df, holiday_df, start_date, availability)
    st.success("✅ Schedule generated successfully!")
    st.dataframe(result_df)

    # Optional download
    csv = result_df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download Schedule CSV", csv, "schedule.csv", "text/csv")
