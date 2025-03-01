import os
import streamlit as st
from streamlit_lottie import st_lottie, st_lottie_spinner
from .helpers import ReadFromPDF, ReadFromText, PersonalInformationExtractor, GenAITextExtractor, ExcellencyExtractor, TextToCommaSeperated, CalculateResumeSimilarity, CategorizeFit, CommunicationGenerator
from .streamlit_helpers import load_lottiefile, go_to_resume_analysis_page

"""Analyzes the resume and job description."""
def AnalyseDocument(resume, analysed_job_description, technology):

    """TASK: PDF/DOCX FORMAT"""
    # Extract resume text based on the file type
    if os.path.splitext(resume.name)[1] == '.pdf':
        resume_text = ReadFromPDF(resume)
    if os.path.splitext(resume.name)[1] == '.txt':
        resume_text = ReadFromText(resume)
    
    """TASK: PERSONAL INFORMATION"""
    # Identify information: name, email, phone number from extracted resume text
    personal_info = PersonalInformationExtractor(resume_text)

    """TASK: PROMPT ENGINEERING"""
    analysed_resume = GenAITextExtractor(resume_text, technology)

    """TASK: EXPERIENCE, EDUCATION, STRENGTHS, WEAKNESSES"""
    years_of_experience, education, strengths, missing_skills = ExcellencyExtractor(analysed_resume)

    """TASK: JOB DESCRIPTION MATCHING"""
    # Identify matching skills
    resume_skill_set = TextToCommaSeperated(analysed_resume).split(',')
    job_description_skill_set = TextToCommaSeperated(analysed_job_description).split(',')
    matching_skills = list(set(resume_skill_set) & set(job_description_skill_set))
    missing_skills = list(set(job_description_skill_set).difference(set(resume_skill_set)))

    # Calculate similarity score USING PROCESSED RESUME TEXT AND JOB DESCRIPTION TEXT THAN JUST PDF EXTRACTED TEXT
    similarity_score = CalculateResumeSimilarity(analysed_resume, analysed_job_description)
    fit_category, fit_percentage = CategorizeFit(similarity_score)

    # Generate communication response
    communication_response = CommunicationGenerator(
        f"The candidate has the following skills: {', '.join(resume_skill_set)}.",
        fit_category
    )

    return (
        "Success",
        personal_info,
        f"{similarity_score*100:.2f}%",
        ", ".join(skill for skill in matching_skills if skill.strip()),
        years_of_experience,
        education,
        ", ".join(strengths),
        ", ".join(missing_skills),
        communication_response,
        ", ".join(resume_skill_set),
        ", ".join(job_description_skill_set),
    )

def AnalyseBatch(resumes_list, job_description, technology):
    blank_col_1, status_col, blank_col_2 = st.columns([1,3,1])
    blank_col_1.empty()
    blank_col_2.empty()
    
    with status_col:
        progress_bar = st.empty()
        _,squeezed_col,_ = st.columns(3)
        with squeezed_col:
            with st_lottie_spinner(load_lottiefile("./frontend/processing.json"), key="processing", width=0, height=500):
                try:
                    progress_bar.progress(0, text="Analysis in progress. Please wait.")
                    job_description_text = ReadFromText(job_description)
                    analysed_job_description = GenAITextExtractor(job_description_text, technology)

                    results = []
                    for idx, resume in enumerate(resumes_list):
                        progress_bar.progress(((idx+1)/len(resumes_list)), text="Analysis in progress. Please wait.")
                        status, contact, similarity_score, matching_skills, experience, education, strengths, missing_skills, tool_response, resume_skills, job_skills = AnalyseDocument(resume, analysed_job_description, technology)
                        results.append(
                            {
                                "filename": resume.name,
                                "status": status,
                                "name": contact["name"],
                                "email": contact["email"],
                                "phone": contact["phone"],
                                "similarity_score": similarity_score,
                                "matching_skills": matching_skills,
                                "experience": experience,
                                "education": education,
                                "strengths": strengths,
                                "missing_skills": missing_skills,
                                "tool_response": tool_response,
                            }
                        )
                    return results
                except Exception as e:
                    progress_bar.empty()
                    st.error(f"{str(e)}")
            st_lottie(load_lottiefile("./frontend/error.json"), key="error", loop=False, width = 0, height=200)
            st.button("Go back", use_container_width=True, type="primary", on_click=go_to_resume_analysis_page)
        return None
