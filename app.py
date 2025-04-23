import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Production Scheduler", layout="wide")

# ---- Load data from Excel ----
@st.cache_data
def load_data():
    xls = pd.ExcelFile("production_schedule_template.xlsx")
    table_df = xls.parse("Table")
    item_df = xls.parse("Item Sizes per meter")
    speed_df = xls.parse("Manufacturing speed")
    hours_df = xls.parse("Hours per day")
    holiday_df = xls.parse("Holidays")
    return table_df, item_df, speed_df, hours_df, holiday_df

# ---- Calculate production plan ----
def calculate_schedule(table_df, item_df, speed_df, hours_df, holiday_df, start_date, availability):
    # Merge M3 data into the table
    table_df = table_df.merge(item_df, on="Batch", how="left")

    # Calculate actual M3 needed
    table_df["Total M3"] = table_df["Meters Needed"] * table_df["M3"]

    # Load machine speed
    speed_m_per_min = speed_df.iloc[0]["Speed"]

    # Combine shift hours by weekday and shift
    shift_hours = hours_df.copy()
    shift_hours["Weekday"] = shift_hours["Day"].map({
        "Monday": 0, "Tuesday": 1, "Wednesday": 2,
        "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
    })

    # Convert holiday list to datetime
    holiday_dates = pd.to_datetime(holiday_df["Date"]).dt.date

    results = []

    current_datetime = start_date
    for idx, row in table_df.iterrows():
        batch = row["Batch"]
        meters_needed = row["Meters Needed"]
        m3_per_meter = row["M3"]
        total_m3 = row["Total M3"]

        meters_remaining = meters_needed
        hours_needed = meters_needed / speed_m_per_min / 60  # in hours

        while meters_remaining > 0:
            # Skip holiday
            if current_datetime.date() in holiday_dates:
                current_datetime += timedelta(days=1)
                continue

            weekday = current_datetime.weekday()

            daily_shifts = shift_hours[shift_hours["Weekday"] == weekday]
            for _, shift_row in daily_shifts.iterrows():
                shift = shift_row["Shift"]
                shift_hours_val = shift_row["Hours"]

                meters_this_shift = speed_m_per_min * shift_hours_val * 60
                used_meters = min(meters_remaining, meters_this_shift)
                used_m3 = used_meters * m3_per_meter
                used_hours = used_meters / speed_m_per_min / 60

                results.append({
                    "Batch": batch,
                    "Shift Date": current_datetime.date(),
                    "Shift": shift,
                    "Used Meters": used_meters,
                    "Used M3": used_m3,
                    "Used Hours": used_hours
                })

                meters_remaining -= used_meters

                if meters_remaining <= 0:
                    break
            current_datetime += timedelta(days=1)

    return pd.DataFrame(results)

# ---- Streamlit UI ----
st.title("🛠️ Production Scheduling App")

table_df, item_df, speed_df, hours_df, holiday_df = load_data()

start_date = st.date_input("Select start date for planning", datetime.today())

if st.button("Generate Schedule"):
    with st.spinner("Calculating schedule..."):
        result_df = calculate_schedule(
            table_df, item_df, speed_df, hours_df, holiday_df, start_date, availability=None
        )
        st.success("Schedule generated!")

        # Show preview
        st.dataframe(result_df)

        # Download
        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Schedule CSV", csv, "production_schedule.csv", "text/csv")
