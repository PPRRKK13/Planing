import streamlit as st
import pandas as pd
from datetime import timedelta

# -------- Load Excel Data --------
@st.cache_data
def load_data():
    xls = pd.ExcelFile("For Phyton.xlsx")
    table_df = xls.parse("Table")
    item_df = xls.parse("Item Sizes per meter")
    speed_df = xls.parse("Manufacturing speed")
    hours_df = xls.parse("Hours per day")
    holiday_df = xls.parse("Holidays")  # Sheet with one column 'Date' in datetime format
    return table_df, item_df, speed_df, hours_df, holiday_df

# -------- Latvian Holidays Helper --------
def is_holiday(date, holidays):
    return date in holidays

# -------- Production Calculation --------
def calculate_schedule(table_df, item_df, speed_df, hours_df, holiday_df, start_date, availability, selected_batches, meter_inputs):
    holidays = set(holiday_df['Date'].dt.date)

    # Map batch to m3 per meter
    m3_map = item_df.set_index("Batch")["M3"].to_dict()
    speed_m_per_min = speed_df.iloc[0]["Speed"]

    # Get hours per shift type
    shift_hours = hours_df.set_index("Type")["Hours"].to_dict()
    hours_per_day = shift_hours.get(availability, 8)
    minutes_per_day = hours_per_day * 60

    schedule = []

    current_date = start_date

    for batch in selected_batches:
        meters = meter_inputs.get(batch, 0)
        m3_per_meter = m3_map.get(batch, 0)
        total_m3 = meters * m3_per_meter
        total_minutes = meters / speed_m_per_min

        while total_minutes > 0:
            # Skip holidays
            if is_holiday(current_date, holidays) or current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            work_minutes = min(total_minutes, minutes_per_day)

            schedule.append({
                "Date": current_date,
                "Batch": batch,
                "Meters": round(work_minutes * speed_m_per_min, 2),
                "M3": round(work_minutes * speed_m_per_min * m3_per_meter, 2),
                "Shift Hours": round(work_minutes / 60, 2),
            })

            total_minutes -= work_minutes
            current_date += timedelta(days=1)

    return pd.DataFrame(schedule)

# -------- Streamlit UI --------
st.set_page_config(page_title="Production Planner", layout="wide")
st.title("📊 Production Schedule Planner")

# Load data
table_df, item_df, speed_df, hours_df, holiday_df = load_data()

# Get list of available batches
available_batches = sorted(table_df["Batch"].unique())
selected_batches = st.multiselect("Select batch(es)", options=available_batches)

# Input meters per selected batch
meter_inputs = {}
if selected_batches:
    for batch in selected_batches:
        meter_inputs[batch] = st.number_input(f"Enter meters for {batch}", min_value=0.0, key=batch)

# Start date input
start_date = st.date_input("Select start date")

# Shift availability
availability = st.selectbox("Select shift availability", ["1 shift", "2 shifts", "3 shifts"])

# Generate Schedule
if st.button("📅 Generate Schedule"):
    if selected_batches and start_date:
        result_df = calculate_schedule(
            table_df, item_df, speed_df, hours_df, holiday_df,
            start_date, availability, selected_batches, meter_inputs
        )
        st.success("✅ Schedule generated!")
        st.dataframe(result_df)

        # Download CSV
        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Schedule CSV", csv, "production_schedule.csv", "text/csv")
    else:
        st.warning("Please select batches and enter a start date.")
