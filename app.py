import streamlit as st
import os
import json
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_URL, SHEET_NAME, CREDENTIALS_PATH

# --- Simple password protection ---
PASSWORD = st.secrets["PASSWORD"] 

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    pwd = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
cred_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)


@st.cache_data
def get_worksheet_names():
    client = gspread.authorize(credentials)
    sheet = client.open_by_url(SHEET_URL)
    return [ws.title for ws in sheet.worksheets()]

# loading data
@st.cache_data
def load_data(selected_sheet):
    client = gspread.authorize(credentials)
    sheet = client.open_by_url(SHEET_URL)
    worksheet = sheet.worksheet(selected_sheet)
    df = get_as_dataframe(worksheet, header=0)
    df = df.dropna(subset=["Description" , "Image URL"])
    return df

#stream lit ui
st.set_page_config(page_title="PhotoTank", layout="wide")
st.title("PhotoTank")
st.write("Search for photos by description or year")

#refresh button 
if st.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()

#sheet selection
worksheet_names = get_worksheet_names()
selected_sheet = st.selectbox("Select sheet (year):", worksheet_names)

#loads data from selected sheet
df = load_data(selected_sheet)

#category selection
category = None
if "Category" in df.columns:
    categories = ["All"] + sorted(df["Category"].dropna().unique().tolist())
    category = st.selectbox("Select category:", categories)
    if category != "All":
        df = df[df["Category"] == category]

#keyword search
keyword = st.text_input("Enter a keyword to search in the description:")

if keyword:
    filtered_df = df[df["Description"].str.contains(keyword, case=False, na=False)]
    st.write(f"Found {len(filtered_df)} results for '{keyword}'")
else:
    filtered_df = df
    st.write(f"Showing all {len(filtered_df)} results")

# image display
if filtered_df.empty:
    st.info("No results found.")
else:
    for _, row in filtered_df.iterrows():
        st.markdown(f"### {row['Description']}")
        # Show the image if the link is accessible
        if "Cover" in filtered_df.columns and pd.notna(row["Cover"]):
            st.image(row["Cover"], width=300)
        st.markdown(f"[View Image Link]({row['Image URL']})")
        st.markdown("---")
