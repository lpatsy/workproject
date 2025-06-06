import streamlit as st
import os
import json
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
from config import SHEET_URL, SHEET_NAME, CREDENTIALS_PATH

# --- Simple password protection ---
PASSWORD = "singhaphotostest"  # Change this to your desired password

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    pwd = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.error("Incorrect password")
    st.stop()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
cred_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)

# loading data
@st.cache_data
def load_data():
   
    client = gspread.authorize(credentials)

    sheet = client.open_by_url(SHEET_URL)
    worksheet = sheet.worksheet(SHEET_NAME)
    df = get_as_dataframe(sheet, header=0)
    df = df.dropna(subset=["Description" , "Image URL"])
    return df

#stream lit ui
st.set_page_config(page_title="PhotoTank", layout="wide")
st.title("PhotoTank")
st.write("Search for photos by description or year")

df = load_data()

keyword = st.text_input("Enter a keyword to search in the description:")

if keyword:
    filtered_df = df[df["Description"].str.contains(keyword, case=False, na=False)]
    st.write(f"Found {len(filtered_df)} results for '{keyword}'")

    for _, row in filtered_df.iterrows():
        st.markdown(f"### {row['Description']}")
        st.markdown(row["Image URL"], use_column_width=True)
        st.markdown("---")
else:
    st.info("Please enter a keyword to search for photos.")

if st.button("Refresh data"):
    st.cache_data.clear()
    st.experimental_rerun()