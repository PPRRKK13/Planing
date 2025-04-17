import streamlit as st
import pandas as pd

# ==== Embedded Data ====

table_data = [
    {"Batch": "19x75", "Quality": "Q1", "Volume [m3]": 10.5},
    {"Batch": "19x75", "Quality": "Q2", "Volume [m3]": 2.3},
    {"Batch": "25x100", "Quality": "Q1", "Volume [m3]": 15.2},
    {"Batch": "25x100", "Quality": "Q3", "Volume [m3]": 1.8},
    {"Batch": "32x125", "Quality": "Q1", "Volume [m3]": 20.0},
]

items_data = [
    {"item": "19x75", "m3_per_meter": 0.00143},
    {"item": "25x100", "m3_per_meter": 0.0025},
    {"item": "32x125", "m3_per_meter": 0.0040},
]

shifts = [
    {"day": "Monday", "start": "07:00", "end": "19:00"},
    {"day": "Monday", "start": "19:00", "end": "07:00"},
    {"day": "Tuesday", "start": "07:00", "end": "19:00"},
    {"day": "Tuesday", "start": "19:00", "end": "07:00"},
    {"day": "Wednesday", "start": "07:00", "end": "19:00"},
    {"day": "Wednesday", "start": "19:00", "end": "07:00"},
    {"day": "Thursday", "start": "07:00", "end": "16:30"},
    {"day": "Thursday", "start": "20:30", "end": "06:00"},
]

# ==== Streamlit UI ====

st.set_page_config(layout="wide")
st.title("📏 Production Planning App")

# Sidebar inputs
st.sidebar.header("🔧 Planning Settings")
availability = st.sidebar.slider("Availability (%)", 50, 100, 85) / 100.0
speed = st.sidebar.number_input("Line Speed (m/min)", min_value=1, value=70)

# Item selection
st.subheader("📦 Item Selection")
item_inputs = []
for item in items_data:
    with st.expander(f"Item: {item['item']}"):
        meters = st.number_input(f"Enter needed meters for {item['item']}", key=item['item'], value=0)
        if meters > 0:
            item_inputs.append({
                "item": item['item'],
                "meters": meters,
                "m3_per_meter": item["m3_per_meter"]
            })

if not item_inputs:
    st.warning("Please add meters for at least one item to calculate the plan.")
    st.stop()

# ==== Calculations ====
results = []
for item in item_inputs:
    # Get yield % for Q1
    q1_volume = sum(row["Volume [m3]"] for row in table_data if row["Batch"] == item["item"] and row["Quality"] == "Q1")
    total_volume = sum(row["Volume [m3]"] for row in table_data if row["Batch"] == item["item"])
    q1_yield = q1_volume / total_volume if total_volume > 0 else 0

    # Adjusted meters and production time
    adjusted_meters = item["meters"] / q1_yield if q1_yield > 0 else 0
    m3_needed = adjusted_meters * item["m3_per_meter"]
    hours_needed = adjusted_meters / (speed * 60 * availability)

    results.append({
        "Item": item["item"],
        "Q1 Yield %": round(q1_yield * 100, 2),
        "Meters Needed": item["meters"],
        "Adjusted Meters": round(adjusted_meters, 2),
        "M3 Needed": round(m3_needed, 2),
        "Hours Needed": round(hours_needed, 2)
    })

# ==== Show Result Table ====
st.subheader("📊 Planning Summary")
df = pd.DataFrame(results)
st.dataframe(df)

st.success("✅ Plan created. Future versions will add calendar-based scheduling!")
