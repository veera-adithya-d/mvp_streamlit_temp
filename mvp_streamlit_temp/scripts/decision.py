import os
import re
import smtplib
import streamlit as st
import time
from datetime import datetime
from docxtpl import DocxTemplate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO

def EmailOfferLetter(offer_letter, volunteer_waiver, applicant_name, applicant_email, job_role):
    with st.status("Emailing offer letter...", expanded=True) as status:
        port = 587 #Default port for GMAIL TLS
        smtp_server = "smtp.gmail.com"
        st.write("Fetching authentication details...")
        time.sleep(1)
        sender_email = st.secrets.google.account_email
        password = st.secrets.google.account_password
        if not sender_email or not password:
            status.update(label=f"Authentication records not found. Set environmental variables/secrets: account_email, account_password", state="error", expanded=False)
            return False
        
        st.write("Processing input fields.")
        time.sleep(1)
        applicant_name = re.sub(r'[^a-zA-Z0-9 ]', '', applicant_name)
        offer_letter_filename = f"{applicant_name} CDF Offer Letter - {job_role}.docx"
        volunteer_waiver_filename = "CDF Volunteer Waiver.docx"

        if not applicant_email:
            status.update(label="Applicant email required!", state="error", expanded=False)
            return False
        st.write("Generating email body...")
        time.sleep(1)
        body = f"""Hello {str(applicant_name)},\n\nWe are delighted to welcome you to the Community Dreams Foundation!\n
To ensure a smooth onboarding process, please find attached the necessary documents required for your employment.\n
Kindly review, fill out, sign, and return these documents to us at your earliest convenience. You can simply reply to this email with the completed documents attached. If the start date in the offer letter needs to be changed, please update in the word document and share the signed copies with us. After sharing the documents, you'll receive an invitation to join our Slack channel. Please remain vigilant for any email notifications regarding further instructions.\n
Should you have any questions or need further clarification on any of the documents, please don't hesitate to contact us.\n
Regards\nAI Applicant Tracking System"""

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = applicant_email
        message["Subject"] = "Test Mail: Welcome to Community Dreams Foundation! Important Onboarding Documents Attached"
        message.attach(MIMEText(body, "plain"))

        try:
            st.write("Attaching documents: offer letter, volunteer waiver.")
            time.sleep(1)
            mime_attachment = MIMEBase("application", "octet-stream")
            # Attach offer letter
            mime_attachment.set_payload(offer_letter.getvalue())
            encoders.encode_base64(mime_attachment)
            mime_attachment.add_header(
                "Content-Disposition",
                "attachment; filename=%s" % offer_letter_filename,
            )
            message.attach(mime_attachment)

            # Attach volunteer waiver
            mime_attachment = MIMEBase("application", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with open(volunteer_waiver, "rb") as attachment_file:
                mime_attachment.set_payload(attachment_file.read())

            encoders.encode_base64(mime_attachment)
            mime_attachment.add_header(
                "Content-Disposition",
                "attachment; filename=%s" % volunteer_waiver_filename,
            )
            message.attach(mime_attachment)

            with smtplib.SMTP(smtp_server, port) as server:
                st.write("Connecting to network!")
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, applicant_email, message.as_string())
                server.quit()
                status.update(label="Email sent successfully. Deleting offer letter from session for security purposes.", state="complete")
                return True

        except smtplib.SMTPAuthenticationError:
            status.update(label="SMTP authentication error. Check username and password", state="error", expanded=False)
            return False

        except Exception as e:
            status.update(label=f"Error occured when sending email: {str(e)}", state="error", expanded=True)
            return False
    

def GenerateOfferLetter(offer_letter_template, applicant_name, start_date, job_role, hours_per_week):
    
    with st.status("Tailoring document...", expanded=True) as status:
        """Generates an offer letter from a template."""
        st.write("Fetching template...")
        time.sleep(1)

        if not os.path.exists(offer_letter_template):
            status.update(label="No file found! Please add a file in a valid .docx format.", state="error", expanded=False)
            return None

        st.write("Processing input fields.")
        time.sleep(1)
        applicant_name = re.sub(r'[^a-zA-Z0-9 ]', '', applicant_name)
        context = {
            'candidate_name': applicant_name,
            'role': job_role,
            'hours': hours_per_week,
        }

        context['start_date'] = start_date
        st.write("Filling in the details.")
        time.sleep(1)
        try:
            # Read the content of the uploaded file
            tpl = DocxTemplate(offer_letter_template)
            tpl.render(context)

            offer_letter_bytes = BytesIO()

            tpl.save(offer_letter_bytes)
            offer_letter_bytes.seek(0)
            status.update(label="Generation complete!", state="complete")
            return offer_letter_bytes

        except Exception as e:
            status.update(label=f"Error occured during offer letter generation: {str(e)}", state="error", expanded=True)
            return None
