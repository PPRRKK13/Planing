import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Production Planning App", layout="wide")

# 📥 Load Excel Data
@st.cache_data
def load_data():
    xls = pd.ExcelFile("For Phyton.xlsx")
    table_df = xls.parse("Table")
    item_df = xls.parse("Item sizes per meter")
    speed_df = xls.parse("Manufacturing speed")
    hours_df = xls.parse("Hours per day")
    holiday_df = xls.parse("Holidays")
    return table_df, item_df, speed_df, hours_df, holiday_df

# 🔧 Shift Calendar Logic
def generate_shift_calendar(start_date, hours_needed, hours_df, holidays):
    shift_calendar = []
    current_date = pd.to_datetime(start_date)
    remaining_hours = hours_needed

    hours_by_day_shift = (
        hours_df.groupby(['Day', 'Shift'])['Hours'].sum().reset_index()
    )

    holidays = pd.to_datetime(holidays['Date']).dt.date

    while remaining_hours > 0:
        day_name = current_date.strftime("%A")
        for _, row in hours_by_day_shift[hours_by_day_shift['Day'] == day_name].iterrows():
            if current_date.date() not in holidays:
                shift_hours = row['Hours']
                shift_type = row['Shift']
                used_hours = min(remaining_hours, shift_hours)
                shift_calendar.append({
                    "Date": current_date.date(),
                    "Shift": shift_type,
                    "Used Hours": used_hours
                })
                remaining_hours -= used_hours
                if remaining_hours <= 0:
                    break
        current_date += pd.Timedelta(days=1)

    return pd.DataFrame(shift_calendar)

# 🧮 Schedule Calculation
def calculate_schedule(batch, meters_needed, table_df, item_df, speed_df, hours_df, holiday_df):
    # Q1 Yield (% to decimal)
    batch_data = table_df[table_df["Batch"] == batch]
    if batch_data.empty:
        st.error(f"No Q1 data found for batch {batch}")
        return None
    q1_yield = batch_data["Q1 Yield %"].astype(str).str.replace('%', '').astype(float).mean() / 100

    # Adjusted meters
    adjusted_meters = meters_needed / q1_yield

    # M3 per meter
    m3_per_meter = item_df[item_df["Batch"] == batch]["M3"].values[0]
    total_m3 = adjusted_meters * m3_per_meter

    # Speed (meters per hour)
    speed = float(speed_df.iloc[0][0])
    hours_needed = adjusted_meters / speed

    # Shift calendar
    shift_df = generate_shift_calendar(start_date, hours_needed, hours_df, holiday_df)

    # Summary Table
    summary = pd.DataFrame({
        "Batch": [batch],
        "Requested Meters": [meters_needed],
        "Q1 Yield Avg": [round(q1_yield * 100, 2)],
        "Adjusted Meters": [round(adjusted_meters, 2)],
        "Total M3": [round(total_m3, 2)],
        "Hours Needed": [round(hours_needed, 2)]
    })

    return summary, shift_df

# 🖥️ Interface
st.title("📦 Production Planning App (Q1 Based)")

# Load data
table_df, item_df, speed_df, hours_df, holiday_df = load_data()

# Batch selection
batches = sorted(table_df["Batch"].unique())
selected_batch = st.selectbox("Select a Batch", batches)

# Meter input
meters_input = st.number_input("Enter Meters to Produce", min_value=1, value=100)

# Start date
start_date = st.date_input("Select Start Date", datetime.date.today())

if st.button("Calculate Schedule"):
    summary_df, schedule_df = calculate_schedule(
        selected_batch, meters_input, table_df, item_df, speed_df, hours_df, holiday_df
    )

    if summary_df is not None:
        st.subheader("📊 Production Summary")
        st.dataframe(summary_df)

        st.subheader("📅 Shift Calendar")
        st.dataframe(schedule_df)

        csv = schedule_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Shift Schedule as CSV", csv, "shift_schedule.csv", "text/
