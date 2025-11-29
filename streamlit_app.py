import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

# -------------- PAGE NAVIGATION -------------------
if "page" not in st.session_state:
    st.session_state.page = "main"

def go_to_message_page():
    st.session_state.page = "message"

# --------------------------------------------------

if st.session_state.page == "main":

    st.set_page_config(page_title="Customer Payment Assistant")

    st.title("Customer Payment Assistant")

    use_hardcoded = st.checkbox("Use hardcoded ID", value=False)
    HARDCODED_ID = "E00789"

    if use_hardcoded:
        customer_id = HARDCODED_ID
        st.info(f"Using hardcoded ID: {customer_id}")
    else:
        customer_id = st.text_input("Enter Customer ID")

    if st.button("Proceed"):
        if not customer_id:
            st.warning("Please enter an ID.")
        else:
            try:
                # Call backend generate endpoint only
                gen = requests.get(f"{API_BASE}/generate/{customer_id}", timeout=10).json()

                # Save data in session_state
                st.session_state.generated_message = gen
                st.session_state.customer_id = customer_id

                # Navigate to message page
                go_to_message_page()
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

# ---------------- MESSAGE PAGE ---------------------

elif st.session_state.page == "message":

    st.title("Generated Message")

    gen = st.session_state.get("generated_message", {})
    customer_id = st.session_state.get("customer_id", "Unknown")

    email = gen.get("email", {})
    subject = email.get("subject", "No Subject")
    body = email.get("body", "No Message Body")

    st.subheader("Subject:")
    st.write(subject)

    st.subheader("Message:")
    st.text_area("Body", body, height=300)

    if st.button("Back"):
        st.session_state.page = "main"
        st.rerun()
