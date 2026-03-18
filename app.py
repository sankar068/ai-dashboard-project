import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

st.title("🚀 Auto Insights AI Dashboard")

st.write("Upload your CSV or Excel file to visualize the data!")

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        if file_extension == 'csv':
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except:
                uploaded_file.seek(0)
                try:
                    df = pd.read_csv(uploaded_file, encoding="latin1")
                except:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding="cp1252")

        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file, engine='openpyxl' if file_extension == 'xlsx' else None)
        else:
            st.error("Unsupported file format.")
            df = None

    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        df = None

    if df is not None:
        # Clean columns
        df.columns = df.columns.str.replace(r'[^\x00-\x7F]+', '', regex=True)
        df.columns = df.columns.str.strip()

        st.write("**Columns detected:**", list(df.columns))

        st.write("### 📊 Dataset Preview")
        st.dataframe(df.head(10))

        st.write("### 📈 Dataset Statistics")
        st.write(df.describe())

        # =========================
        # 🤖 QUERY BOT FEATURE (FIXED)
        # =========================
        st.write("---")
        st.write("## 🤖 Ask Questions About Your Data")

        user_query = st.text_input("Example: 'show data from 2021 to 2024' or 'top 10'")

        if user_query:
            try:
                query = user_query.lower()
                df_query = df.copy()

                # Extract years
                years = re.findall(r'\d{4}', query)

                if len(years) >= 2:
                    start_year = int(years[0])
                    end_year = int(years[1])

                    # 🔥 SMART DATE COLUMN DETECTION
                    date_cols = []
                    for col in df.columns:
                        try:
                            temp = pd.to_datetime(df[col], errors='coerce')
                            if temp.notna().sum() > 0:
                                date_cols.append(col)
                        except:
                            pass

                    if date_cols:
                        date_col = date_cols[0]
                        df_query[date_col] = pd.to_datetime(df_query[date_col], errors='coerce')

                        df_query = df_query[
                            (df_query[date_col].dt.year >= start_year) &
                            (df_query[date_col].dt.year <= end_year)
                        ]

                        st.write(f"### 📊 Data from {start_year} to {end_year}")
                        st.write("Filtered rows:", len(df_query))

                        if df_query.empty:
                            st.warning("⚠️ No data found for given years.")
                        else:
                            st.dataframe(df_query.head())

                            numeric_cols = df_query.select_dtypes(include=['number']).columns.tolist()

                            if numeric_cols:
                                fig = px.bar(
                                    df_query,
                                    x=date_col,
                                    y=numeric_cols[0],
                                    title=f"{numeric_cols[0]} from {start_year} to {end_year}"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("⚠️ No date/year column detected in dataset.")

                elif "top" in query:
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

                    if numeric_cols:
                        col = numeric_cols[0]
                        df_top = df.sort_values(by=col, ascending=False).head(10)

                        st.write("### 🔝 Top 10 Records")
                        st.dataframe(df_top)

                        fig = px.bar(df_top, x=df_top.columns[0], y=col, title="Top 10 Data")
                        st.plotly_chart(fig, use_container_width=True)

                else:
                    st.warning("Try queries like '2021 to 2024' or 'top 10'")

            except Exception as e:
                st.error(f"Query Error: {str(e)}")

        # =========================
        # EXISTING STOCK LOGIC
        # =========================
        stock_columns = ["DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]
        has_stock_data = all(col in df.columns for col in stock_columns)

        if has_stock_data:
            df['DATE'] = pd.to_datetime(df['DATE'])
            df = df.sort_values('DATE')

            if 'SYMBOL' in df.columns:
                symbols = df['SYMBOL'].unique()
                if len(symbols) > 1:
                    selected_symbol = st.selectbox("Select Symbol:", symbols)
                    df_filtered = df[df['SYMBOL'] == selected_symbol]
                else:
                    df_filtered = df
            else:
                df_filtered = df

            st.write("### 📊 Candlestick Chart")
            fig_candle = go.Figure(data=[go.Candlestick(
                x=df_filtered['DATE'],
                open=df_filtered['OPEN'],
                high=df_filtered['HIGH'],
                low=df_filtered['LOW'],
                close=df_filtered['CLOSE']
            )])
            st.plotly_chart(fig_candle, use_container_width=True)

            st.write("### 📊 Volume")
            st.plotly_chart(px.bar(df_filtered, x='DATE', y='VOLUME'), use_container_width=True)

            st.write("### 📈 Closing Price")
            st.plotly_chart(px.line(df_filtered, x='DATE', y='CLOSE'), use_container_width=True)

        # =========================
        # CUSTOM VISUALIZATION
        # =========================
        st.write("---")
        st.write("## 🎨 Custom Visualization")

        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        all_cols = df.columns.tolist()

        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie"])

        if chart_type != "Pie":
            x = st.selectbox("X-axis", all_cols)
            y = st.selectbox("Y-axis", numeric_cols)

        if st.button("Generate Chart"):
            if chart_type == "Bar":
                fig = px.bar(df, x=x, y=y)
            elif chart_type == "Line":
                fig = px.line(df, x=x, y=y)
            elif chart_type == "Scatter":
                fig = px.scatter(df, x=x, y=y)
            elif chart_type == "Pie":
                labels = st.selectbox("Labels", all_cols)
                values = st.selectbox("Values", numeric_cols)
                fig = px.pie(df, names=labels, values=values)

            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Upload a file to begin.")
