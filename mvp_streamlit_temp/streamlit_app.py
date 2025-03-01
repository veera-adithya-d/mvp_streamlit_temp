import os
import streamlit as st
import time
from datetime import datetime
from streamlit_lottie import st_lottie

import scripts.streamlit_helpers as st_helpers
from scripts.analysis import AnalyseBatch
from scripts.decision import GenerateOfferLetter, EmailOfferLetter
from scripts.helpers import DatatableToDataframe, VerifyInputRequirements

# SITE CONFIGURATION
st.set_page_config(
    page_title="CDF - AI HR",
    page_icon="👋",
    layout="wide"
)

# STATIC DIRECTORY REFERENCES
if "offer_letter_templates_dir" not in st.session_state:
    #st.session_state.offer_letter_templates_dir = os.getenv("offer_letter_templates_directory")
    st.session_state.offer_letter_templates_dir = './offer_letter_templates/'
if "volunteer_waiver" not in st.session_state:
    #st.session_state.volunteer_waiver = os.getenv("volunteer_waiver")
    st.session_state.volunteer_waiver = './CDF Volunteer Waiver.docx'

# SESSION STATE VARIABLES
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Resume Analysis" # Value for current display tab. Default: Resume Analysis
if "resumes_input" not in st.session_state:
    st.session_state.resumes_input = None # Stores uploaded resume documents
if "job_description_input" not in st.session_state:
    st.session_state.job_description_input = None # Stores uploaded job description document
if "applicants_datatable" not in st.session_state:
    st.session_state.applicants_datatable = None # Stores complete tool results for each applicant in table format
if "applicants_dataframe" not in st.session_state:
    st.session_state.applicants_dataframe = None # Stores reduced tool results for each applicant in dataframe format
if "flagged_applicant" not in st.session_state:
    st.session_state.flagged_applicant = None # Stores flagged applicant in session for other pages
if "offer_letter" not in st.session_state:
    st.session_state.offer_letter = None # Stores generated offer letter file in bytes format

# EXPERIMENTAL KEY VALUE TO CLEAR FILE UPLOADS
if "resume_input_component_key" not in st.session_state:
    st.session_state.resume_input_component_key = 1
if "job_description_input_component_key" not in st.session_state:
    st.session_state.job_description_input_component_key = 10000

# TITLE + PAGE NAVIGATION
title_col, resume_button_col, offer_button_col, _ = st.columns([2, 2, 2, 8], gap="small", vertical_alignment="bottom")
with title_col:
    st.image("./frontend/logo-dark.png", width=180)
with resume_button_col:
    st.button("Resume Analysis", use_container_width=True, type="tertiary", on_click=st_helpers.go_to_resume_analysis_page)
with offer_button_col:
    st.button("Offer Letter Generation", use_container_width=True, type="tertiary", on_click=st_helpers.go_to_offer_letter_generation_page)
st.divider()

# RESUME ANALYSIS PAGE CONTENT
if st.session_state.current_tab == "Resume Analysis":
    app_info_col, blank_col_0, input_documents_col = st.columns([5,1,4])
    with app_info_col.empty():
        st.image("./frontend/homepage.png", width=1400)
    blank_col_0.empty()
    with input_documents_col.empty():
        with st.container(border=False, key="input_documents", height=650):
            heading_col, results_col, clear_col = st.columns([6,3,2], vertical_alignment="center")
            with heading_col:
                st.markdown("#### File uploads")
            with results_col:
                st.button("📄 Results", use_container_width=True, on_click=st_helpers.go_to_results_page, key="go_to_results", type="secondary")
            with clear_col:
                st.button("⛔ Clear", use_container_width=True, on_click=st_helpers.clear_resume_analysis, key="clear_resume_analysis", type="secondary")
            st.session_state.resumes_input = st.file_uploader("Upload up to 10 resumes (.PDF or .TXT)", accept_multiple_files=True, type=['pdf', 'txt'], key=st.session_state.resume_input_component_key)
            st.session_state.job_description_input = st.file_uploader("Upload job description (.TXT)", type='txt', key=st.session_state.job_description_input_component_key)

            if st.button("Submit", use_container_width=True, type="primary"):
                if VerifyInputRequirements(st.session_state.resumes_input, st.session_state.job_description_input):
                    st_helpers.go_to_processing_page()
                    st.rerun()
                    

