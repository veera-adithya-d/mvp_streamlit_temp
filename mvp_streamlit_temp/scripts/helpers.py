import google.generativeai as genai
import os
import pandas as pd
import psutil
import PyPDF2
import re
import streamlit as st
import torch
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModel

""" Documents upload verification"""
def VerifyInputRequirements(resumes_list, job_description):
    if not resumes_list:
        st.error("No resumes uploaded.")
        return False

    elif len(resumes_list) > 10:
        st.error("Upload only upto 10 resumes.")
        return False

    elif not job_description:
        st.error("No job description uploaded.")
        return False
    
    return True

""" Text processor functions """
def ReadFromPDF(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ''.join(page.extract_text() for page in pdf_reader.pages)
    return text

def ReadFromText(text_file):
    return text_file.getvalue().decode("utf-8")

def TextToCommaSeperated(text):
    text = text.lower()
    text = re.sub(r"\*", "", text)
    # Remove subheadings (Skills, Experience, Education)
    text = re.sub(r"(skills|experience|education):", "", text)
    text = re.sub(r"[.,:]", ",", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r",\s*", ",", text)

    return text

""" Text extractor functions """
def PersonalInformationExtractor(text):
    # Regex patterns for email and phone
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\+?\d[\d -]{8,12}\d'

    # Attempt to extract contact details
    email = re.search(email_pattern, text)
    phone = re.search(phone_pattern, text)

    # Extract Name (assuming first line of the resume might be the name)
    name = text.splitlines()[0].strip() if text else "Name Not Found"

    return {
        "name": name,
        "email": email.group() if email else "Email Not Found",
        "phone": phone.group() if phone else "Contact Not Found"
    }

def ExcellencyExtractor(text):

    excellency_pattern = r"Experience:\s*(.*?)\n\nEducation:\s*(.*?)(?=\n|$)"
    strengths_pattern = r"Strengths:\s*(?:- )?([\s\S]*?)(?=\nWeaknesses:|\n$)"
    weaknesses_pattern = r"Weaknesses:\s*(?:- )?([\s\S]*?)$"

    match = re.search(excellency_pattern, text, re.DOTALL)
    if match:
        years_of_experience = match.group(1)
        education = match.group(2).strip()
    else:
        years_of_experience = "0"
        education = "No education found"

    strengths_match = re.search(strengths_pattern, text, re.DOTALL)
    strengths = [s.strip() for s in strengths_match.group(1).strip().split("\n- ")] if strengths_match else []

    weaknesses_match = re.search(weaknesses_pattern, text, re.DOTALL)
    weaknesses = [w.strip() for w in weaknesses_match.group(1).strip().split("\n- ")] if weaknesses_match else []

    return years_of_experience, education, strengths, weaknesses


def GenAITextExtractor(text, technology):
    if technology == "Gemini":
        prompt = f"""Act as a efficient ATS system. Summarize the text into data suitable for input to a RoBERTa model and in following format
Skills: List skills here (Technical and Soft-skills), \n
Experience: Provide the total years of experience, followed by the most relevant title based on the text. Include only one title, ensuring it aligns with the primary expertise area.
Education: Summarize academic qualifications by listing the highest degree achieved. For candidates with dual degrees, mention only the highest. Replace abbreviations with full degree names (e.g., Bachelors, Masters). Do not include the field of study.
Strengths: Identify three key strengths derived from the candidate's skills, experience, and notable achievements.
- [Strength 1, Concise and impactful]
- [Strength 2, Concise and impactful]
- [Strength 3, Concise and impactful]
Guidelines:
Ensure output is concise, adhering to the specified format.
Avoid repetition, and focus on relevant details only.
Do not include unnecessary commentary or additional formatting.Text: {text}"""
        genai.configure(api_key=st.secrets.gemini.api_key)
        # Selecting a gemini model depending on the plan (Free in this instance)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count = 1,
                max_output_tokens = 512,
                temperature = 0.5
            )
        )
        print(response.text)
        return response.text

""" Text similarity functions """
"""
def CalculateResumeSimilarity(resume_text, job_description_text):
    #Calculates similarity score between resume and job description.
    model_name = "cross-encoder/stsb-roberta-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    text_matching_model = AutoModelForSequenceClassification.from_pretrained(model_name)


    inputs = tokenizer(resume_text, job_description_text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = text_matching_model(**inputs)
        similarity_score = torch.sigmoid(outputs.logits).item()
    return similarity_score
"""

def CalculateResumeSimilarity(resume_text, job_description_text):
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    def get_embeddings(text):
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        outputs = model(**inputs)
        
        return outputs.last_hidden_state.mean(dim=1)
    
    resume_embeddings = get_embeddings(resume_text)
    job_description_embeddings = get_embeddings(job_description_text)

    similarity = cosine_similarity(resume_embeddings.detach().numpy(), job_description_embeddings.detach().numpy())
    return similarity[0][0]

# --- Fit Categorization ---
def CategorizeFit(similarity_score):
    """Categorizes fit based on similarity score."""
    fit_percentage = similarity_score * 100
    if fit_percentage >= 75:
        return "a good fit", fit_percentage
    elif fit_percentage >= 60:
        return "a moderate fit", fit_percentage
    else:
        return "not a good fit", fit_percentage

# --- Communication Generation ---
def CommunicationGenerator(message, fit_category):
    """Generates a communication response based on the input message and fit category."""
    #return (f"{message}"
            #f"This candidate is considered a {fit_category}.")
    return f"This candidate is considered {fit_category}."

# --- Resource Monitoring ---
def GetResourceUsage():
    """Retrieves resource usage information."""
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_consumed = memory_info.rss / (1024 ** 2)
    return memory_consumed

def DatatableToDataframe(data):
    return pd.DataFrame([
        {
            "Filename": applicant["filename"],
            "Status": "✅" if applicant["status"]=="Success" else "❗",
            "Name": applicant["name"],
            "Similarity score": applicant["similarity_score"],
        }
        for applicant in data
    ]).set_index("Name")
