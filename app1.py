import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
from fpdf import FPDF
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderInsufficientPrivileges

# Mock Database for User Authentication
users_db = {"admin": "password123"}

# Helper Functions
def save_data_to_excel(user_data, filename="user_data.xlsx"):
    df = pd.DataFrame(user_data)
    df.to_excel(os.path.join("C:/Users/vadiraj/OneDrive/Desktop/Hackthon", filename), index=False)

def save_data_to_pdf(user_data, filename="user_data.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for key, value in user_data.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

    pdf.output(os.path.join("C:/Users/vadiraj/OneDrive/Desktop/Hackthon", filename))

def signup(username, password):
    if username in users_db:
        st.error("User already exists. Please log in.")
    else:
        users_db[username] = password
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.success("Signup successful! You are now logged in.")

def login(username, password):
    if username in users_db and users_db[username] == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.success("Login successful!")
    else:
        st.error("Invalid username or password.")

def detect_location_india(city):
    try:
        geolocator = Nominatim(user_agent="MyRetailApp_v1")
        location = geolocator.geocode(f"{city}, India")
        if location:
            return location.address
        else:
            return "Location not found"
    except GeocoderInsufficientPrivileges as e:
        return f"Error: Insufficient privileges - {str(e)}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

def predict_future_trends(df, location, start_month, months_ahead):
    """
    Predict future trends for grocery sales for a given location.
    This function predicts quantities for each grocery item separately.
    """
    trends = []
    start_date = datetime(2024, start_month, 1)

    for i in range(months_ahead):
        future_month = (start_date + timedelta(days=30 * i)).strftime("%B")
        
        # Filter data for the specified location and month
        monthly_data = df[(df["Location"] == location) & (df["Month"] == future_month)]
        if not monthly_data.empty:
            # For each item, calculate the future quantity trend
            item_summary = monthly_data.groupby("Item")["Quantity"].sum()
            trends.append({"Month": future_month, "Data": item_summary})

    return trends

# Main Application
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("Welcome to Retail Inventory Forecasting")
    st.subheader("Signup or Login to continue")

    option = st.selectbox("Select an option", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Signup":
        if st.button("Signup"):
            signup(username, password)
            st.experimental_rerun()
    else:
        if st.button("Login"):
            login(username, password)
            st.experimental_rerun()
else:
    st.title(f"Welcome, {st.session_state['username']}!")

    # File Upload Section
    st.sidebar.header("File Upload")
    uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])

    # Location Input Section
    st.sidebar.header("User Input")
    city = st.sidebar.text_input("Enter your City:")

    if city:
        location_address = detect_location_india(city)
        st.write(f"Detected Location: {location_address}")

    # Future Prediction Inputs
    future_month = st.sidebar.number_input("Enter start month (1-12):", min_value=1, max_value=12, step=1)
    future_year = st.sidebar.number_input("Enter year:", min_value=datetime.now().year, max_value=2100, step=1)
    months_ahead = st.sidebar.number_input("Predict for how many months:", min_value=1, max_value=12, step=1)

    # Dropdown to select graph type
    graph_type = st.sidebar.selectbox(
        "Select graph type to display", 
        ["Grocery Quantity", "Price Distribution", "Season-wise Sales", "Monthly Sales", "Future Trend Prediction"]
    )

    if uploaded_file:
        try:
            # Load Excel File
            df = pd.read_excel(uploaded_file)
            st.write("### Uploaded Data")
            st.dataframe(df)

            required_columns = {"Date", "Cost", "Location", "Quantity", "Item"}
            if not required_columns.issubset(df.columns):
                st.error(f"The file must contain these columns: {', '.join(required_columns)}.")
            else:
                # Convert Date Column to Datetime
                df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
                df.dropna(subset=["Date"], inplace=True)

                # Extract Month from Date
                df["Month"] = df["Date"].dt.month_name()
                st.write("### Data with Month Extracted")
                st.dataframe(df)

                # Visualization: Different Graphs based on user selection
                if graph_type == "Grocery Quantity":
                    st.write("### Grocery Quantity Distribution")
                    location_data = df[df["Location"] == city]
                    if not location_data.empty:
                        quantity_summary = location_data.groupby("Item")["Quantity"].sum().reset_index()
                        st.dataframe(quantity_summary)
                        fig, ax = plt.subplots()
                        sns.barplot(x="Item", y="Quantity", data=quantity_summary, ax=ax)
                        ax.set_title("Grocery Quantity Distribution")
                        st.pyplot(fig)

                elif graph_type == "Price Distribution":
                    st.write("### Price Distribution")
                    fig, ax = plt.subplots()
                    sns.histplot(df["Cost"], bins=10, kde=True, ax=ax)
                    ax.set_title("Price Distribution")
                    st.pyplot(fig)

                elif graph_type == "Season-wise Sales":
                    st.write("### Season-wise Sales")
                    season_data = {
                        "Winter": df[df["Month"].isin(["December", "January", "February"])]["Cost"].sum(),
                        "Spring": df[df["Month"].isin(["March", "April", "May"])]["Cost"].sum(),
                        "Summer": df[df["Month"].isin(["June", "July", "August"])]["Cost"].sum(),
                        "Autumn": df[df["Month"].isin(["September", "October", "November"])]["Cost"].sum()
                    }
                    season_df = pd.DataFrame(list(season_data.items()), columns=["Season", "Total Sales"])
                    st.dataframe(season_df)
                    fig, ax = plt.subplots()
                    sns.barplot(x="Season", y="Total Sales", data=season_df, ax=ax)
                    ax.set_title("Season-wise Sales")
                    st.pyplot(fig)

                elif graph_type == "Monthly Sales":
                    st.write("### Monthly Sales")
                    monthly_sales = df.groupby("Month")["Cost"].sum()
                    st.dataframe(monthly_sales)
                    fig, ax = plt.subplots()
                    monthly_sales.plot(kind="bar", ax=ax)
                    ax.set_title("Monthly Sales")
                    st.pyplot(fig)

                elif graph_type == "Future Trend Prediction":
                    if city:
                        trends = predict_future_trends(df, city, future_month, months_ahead)
                        if trends:
                            for trend in trends:
                                st.write(f"### Predictions for {trend['Month']}")
                                st.dataframe(trend["Data"])
                                fig, ax = plt.subplots()
                                trend["Data"].plot(kind="bar", ax=ax, title=f"Trends for {trend['Month']}")
                                st.pyplot(fig)
                        else:
                            st.write("No data available for predictions.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.write("Upload an Excel file to get started.")