# PROCESSING PAGE CONTENT
elif st.session_state.current_tab == "Processing":
    st.session_state.applicants_datatable = AnalyseBatch(st.session_state.resumes_input, st.session_state.job_description_input, "Gemini")
    if st.session_state.applicants_datatable:
        st.session_state.applicants_dataframe = DatatableToDataframe(st.session_state.applicants_datatable)
        st_helpers.go_to_results_page()
        st.rerun()
    

# RESULTS PAGE CONTENT
elif st.session_state.current_tab == "Results":
    table_col, blank_col_3, detailed_col = st.columns([4,1,5])
    with table_col:
        # CONTAINER: output_score_table
        with st.container(border=False, key="output_score_table", height=650):
            st.markdown("##### Comparison table")
            if st.session_state.applicants_dataframe is not None: 
                st.dataframe(data=st.session_state.applicants_dataframe, use_container_width=True)
            else: 
                st.info("Upload upto 10 resumes, a job description and click submit to view comparison table")
    
    with detailed_col:
        # CONTAINER: detailed_analysis
        with st.container(border=False, key="detailed_analysis", height=550):
            st.markdown("##### Detailed Analysis")
            if st.session_state.applicants_datatable:
                dropdown_col, flag_col = st.columns([4,1], vertical_alignment="bottom")
                with dropdown_col:
                    applicant_index = st.selectbox("Select an applicant for more information", [applicant_row["name"] for applicant_row in st.session_state.applicants_datatable])
                selected_applicant_row = next(applicant_row for applicant_row in st.session_state.applicants_datatable if applicant_row["name"] == applicant_index)
                with flag_col:
                    if st.button("Accept", use_container_width=True, type="primary"):
                        st.session_state.flagged_applicant = selected_applicant_row

                st.text(f"Message: {selected_applicant_row['status']}")
                st.text(f"Similarity score: {selected_applicant_row['similarity_score']}")
                st.text(f"Matching skills: {selected_applicant_row['matching_skills']}")
                st.text(f"Experience: {selected_applicant_row['experience']}")
                st.text(f"Education: {selected_applicant_row['education']}")
                st.text(f"Strengths: {selected_applicant_row['strengths']}")
                st.text(f"Decision: {selected_applicant_row['tool_response']}")
            else:
                st.info("Upload upto 10 resumes, a job description and click submit to view detailed analysis")
        
        blank_col_4, next_col = st.columns([4,1])
        with next_col:
            st.button("Next", use_container_width=True, type="secondary", on_click=st_helpers.go_to_offer_letter_generation_page)

