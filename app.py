
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📏 Production Planner with Q1 Yield")



 # ---- Upload Excel File ----
 uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])
 
 if uploaded_file:
     # ---- Load Data ----
     xls = pd.ExcelFile(uploaded_file)
     table_df = xls.parse("Table")
     items_df = xls.parse("Item Sizes per meter")
     hours_df = xls.parse("Hours per day")



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
