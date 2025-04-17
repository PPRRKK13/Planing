import os
import streamlit as st
import pandas as pd

# Get absolute path to this file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "For Phyton.xlsx")

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        st.error("Excel file 'For Phyton.xlsx' not found. Please ensure it's in the same directory as 'app.py'.")
        st.stop()
    xls = pd.ExcelFile(file_path)
    table_df = xls.parse("Table")
    item_df = xls.parse("Item sizes per meter")
    return table_df, item_df

table_df, item_df = load_data()

# Preview data
st.title("Production Planning")
st.write("Table Data")
st.dataframe(table_df)
st.write("Item Data")
st.dataframe(item_df)
st.write("Available sheets:", xls.sheet_names)