# OFFER LETTER GENERATION PAGE CONTENT
elif st.session_state.current_tab == "Offer Letter Generation":
    contact_col, output_documents_col = st.columns(2)
    with contact_col:
        # CONTAINER: contact_information
        with st.container(border=False, key="contact_information", height=320):
            heading_col, results_col, clear_col = st.columns([3,1,1], vertical_alignment="center")
            with heading_col:
                st.markdown("##### Applicant Contact")
            with results_col:
                st.button("📄 Results", use_container_width=True, on_click=st_helpers.go_to_results_page, key="go_to_results", type="secondary")
            with clear_col:
                st.button("⛔ Clear", use_container_width=True, on_click=st_helpers.clear_applicant_contact, key="clear_applicant_contact", type="secondary")
            # Name input
            if st.session_state.flagged_applicant:
                name_input = st.text_input("Applicant Name", value=f"{st.session_state.flagged_applicant['name']}")
                email_input = st.text_input("Applicant Email", value=f"{st.session_state.flagged_applicant['email']}")
            else:
                name_input = st.text_input("Applicant Name")
                email_input = st.text_input("Applicant Email")
            # Email input
            
            # Phone input
            extension_col, number_col = st.columns([4, 10], gap="small")
            with extension_col:
                phone_extensions = [
                    "+1",  # United States, Canada
                    "+44",  # United Kingdom
                    "+91",  # India
                    "+86",  # China
                    "+81",  # Japan
                    "+61",  # Australia
                    "+55",  # Brazil
                    "+7",   # Russia
                    "+52",  # Mexico
                    "+49",  # Germany
                    "+33",  # France
                    "+34",  # Spain
                    "+39"   # Italy
                ]
                selected_extension = st.selectbox("Phone", phone_extensions, key="extension", index=0)
            with number_col:
                if st.session_state.flagged_applicant:
                    number = st.text_input("Number", value=f"{st.session_state.flagged_applicant['phone']}", label_visibility="hidden")
                else:
                    number = st.text_input("Number", label_visibility="hidden")

            # Combine phone number and extension
            phone_input = f"{selected_extension}{number}"
        
        # CONTAINER: management_decision 
        with st.container(border=False, key="management_decision", height = 300):
            # Management Decision
            st.markdown("##### Management Decision")
            management_decision = st.radio("decision", ("Schedule interview", "Offer position"), key="decision", label_visibility="collapsed", index=1)

            if management_decision == "Schedule interview":
                st.error("This feature is not available in the current version of application.")

                with output_documents_col:
                    # CONTAINER: resume_preview
                    with st.container(border=True, key="resume_preview", height=650):
                        st.info("Placeholder for resume preview. Not available in the current version of application.")


            if management_decision == "Offer position":
                start_date_input = st.date_input("Start Date", value=datetime.today())
                hours_per_week_input = st.number_input("Minimum Hours per Week", min_value=0, step=1)

                with output_documents_col:
                    # CONTAINER: offer_letter
                    with st.container(border=False, key="offer_letter", height=650):
                        st.markdown("##### Offer letter")
                        # Job role selection
                        try:
                            filenames = os.listdir(st.session_state.offer_letter_templates_dir)
                            offer_letter_templates = [file for file in filenames if os.path.isfile(os.path.join(st.session_state.offer_letter_templates_dir, file)) and file.endswith(".docx")]
                        except FileNotFoundError:
                            offer_letter_templates = []
                            st.error(f"Specified directory: {st.session_state.offer_letter_templates_dir} not found. Please update the path")
                        
                        template_job_pairs = [
                            (file, file.split('-')[-1].replace('.docx', '').replace('_', ' ')) 
                            for file in offer_letter_templates
                        ]
                        template_job_pairs.sort(key=lambda x: x[1])
                        offer_letter_templates, job_roles = zip(*template_job_pairs) if template_job_pairs else (None, None)

                        if offer_letter_templates:
                            job_role_input = st.selectbox("Job Role", job_roles)
                            offer_letter_template = offer_letter_templates[job_roles.index(job_role_input)]
                        else:
                            offer_letter_template = None
                            st.error("Templates in the required format .DOCX not found. Please update the repository.")

                        generate_col, email_col = st.columns([3,2])
                        if generate_col.button("Generate", use_container_width=True, type="primary"):
                            if name_input and start_date_input and hours_per_week_input and offer_letter_template:
                                st.session_state.offer_letter = GenerateOfferLetter(
                                    os.path.join(st.session_state.offer_letter_templates_dir, offer_letter_template),
                                    name_input,
                                    start_date_input,
                                    job_role_input,
                                    hours_per_week_input
                                )
                                if st.session_state.offer_letter:
                                    st.download_button(
                                        label="Download .DOCX",
                                        data=st.session_state.offer_letter,
                                        file_name=f"{name_input} CDF Offer Letter - {job_role_input}.docx",
                                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    )
                            else:
                                st.warning("Required inputs missing. Offer letter might consist errors.")

                        if email_col.button("Email", icon="📧", use_container_width=True, type="secondary"):
                            if st.session_state.offer_letter:
                                if EmailOfferLetter(st.session_state.offer_letter, st.session_state.volunteer_waiver, name_input, email_input, job_role_input):
                                    st.session_state.offer_letter=None
                            else:
                                st.error("Offer letter not found. Please generate and validate manually it first")
                


