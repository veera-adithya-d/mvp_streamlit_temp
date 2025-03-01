import json
import requests
import streamlit as st
from .helpers import VerifyInputRequirements

# SESSION STATE DELETION FUNCTIONS
def clear_resume_analysis():
    st.session_state.resume_input_component_key += 1
    st.session_state.job_description_input_component_key += 1
    st.session_state.applicants_datatable = None
    st.session_state.applicants_dataframe = None
    st.session_state.flagged_applicant = None

def clear_applicant_contact():
    st.session_state.flagged_applicant = None
    st.session_state.offer_letter = None

# SESSION STATE UPDATION FUNCTIONS
def go_to_resume_analysis_page():
    st.session_state.current_tab = "Resume Analysis"

def go_to_results_page():
    st.session_state.current_tab = "Results"

def go_to_processing_page():
    st.session_state.current_tab = "Processing"

def go_to_offer_letter_generation_page():
    st.session_state.current_tab = "Offer Letter Generation"

# LOTTIE FILES
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()