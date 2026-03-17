import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("🚀 AI Dashboard Project")

st.write("Upload your CSV or Excel file to visualize the data!")

# File uploader - supports both CSV and Excel files
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    # Get file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    # Load dataset based on file type
    try:
        if file_extension == 'csv':
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except (UnicodeDecodeError, TypeError):
                uploaded_file.seek(0)  # Reset file pointer
                try:
                    df = pd.read_csv(uploaded_file, encoding="latin1")
                except (UnicodeDecodeError, TypeError):
                    uploaded_file.seek(0)  # Reset file pointer
                    df = pd.read_csv(uploaded_file, encoding="cp1252")
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file, engine='openpyxl' if file_extension == 'xlsx' else None)
        else:
            st.error("Unsupported file format. Please upload CSV or Excel files.")
            df = None
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        df = None
    
    if df is not None:
        # Clean column names
        df.columns = df.columns.str.replace(r'[^\x00-\x7F]+', '', regex=True)
        df.columns = df.columns.str.strip()
        
        # Show columns (for debugging)
        st.write("**Columns detected:**", list(df.columns))
        
        st.write("### 📊 Dataset Preview")
        st.dataframe(df.head(10))
        
        # Show basic statistics
        st.write("### 📈 Dataset Statistics")
        st.write(df.describe())
        
        # Check for stock data columns
        stock_columns = ["DATE", "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"]
        has_stock_data = all(col in df.columns for col in stock_columns)
        
        if has_stock_data:
            # Convert DATE to datetime
            df['DATE'] = pd.to_datetime(df['DATE'])
            df = df.sort_values('DATE')
            
            # Get unique symbols if available
            if 'SYMBOL' in df.columns:
                symbols = df['SYMBOL'].unique()
                st.write(f"**Stock Symbols Found:** {', '.join(symbols)}")
                
                # Allow user to select symbol if multiple exist
                if len(symbols) > 1:
                    selected_symbol = st.selectbox("Select Symbol to Visualize:", symbols)
                    df_filtered = df[df['SYMBOL'] == selected_symbol]
                else:
                    df_filtered = df
            else:
                df_filtered = df
            
            # Create candlestick chart
            st.write("### 📊 Candlestick Chart (OHLC)")
            fig_candle = go.Figure(data=[go.Candlestick(
                x=df_filtered['DATE'],
                open=df_filtered['OPEN'],
                high=df_filtered['HIGH'],
                low=df_filtered['LOW'],
                close=df_filtered['CLOSE']
            )])
            fig_candle.update_layout(
                title="Stock Price (OHLC)",
                xaxis_title="Date",
                yaxis_title="Price",
                height=500
            )
            st.plotly_chart(fig_candle, use_container_width=True)
            
            # Create volume chart
            st.write("### 📊 Trading Volume")
            fig_volume = px.bar(df_filtered, x='DATE', y='VOLUME', title="Trading Volume Over Time")
            fig_volume.update_layout(
                xaxis_title="Date",
                yaxis_title="Volume",
                height=400
            )
            st.plotly_chart(fig_volume, use_container_width=True)
            
            # Create closing price line chart
            st.write("### 📈 Closing Price Trend")
            fig_close = px.line(df_filtered, x='DATE', y='CLOSE', title="Closing Price Trend")
            fig_close.update_layout(
                xaxis_title="Date",
                yaxis_title="Closing Price",
                height=400
            )
            st.plotly_chart(fig_close, use_container_width=True)
            
            # Price range analysis
            if 'TURNOVER' in df.columns:
                st.write("### 💰 Turnover Analysis")
                fig_turnover = px.area(df_filtered, x='DATE', y='TURNOVER', title="Turnover Over Time")
                fig_turnover.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Turnover",
                    height=400
                )
                st.plotly_chart(fig_turnover, use_container_width=True)
            
        else:
            st.warning("⚠️ The uploaded file doesn't contain the expected stock market columns.")
            st.write("**Expected columns:** DATE, OPEN, HIGH, LOW, CLOSE, VOLUME")
            st.write("**Available columns:**", list(df.columns))
        
        # Custom Visualization Section
        st.write("---")
        st.write("## 🎨 Custom Visualization")
        st.write("Create your own charts by selecting columns and chart types!")
        
        # Get numeric and categorical columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        all_cols = df.columns.tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            chart_type = st.selectbox(
                "Select Chart Type:",
                ["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart", "Area Chart", "Box Plot"]
            )
        
        with col2:
            if chart_type in ["Bar Chart", "Line Chart", "Area Chart", "Box Plot"]:
                x_axis = st.selectbox("Select X-axis:", all_cols, key="x_axis")
                y_axis = st.selectbox("Select Y-axis:", numeric_cols, key="y_axis")
            elif chart_type == "Scatter Plot":
                x_axis = st.selectbox("Select X-axis:", numeric_cols, key="x_axis_scatter")
                y_axis = st.selectbox("Select Y-axis:", numeric_cols, key="y_axis_scatter")
            elif chart_type == "Pie Chart":
                labels_col = st.selectbox("Select Labels:", all_cols, key="labels")
                values_col = st.selectbox("Select Values:", numeric_cols, key="values")
        
        # Optional: Filter by categorical column
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        if categorical_cols:
            filter_option = st.checkbox("Filter data by a column?")
            if filter_option:
                filter_col = st.selectbox("Select column to filter:", categorical_cols)
                filter_values = st.multiselect(
                    f"Select {filter_col} values:",
                    options=df[filter_col].unique().tolist(),
                    default=df[filter_col].unique().tolist()
                )
                df_custom = df[df[filter_col].isin(filter_values)]
            else:
                df_custom = df
        else:
            df_custom = df
        
        # Create custom chart
        if st.button("Generate Chart"):
            try:
                if chart_type == "Bar Chart":
                    fig = px.bar(df_custom, x=x_axis, y=y_axis, title=f"{y_axis} by {x_axis}")
                elif chart_type == "Line Chart":
                    fig = px.line(df_custom, x=x_axis, y=y_axis, title=f"{y_axis} over {x_axis}")
                elif chart_type == "Scatter Plot":
                    fig = px.scatter(df_custom, x=x_axis, y=y_axis, title=f"{y_axis} vs {x_axis}")
                elif chart_type == "Area Chart":
                    fig = px.area(df_custom, x=x_axis, y=y_axis, title=f"{y_axis} over {x_axis}")
                elif chart_type == "Pie Chart":
                    fig = px.pie(df_custom, names=labels_col, values=values_col, title=f"{values_col} by {labels_col}")
                elif chart_type == "Box Plot":
                    fig = px.box(df_custom, x=x_axis, y=y_axis, title=f"{y_axis} distribution by {x_axis}")
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show filtered data statistics
                st.write("### Statistics for Selected Data")
                st.write(df_custom.describe())
                
            except Exception as e:
                st.error(f"Error creating chart: {str(e)}")
                st.write("Please ensure you've selected appropriate columns for the chart type.")

else:
    st.info("👆 Please upload a CSV or Excel file to get started.")
    st.write("**Supported formats:** CSV (.csv), Excel (.xlsx, .xls)")
    st.write("**Example data types:**")
    st.write("- Stock market data with: DATE, SYMBOL, OPEN, HIGH, LOW, CLOSE, VOLUME, TURNOVER")
    st.write("- Any tabular data with columns like: model, price, category, etc.")