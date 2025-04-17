
import os
import streamlit as st
import pandas as pd

# Set correct file path
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "For Phyton.xlsx")

# Print statements to verify paths
print(f"Current directory: {current_dir}")
print(f"File path: {file_path}")

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        st.error("❌ Excel file 'For Phyton.xlsx' not found. Please ensure it's in the same directory as 'app.py'.")
        st.stop()
    xls = pd.ExcelFile(file_path)
    table_df = xls.parse("Table")
    item_df = xls.parse("Item sizes per meter")
    return table_df, item_df

table_df, item_df = load_data()


# Clean up item names
table_df["Batch"] = table_df["Batch"].astype(str).str.strip()
item_df["item"] = item_df["item"].astype(str).str.strip()

# Merge data: Available items with m3 per meter
available_items = pd.merge(
    table_df[["Batch"]].drop_duplicates(),
    item_df,
    how="left",
    left_on="Batch",
    right_on="item"
).dropna(subset=["m3_per_meter"])

# Sidebar config
st.sidebar.header("⚙️ Settings")
speed = st.sidebar.number_input("Line Speed (m/min)", min_value=1, value=70)
availability = st.sidebar.slider("Availability (%)", 50, 100, value=85) / 100.0

# Item selection
st.subheader("🔢 Select Items and Enter Meters")
selected_items = st.multiselect(
    "Select items to plan for:",
    options=available_items["item"].unique()
)

user_inputs = []
for item in selected_items:
    meters = st.number_input(f"Enter meters needed for {item}:", min_value=0, key=item)
    if meters > 0:
        m3_per_meter = available_items[available_items["item"] == item]["m3_per_meter"].values[0]
        user_inputs.append({"item": item, "meters": meters, "m3_per_meter": m3_per_meter})

if not user_inputs:
    st.warning("Please select items and enter needed meters.")
    st.stop()

# ==== Calculation ====
results = []
for entry in user_inputs:
    item = entry["item"]
    meters = entry["meters"]
    m3_per_meter = entry["m3_per_meter"]

    # Q1 Yield calculation
    item_data = table_df[table_df["Batch"] == item]
    q1_volume = item_data[item_data["Quality"] == "Q1"]["Volume [m3]"].sum()
    total_volume = item_data["Volume [m3]"].sum()
    q1_yield = q1_volume / total_volume if total_volume else 0

    adjusted_meters = meters / q1_yield if q1_yield > 0 else 0
    m3_needed = adjusted_meters * m3_per_meter
    hours_needed = adjusted_meters / (speed * 60 * availability)

    results.append({
        "Item": item,
        "Q1 Yield %": round(q1_yield * 100, 2),
        "Meters Needed": meters,
        "Adjusted Meters": round(adjusted_meters, 2),
        "M³ Needed": round(m3_needed, 2),
        "Hours Needed": round(hours_needed, 2)
    })

# Show result table
st.subheader("📊 Planning Output")
result_df = pd.DataFrame(results)
st.dataframe(result_df)

# Optional download
csv = result_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Results as CSV", data=csv, file_name="production_plan.csv", mime="text/csv")
