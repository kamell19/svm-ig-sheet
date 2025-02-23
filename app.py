import streamlit as st
import pandas as pd
from model import get_all_drugs, get_drug_info, svm_predict, add_new_drug_data
import streamlit_authenticator as stauth

# Login menu (assuming Streamlit-Authenticator or similar is used)
authenticator = stauth.Authenticate(
    credentials={"admin": {"password": "adminpass"}}, # Replace with actual authentication setup
    cookie_name="admin_cookie",
    key="admin_key",
    cookie_expiry_days=30
)

# Set page config with title and layout
st.set_page_config(page_title="Ask a Medicine", page_icon="💊", layout="wide")
# Custom CSS for styling
st.markdown(
    """
    <style>
        body {
            background-color: #f5f7fa;
        }
        .stSidebar {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        .stSidebar .markdown-text-container {
            text-align: center !important;
            width: 100%;
        }
        .sidebar-logo {
            display: block;
            margin: auto;
        }
        .sidebar-title {
            font-size: 20px;
            font-weight: bold;
        }
        .sidebar-subtitle {
            font-size: 16px;
            font-weight: normal;
        }
        .stButton>button {
            background-color: #1f77b4;
            color: white;
            border-radius: 8px;
            border: 2px solid white;
            padding: 8px 15px;
            width: 100%;
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
            border: 1px solid #1f77b4;
            padding: 10px;
        }
        .stDataFrameContainer .dataframe {
            text-align: left;
            white-space: normal !important;
            word-wrap: break-word !important;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            word-wrap: break-word;
            white-space: normal;
        }
        th {
            background-color: #1f77b4;
            color: white;
            text-align: center !important;
        }
        td {
            text-align: left;
        }
        .feature-box {
            border: 2px solid #1f77b4;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #ffffff;
        }
        .predict-button {
            background-color: #ff6f61 !important;
            color: white;
            border-radius: 8px;
            padding: 5px 10px !important;
            font-size: 14px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar Layout
with st.sidebar:
    st.image("logo-unud.png", width=80, use_container_width=True, output_format="PNG")
    if st.button("Admin Login"):
        username, password = authenticator.login()
        if username:
            st.session_state["admin_logged_in"] = True
            st.sidebar.success(f"Welcome, {username}")
        else:
            st.sidebar.warning("Please enter username and password.")
    elif "admin_logged_in" in st.session_state and st.session_state["admin_logged_in"]:
        st.sidebar.success("Admin logged in.")
    else:
        st.sidebar.warning("Admin not logged in.")


# Title of the application
st.title("💊 Ask a Medicine")
st.subheader(
    "Your Personal Assistant for Drug Reviews & Side Effect Predictions")

# Button selection layout
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Home"):
        st.session_state["menu"] = "home"
with col2:
    if st.button("Review Side Effect"):
        st.session_state["menu"] = "side_effect"
with col3:
    if st.button("Review Classification"):
        st.session_state["menu"] = "classification"
with col3:
    if st.button("Admin Panel"):
        st.session_state["menu"] = "admin_panel"

# Initialize session state
if "menu" not in st.session_state:
    st.session_state["menu"] = "home"

# Display content based on selected button
if st.session_state["menu"] == "home":
    st.header("📋 List of Available Drugs")
    drug_list = get_all_drugs()
    if drug_list:
        grouped_drugs = {}
        for drug in drug_list:
            initial = drug[0].upper()
            if initial not in grouped_drugs:
                grouped_drugs[initial] = []
            grouped_drugs[initial].append(drug)

        for initial, drugs in sorted(grouped_drugs.items()):
            st.subheader(f"🔤 {initial}")

            # Buat 5 kolom
            cols = st.columns(5)

            # Tampilkan obat secara horizontal dalam 5 kolom
            for i, drug in enumerate(drugs):
                cols[i % 5].markdown(f"- **{drug}**")
    else:
        st.warning("⚠️ No medicines found.")

# Display content based on selected button
elif st.session_state["menu"] == "side_effect":

    st.header("Review Side Effect")
    drug_name = st.text_input("🔎 Search for a Drug",
                              placeholder="Enter drug name...")

    if drug_name:
        drug_info = get_drug_info(drug_name)

        if not drug_info.empty:
            st.subheader(f"📝 Drug Review for: {drug_name}")

            review_data = drug_info[[
                'condition', 'sideEffects', 'sideEffectsReview', 'commentsReview']].copy()
            review_data.reset_index(drop=True, inplace=True)
            review_data.index += 1  # Set index to start from 1
            review_data.insert(0, "No", review_data.index)

            # Convert DataFrame to HTML with center-aligned headers
            html_table = review_data.to_html(
                escape=False, index=False, classes="table table-striped")

            # Add CSS to center align the column headers
            html_table = html_table.replace(
                '<th>', '<th style="text-align:center;">')

            st.markdown(html_table, unsafe_allow_html=True)

        else:
            st.warning("⚠️ No drug found with that name.")

    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state["menu"] == "classification":

    st.header("Review Classification")
    review_text = st.text_area(
        "📝 Enter a drug review", placeholder="Type your review here...")

    if st.button("🔍 Predict", key="predict_button", help="Click to predict side effect severity"):
        if review_text:
            prediction = svm_predict(review_text)
            st.success(
                f"✅ **Predicted Side Effect Severity:** {prediction} Side Effect")
        else:
            st.error("⚠️ Please enter a review first.")

    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state["menu"] == "admin_panel":
    if "admin_logged_in" in st.session_state and st.session_state["admin_logged_in"]:
        st.header("🔧 Admin Panel")
        st.subheader("Current Drug Data")

        # Show the drug data in a table
        drug_data = pd.DataFrame(df)
        st.dataframe(drug_data)

        st.subheader("Add New Drug Data")

        # Input fields for adding new drug data
        urlDrugName = st.text_input("Drug Name (URL format)")
        condition = st.text_input("Condition")
        sideEffects = st.text_area("Side Effects")
        sideEffectsReview = st.text_area("Side Effects Review")
        commentsReview = st.text_area("Comments Review")

        if st.button("Add Drug"):
            if urlDrugName and condition and sideEffects and sideEffectsReview and commentsReview:
                # Add new drug data to Google Sheets
                message = add_new_drug_data(urlDrugName, condition, sideEffects, sideEffectsReview, commentsReview)
                st.success(message)
            else:
                st.error("⚠️ Please fill in all the fields.")