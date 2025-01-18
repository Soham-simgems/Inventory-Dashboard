import streamlit as st
import pandas as pd

# Set the app title
st.title("Inventory and RAP Data Summary Dashboard")

# Sidebar: Page selection
page = st.sidebar.radio("Select Page", ("Inventory", "RAP"))

# Custom CSS for styling buttons, tables, and background
st.markdown("""
    <style>
        body {
            background-color: #f0f8ff;
            font-family: 'Arial', sans-serif;
        }
        .stButton>button {
            background-color: #4CAF50; 
            color: white;
            font-size: 16px;
            border-radius: 8px;
            padding: 10px 24px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stTable {
            background-color: #f8f9fa;
            border-radius: 10px;
        }
        .stTable th {
            background-color: #4CAF50;
            color: white;
            padding: 10px;
        }
        .stTable td {
            padding: 10px;
        }
        .stInfo {
            background-color: #e0f7fa;
            color: #004d40;
            border-radius: 10px;
            padding: 10px;
        }
        .stError {
            background-color: #ffebee;
            color: #d32f2f;
            border-radius: 10px;
            padding: 10px;
        }
        .stDownloadButton>button {
            background-color: #2196F3;
            color: white;
            border-radius: 8px;
        }
        .stDownloadButton>button:hover {
            background-color: #1976D2;
        }
    </style>
""", unsafe_allow_html=True)

