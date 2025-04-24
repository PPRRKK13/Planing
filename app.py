import streamlit as st
import pandas as pd
import os
import altair as alt
from datetime import datetime, timedelta

# --- CONFIG ---
EXCEL_FILE = "For Phyton.xlsx"

# --- FUNCTIONS ---
@st.cache_data
def load_data():
    xls = pd.ExcelFile(EXCEL_FILE)
    table_df = xls.parse("Table")
    item_df = xls.parse("Item Sizes per meter")
    hours_df = xls.parse("Hours per day")
    speed_df = xls.parse("Manufacturing speed")
    holiday_df = xls.parse("Holidays")
    holiday_df["Date"] = pd.to_datetime(holiday_df["Date"])
    return table_df, item_df, hours_df, speed_df, holiday_df,

@st.cache_data
def get_available_items(table_df):
    return sorted(table_df['Batch'].unique())

def calculate_production(selected_items, meter_inputs, table_df, item_df, hours_df, speed_df, availability):
    q1_yield = (
        table_df[table_df['Quality'] == 'Q1']
        .groupby('Batch')['Volume [m3]']
        .sum()
        / table_df.groupby('Batch')['Volume [m3]'].sum()
    ).fillna(0)

    item_m3_per_meter = item_df.set_index('Batch')['M3'].to_dict()
    speed_m_per_min = speed_df.iloc[0]['Speed']

    results = []
    for item in selected_items:
        input_meters = meter_inputs.get(item, 0)
        yield_percent = q1_yield.get(item, 1)
        adjusted_meters = input_meters / yield_percent if yield_percent > 0 else 0
        m3_needed = adjusted_meters * item_m3_per_meter.get(item, 0)
        minutes_needed = adjusted_meters / speed_m_per_min if speed_m_per_min else 0
        hours_needed = minutes_needed / 60
        hours_needed_adjusted = hours_needed / (availability / 100)

        results.append({
            "Item": item,
            "Input Meters": input_meters,
            "Q1 Yield %": round(yield_percent * 100, 2),
            "Adjusted Meters": round(adjusted_meters, 2),
            "m3 Needed": round(m3_needed, 2),
            "Hours Needed": round(hours_needed_adjusted, 2)
        })
    return pd.DataFrame(results)

def compute_shift_schedule(total_hours_needed, hours_df, holiday_df):
    schedule = []
    start_date = datetime.strptime("2025-04-21", "%Y-%m-%d")
    total_allocated = 0
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    while total_allocated < total_hours_needed:
        for shift_day in hours_df["Day"].unique():
            for shift_type in ["Day", "Night"]:
                match = hours_df[(hours_df["Day"] == shift_day) & (hours_df["Shift"] == shift_type)]
                if match.empty:
                    continue
                hours = match["Hours"].values[0]
                current_date = start_date + timedelta(days=day_names.index(shift_day))

                # Skip if it's a holiday
                if current_date.date() in holiday_df["Date"].dt.date.values:
                    continue

                usable_hours = min(hours, total_hours_needed - total_allocated)
                total_allocated += usable_hours

                schedule.append({
                    "Day": shift_day,
                    "Shift": shift_type,
                    "Date": current_date.date(),
                    "Planned Hours": round(usable_hours, 2)
                })

                if total_allocated >= total_hours_needed:
                    break
            if total_allocated >= total_hours_needed:
                break

        start_date += timedelta(weeks=1)

    return pd.DataFrame(schedule)
# --- STREAMLIT UI ---
st.set_page_config("Production Planner", layout="wide")
st.title("📦 Production Planning Calculator")

# --- CHECK FILE ---
if not os.path.exists(EXCEL_FILE):
    st.error("❌ Excel file 'For Phyton.xlsx' not found. Please upload or ensure it's in the same directory as app.py.")
    st.stop()

# --- LOAD DATA ---
table_df, item_df, hours_df, speed_df, holiday_df = load_data()
availability = st.slider("⏳ Estimated Availability % (Unplanned Stops etc)", 0, 100, 85)

# --- ITEM SELECTION ---
available_items = get_available_items(table_df)
selected_items = st.multiselect("📋 Select Items", options=available_items)

# --- USER INPUTS ---
meter_inputs = {}
if selected_items:
    st.subheader("🧮 Enter Needed Meters for Each Item")
    for item in selected_items:
        meter_inputs[item] = st.number_input(f"Meters needed for {item}", min_value=0.0, value=100.0, step=10.0)

# --- CALCULATE ---
if selected_items:
    df_results = calculate_production(selected_items, meter_inputs, table_df, item_df, hours_df, speed_df, availability)
    st.subheader("📊 Production Summary")
    st.dataframe(df_results)

    total_hours = df_results['Hours Needed'].sum()
    st.markdown(f"### 🕒 Total Estimated Hours: **{round(total_hours, 2)} hrs**")

    # --- SCHEDULE ---
    st.subheader("📅 Shift Calendar")
    calendar_df = compute_shift_schedule(total_hours, hours_df, holiday_df)
    st.dataframe(calendar_df)

    # --- CHART ---
    st.subheader("📈 Meters per Shift")
    calendar_df['Shift Label'] = calendar_df['Date'] + " " + calendar_df['Shift']
    bar_chart = alt.Chart(calendar_df).mark_bar().encode(
        x=alt.X('Shift Label', sort=None, title="Shift"),
        y=alt.Y('Planned Meters', title="Adjusted Meters"),
        color=alt.Color('Shift', legend=None)
    ).properties(width=800, height=400)
    st.altair_chart(bar_chart, use_container_width=True)

    # --- DOWNLOAD ---
    with st.expander("⬇️ Download Results"):
        st.download_button("Download Production Plan (CSV)", df_results.to_csv(index=False), file_name="production_plan.csv")
        st.download_button("Download Shift Calendar (CSV)", calendar_df.to_csv(index=False), file_name="shift_schedule.csv")
