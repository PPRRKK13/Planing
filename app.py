
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📏 Production Planner with Q1 Yield")


# ---- Embed Excel Data ----
# Load the embedded Excel data
table_data = {
    "Date": ["01/01/2024"] * 10,
    "Supplier": ["0007"] * 10,
    "Batch": ["19x75"] * 10,
    "Product name": ["Waste", "Long Waste", "Blade Waste", "Full Waste Board", "Q1 FJ 18x73", "Q1 FJ 18x73 short", "Q3 18x62,5", "Q2 18x73 BLUE", "Q4 18x73 2nd size down", "Q5 18x73x2403"],
    "Product Grade name": ["Waste", "Reserved for Waste", "Waste", "Waste", "Q1 Finger Joint", "Q1 Finger Joint", "Q3 Width", "BLUE Q2 grade", "Q3 Width", "Q1 Finger Joint"],
    "Quality": ["Waste", "Waste", "Waste", "Waste", "Q1", "Q1", "Q3", "Q2", "Q4", "Q5"],
    "Pieces": [63415, 25976, 0, 0, 59502, 19445, 3751, 4894, 3659, 100],
    "Length [m]": [3530.77, 5263.21, 599.53, 0, 24304.4, 3965.93, 947.134, 1527.63, 846.612, 240.8],
    "Volume [m3]": [4.65, 6.931, 0.79, 0, 31.999, 5.225, 1.247, 2.014, 1.115, 0.317]
}

item_sizes_data = {
    "Item": ["19x75"] * 10,
    "M3 per meter": [0.001] * 10
}

hours_per_day_data = {
    "Hours": [24]
}

# Convert to DataFrames
table_df = pd.DataFrame(table_data)
items_df = pd.DataFrame(item_sizes_data)
hours_df = pd.DataFrame(hours_per_day_data)




    # Clean item size table
    items_cleaned = items_df.rename(columns={items_df.columns[0]: "Item", items_df.columns[1]: "M3 per meter"})

    # ---- Calculate Q1 Yield ----
    total_volume = table_df.groupby("Batch")["Volume [m3]"].sum().reset_index(name="Total Volume")
    q1_volume = table_df[table_df["Quality"] == "Q1"].groupby("Batch")["Volume [m3]"].sum().reset_index(name="Q1 Volume")
    q1_yield = pd.merge(q1_volume, total_volume, on="Batch")
    q1_yield["Q1 Yield"] = q1_yield["Q1 Volume"] / q1_yield["Total Volume"]
    q1_yield = q1_yield.rename(columns={"Batch": "Item"})

    # Merge with item sizes
    item_master = pd.merge(items_cleaned, q1_yield[["Item", "Q1 Yield"]], on="Item", how="inner")

    st.subheader("🛠 Select Items and Enter Required Meters")
    selected_items = st.multiselect("Choose Items", item_master["Item"].unique())

    if selected_items:
        meters_input = {}
        for item in selected_items:
            meters = st.number_input(f"Meters needed for {item}", min_value=0, step=100, key=item)
            meters_input[item] = meters

        # ---- Calculations ----
        df = item_master[item_master["Item"].isin(meters_input.keys())].copy()
        df["Meters Needed"] = df["Item"].map(meters_input)

        speed_mph = 70 * 60  # 70 meters/min
        df["Adjusted Meters"] = df["Meters Needed"] / df["Q1 Yield"]
        df["Good m/h"] = speed_mph * df["Q1 Yield"]
        df["Hours Needed"] = df["Adjusted Meters"] / df["Good m/h"]
        df["m3 Needed"] = df["Adjusted Meters"] * df["M3 per meter"]

        st.subheader("📊 Calculation Results")
        st.dataframe(df[["Item", "Meters Needed", "Q1 Yield", "Adjusted Meters", "Hours Needed", "m3 Needed"]])

        # ---- Calendar Simulation ----
        st.subheader("📆 Monthly Production Simulation")

        hours_per_day = hours_df["Hours"].iloc[0]
        days = []
        cumulative_hours = 0
        day_num = 1

        for i, row in df.iterrows():
            hours_needed = row["Hours Needed"]
            while hours_needed > 0:
                used = min(hours_per_day, hours_needed)
                days.append({
                    "Day": f"Day {day_num}",
                    "Item": row["Item"],
                    "Hours": used
                })
                hours_needed -= used
                cumulative_hours += used
                if used == hours_per_day:
                    day_num += 1

        calendar_df = pd.DataFrame(days)

        fig = px.bar(calendar_df, x="Day", y="Hours", color="Item", title="Production Plan (Hours per Day)", text="Item")
        st.plotly_chart(fig, use_container_width=True)

        # Export option
        st.subheader("💾 Export Results")
        export_df = df[["Item", "Meters Needed", "Q1 Yield", "Adjusted Meters", "Hours Needed", "m3 Needed"]]
        export_excel = export_df.to_excel(index=False, engine='openpyxl')
        st.download_button("Download Calculated Table as Excel", data=export_excel, file_name="production_plan.xlsx")