# ===========================
# RAP Page
# ===========================
if page == "RAP":
    # Display only the RAP file upload button
    rap_file = st.file_uploader("Upload your RAP data file (CSV/Excel)", type=["csv", "xlsx"])

    if rap_file:
        # Load RAP Data
        if rap_file.name.endswith(".csv"):
            rap_data = pd.read_csv(rap_file)
        else:
            rap_data = pd.read_excel(rap_file)

        # Check RAP data columns
        rap_required_columns = ["Rapnet Lot #", "Stock #", "Country"]
        if all(col in rap_data.columns for col in rap_required_columns):
            # Count of Stock # for Total RAP Data
            total_rap_count = rap_data["Stock #"].count()

            # Count of Stock # where Country is Hong Kong
            hk_rap_count = rap_data[rap_data["Country"] == "Hong Kong"]["Stock #"].count()

            # Count of Stock # for each Country
            country_rap_count = rap_data.groupby("Country")["Stock #"].count()

            # Create a RAP Data Summary Table
            rap_summary = pd.DataFrame({
                "Total RAP Count": [total_rap_count],
                "Hong Kong Count": [hk_rap_count],
                "Country Wise RAP Counts": [country_rap_count]
            })

            st.subheader("RAP Data Summary")
            st.table(rap_summary.style.set_table_styles(
                [{'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
                 {'selector': 'tbody td', 'props': [('background-color', '#f8f9fa'), ('color', 'black')]},
                 {'selector': 'table', 'props': [('border-radius', '10px')]}]
            ))

        else:
            st.error("Missing required columns in RAP data.")
    else:
        st.info("Upload your RAP data to see the summary.")

# ===========================
# Inventory Page
# ===========================
elif page == "Inventory":
    # File Uploads for HK, USA, IND Inventory Files
    uploaded_hk_file = st.sidebar.file_uploader("Upload HK Inventory file (CSV/Excel)", type=["csv", "xlsx"])
    uploaded_usa_file = st.sidebar.file_uploader("Upload USA Inventory file (CSV/Excel)", type=["csv", "xlsx"])
    uploaded_ind_file = st.sidebar.file_uploader("Upload IND Inventory file (CSV/Excel)", type=["csv", "xlsx"])

    if uploaded_hk_file or uploaded_usa_file or uploaded_ind_file:
        # Load Inventory Data for HK, USA, IND
        inventory_data = {}

        # Function to load file and add location column
        def load_and_add_location(file, location_name):
            if file.name.endswith(".csv"):
                data = pd.read_csv(file)
            else:
                data = pd.read_excel(file)
            data["Location"] = location_name  # Add Location column based on the country name
            return data

        if uploaded_hk_file:
            inventory_data["HK"] = load_and_add_location(uploaded_hk_file, "HK")

        if uploaded_usa_file:
            inventory_data["USA"] = load_and_add_location(uploaded_usa_file, "USA")

        if uploaded_ind_file:
            inventory_data["IND"] = load_and_add_location(uploaded_ind_file, "IND")

        # Display Summary for each country (HK, USA, IND)
        summary = {}
        for_web_summary_combined = {}

        for country, data in inventory_data.items():
            # Check required columns in inventory data
            required_columns = ["Item CD", "Not for Web", "Legends", "Location"]
            if all(col in data.columns for col in required_columns):
                # Standardize Legends Column
                def classify_legends(legend):
                    if pd.isna(legend) or legend.strip() in ["Memo/Consign IN", ""]:
                        return "Memo in"
                    elif legend.strip() in ["Memo/Consign IN->Out", "Memo/Consign Out"]:
                        return "Memo out"
                    elif legend.strip() == "Hold":
                        return "On hold"
                    else:
                        return "Other"

                data["Legends"] = data["Legends"].apply(classify_legends)

                # Calculate Summary
                summary[country] = {
                    "Total Stones": data["Item CD"].count(),
                    "NFW Memo": data[(data["Not for Web"] == True) & (data["Legends"] == "Memo out")]["Item CD"].count(),
                    "NFW Available": data[(data["Not for Web"] == True) & (data["Legends"] == "Memo in")]["Item CD"].count(),
                    "On Hold": data[data["Legends"] == "On hold"]["Item CD"].count(),
                    "Memo In": data[data["Legends"] == "Memo in"]["Item CD"].count(),
                    "Memo Out": data[data["Legends"] == "Memo out"]["Item CD"].count(),
                    "NFW": data[data["Not for Web"] == True]["Item CD"].count(),
                    "For Web": data[data["Not for Web"] == False]["Item CD"].count(),
                }

                # Calculate For Web Summary Breakdown
                for_web_data = data[data["Not for Web"] == False]  # Filter data where "Not for Web" is False
                for_web_summary = for_web_data.groupby("Legends")["Item CD"].count()
                for_web_summary_combined[country] = for_web_summary

            else:
                st.error(f"Missing required columns in {country} inventory data: {', '.join(required_columns)}")

        # Combine all country summaries into one DataFrame
        combined_summary = pd.DataFrame(summary).fillna(0).T

        # Add a Total row to the summary
        combined_summary.loc["Total"] = combined_summary.sum()

        # Display Inventory Summary Table
        st.subheader("Inventory Summary Table (by Country)")
        st.table(combined_summary.style.set_table_styles(
            [{'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
             {'selector': 'tbody td', 'props': [('background-color', '#f8f9fa'), ('color', 'black')]},
             {'selector': 'table', 'props': [('border-radius', '10px')]}]
        ))

        # Combine "For Web" Summary Breakdown into one DataFrame
        combined_for_web_summary = pd.DataFrame(for_web_summary_combined).fillna(0).T
        combined_for_web_summary.loc["Total"] = combined_for_web_summary.sum()

        # Display Combined "For Web" Summary Breakdown
        st.subheader("Combined For Web Summary Breakdown (by Country)")
        st.table(combined_for_web_summary.style.set_table_styles(
            [{'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
             {'selector': 'tbody td', 'props': [('background-color', '#f8f9fa'), ('color', 'black')]},
             {'selector': 'table', 'props': [('border-radius', '10px')]}]
        ))

        # Interactive Data View
        # ===========================
        st.subheader("Click to View Data")

        # Create a grid layout with 3 columns for each button row
        button_columns = st.columns(3)

        # Loop through the combined_summary table and create buttons in rows of 3
        button_index = 0  # Index to track button placement in columns
        for location in combined_summary.index[:-1]:  # Skip the 'Total' row
            for column in combined_summary.columns:
                button = button_columns[button_index % 3].button(f"View {column} for {location}")
                button_index += 1

                if button:
                    # Filter the data based on the button clicked
                    if column == "Total Stones":
                        # For "Total Stones", display all data for the location
                        filtered_data = inventory_data[location]  # No filtering, just show all data
                    elif column == "NFW Memo":
                        filtered_data = inventory_data[location][(inventory_data[location]["Not for Web"] == True) & (inventory_data[location]["Legends"] == "Memo out")]
                    elif column == "NFW Available":
                        filtered_data = inventory_data[location][(inventory_data[location]["Not for Web"] == True) & (inventory_data[location]["Legends"] == "Memo in")]
                    elif column == "On Hold":
                        filtered_data = inventory_data[location][inventory_data[location]["Legends"] == "On hold"]
                    elif column == "Memo In":
                        filtered_data = inventory_data[location][inventory_data[location]["Legends"] == "Memo in"]
                    elif column == "Memo Out":
                        filtered_data = inventory_data[location][inventory_data[location]["Legends"] == "Memo out"]
                    elif column == "NFW":
                        filtered_data = inventory_data[location][inventory_data[location]["Not for Web"] == True]
                    elif column == "For Web":
                        filtered_data = inventory_data[location][inventory_data[location]["Not for Web"] == False]
                    else:
                        filtered_data = pd.DataFrame()

                    # Display the filtered data directly below the button
                    st.write(f"Filtered data for {column} in {location}:")
                    st.dataframe(filtered_data)

                    # Add a Download Button
                    csv = filtered_data.to_csv(index=False)
                    st.download_button(
                        label="Download Filtered Data",
                        data=csv,
                        file_name=f"{column}_{location}_data.csv",
                        mime="text/csv",
                    )

    else:
        st.info("Upload your Inventory files for HK, USA, and IND to see the summary.")
