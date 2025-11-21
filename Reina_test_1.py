import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ------------------------------
# STREAMLIT APP HEADER
# ------------------------------
st.set_page_config(page_title="Invoice Cleaning App", layout="wide")
st.title("🧹 Invoice Cleaning & Processing App")

st.write("Upload your **Invoice_Detail.csv** and **Assignment File.xlsx** to process the data.")

# ------------------------------
# FILE UPLOAD SECTION
# ------------------------------
invoice_file = st.file_uploader("Upload Invoice_Detail.csv", type=["csv"])
assign_file = st.file_uploader("Upload Assignment File.xlsx", type=["xlsx"])


# -----------------------------------------------------
# PROCESSING STARTS WHEN BOTH FILES ARE UPLOADED
# -----------------------------------------------------
if invoice_file and assign_file:
    st.success("Files uploaded successfully!")

    # Load files
    df = pd.read_csv(invoice_file, on_bad_lines='skip', engine='python')
    df_Assign = pd.read_excel(assign_file, engine='openpyxl')

    # ------------------------------
    # DATA CLEANING STEPS
    # ------------------------------

    # Drop column
    if "HCPCS" in df.columns:
        df = df.drop(columns=["HCPCS"])

    # Remove Closed/Rejected rows
    df = df[~df["Status"].isin(["Closed", "Rejected"])]

    # Replace blank strings with NaN
    df = df.replace(r'^\s*$', pd.NA, regex=True)

    # Drop rows with any NaN values
    df = df.dropna()

    # Sort by Patient Name
    df = df.sort_values(by="Patient Name")

    # Remove rows with negative balance/charge
    df = df[df["Balance"] > 0]
    df = df[df["Charge"] > 0]

    # ------------------------------
    # GROUPING & MERGING TOTALS
    # ------------------------------
    # Total Charge
    total_charge = df.groupby("Invoice", as_index=False).agg(
        Total_Charge=("Charge", "sum")
    )
    df = df.merge(total_charge, on="Invoice", how="left")

    # Total Balance
    total_balance = df.groupby("Invoice", as_index=False).agg(
        Total_Balance=("Balance", "sum")
    )
    df = df.merge(total_balance, on="Invoice", how="left")

    # Remove duplicate invoices
    df = df.drop_duplicates(subset=["Invoice"], keep="first")

    # ------------------------------
    # DATE LOGIC
    # ------------------------------
    df["DOS From"] = pd.to_datetime(df["DOS From"], errors="coerce")
    today_ts = pd.Timestamp(datetime.today().date())

    df["Age of Claims"] = (today_ts - df["DOS From"]).dt.days
    df = df.sort_values(by="Age of Claims")

    # Buckets
    conditions = [
        (df["Age of Claims"] >= 0) & (df["Age of Claims"] <= 30),
        (df["Age of Claims"] > 30) & (df["Age of Claims"] <= 60),
        (df["Age of Claims"] > 60) & (df["Age of Claims"] <= 90),
        (df["Age of Claims"] > 90) & (df["Age of Claims"] <= 120),
        (df["Age of Claims"] > 120)
    ]

    labels = ["Bucket - 1", "Bucket - 2", "Bucket - 3", "Bucket - 4", "Bucket - 5"]

    df["Bucket"] = np.select(conditions, labels, default="Uncategorized")

    # ------------------------------
    # MERGE ASSIGNMENT FILE
    # ------------------------------
    df = df.merge(
        df_Assign[["Payer Name", "Reps"]],
        on="Payer Name",
        how="left"
    )

    # ------------------------------
    # SHOW OUTPUT
    # ------------------------------
    st.subheader("✅ Cleaned Output Preview")
    st.dataframe(df.head(50))

    # ------------------------------
    # EXPORT BUTTON
    # ------------------------------
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Cleaned Invoice File",
        data=csv,
        file_name="Invoice_Clean.csv",
        mime="text/csv"
    )

    st.success("Processing completed successfully!")

else:
    st.info("Please upload both input files to proceed.")