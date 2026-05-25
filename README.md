import streamlit as st
import pandas as pd
import plotly.express as px

# PAGE SETTINGS
st.set_page_config(
    page_title="Excel Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Excel Data Analyzer")
st.write("Upload your Excel file and explore your data!")

# UPLOAD EXCEL FILE
uploaded_file = st.file_uploader(
    "📁 Upload your Excel file",
    type=["xlsx", "xls"]
)

if uploaded_file is not None:

    # READ THE FILE
    df = pd.read_excel(uploaded_file)
    st.success(f"✅ File loaded! {len(df)} rows and {len(df.columns)} columns found.")

    # SHOW RAW DATA
    st.subheader("🔍 Raw Data Preview")
    st.dataframe(df, use_container_width=True)

    # BASIC STATISTICS
    st.subheader("📈 Basic Statistics")
    st.write(df.describe())

    # CHART SETTINGS
    st.subheader("🎨 Create Your Chart")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    text_cols    = df.select_dtypes(include="object").columns.tolist()

    col1, col2, col3 = st.columns(3)

    with col1:
        chart_type = st.selectbox(
            "Chart type",
            ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"]
        )
    with col2:
        x_axis = st.selectbox("X axis", text_cols + numeric_cols)
    with col3:
        y_axis = st.selectbox("Y axis", numeric_cols)

    # DRAW CHART
    if chart_type == "Bar Chart":
        fig = px.bar(df, x=x_axis, y=y_axis, color=x_axis)

    elif chart_type == "Line Chart":
        fig = px.line(df, x=x_axis, y=y_axis)

    elif chart_type == "Pie Chart":
        fig = px.pie(df, names=x_axis, values=y_axis)

    elif chart_type == "Scatter Plot":
        fig = px.scatter(df, x=x_axis, y=y_axis)

    st.plotly_chart(fig, use_container_width=True)

    # FILTER DATA
    st.subheader("🔎 Filter Your Data")

    if text_cols:
        selected_col = st.selectbox("Filter by column", text_cols)
        unique_values = df[selected_col].unique().tolist()
        selected_value = st.multiselect("Select values", unique_values, default=unique_values)
        filtered_df = df[df[selected_col].isin(selected_value)]
        st.dataframe(filtered_df, use_container_width=True)

    # DOWNLOAD
    st.subheader("⬇️ Download Your Data")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="analyzed_data.csv",
        mime="text/csv"
    )

else:
    st.info("👆 Please upload an Excel file to get started!")# app.py
Python library streamlit
