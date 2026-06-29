import streamlit as st
import requests
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import base64
import json

# Constants
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6KmF8cewEtMtz86zNbNfyj0rAZBT4MOffx6wqKafd68ow")
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/ayqyd31eyeyfo2lecr3q1enhioe3yjif"

# Define the expected JSON structure using Pydantic
class InvoiceData(BaseModel):
    company_name: str = Field(description="Name of the company/vendor issuing the invoice")
    invoice_number: str = Field(description="The unique invoice identifier/number")
    invoice_date: str = Field(description="The date of the invoice (e.g. YYYY-MM-DD)")
    total_amount: str = Field(description="The total invoice amount, including currency (e.g. $150.00)")
    line_items_summary: str = Field(description="A short, concise single-line description summarizing the items on the invoice")

# Configure Streamlit page layout and aesthetics
st.set_page_config(
    page_title="AI Invoice Processor",
    page_icon="🧾",
    layout="wide"
)

# Initialize active upload method in session state
if "upload_method" not in st.session_state:
    st.session_state.upload_method = "file"

# Redesigned minimalist interface styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Soft off-white background */
.stApp {
    background-color: #F8F9FA !important;
}

/* Card layout containers (st.container with border) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 16px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    padding: 1.5rem !important;
    margin-bottom: 1rem !important;
}

/* Typography styles */
.brand-title {
    font-weight: 800;
    font-size: 1.8rem;
    color: #0F172A;
    letter-spacing: -0.5px;
}

.brand-accent {
    color: #4F46E5;
}

/* Primary charcoal action buttons */
div.stButton > button {
    background-color: #0F172A !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
}

div.stButton > button:hover {
    background-color: #1E293B !important;
    transform: translateY(-1px) !important;
}

/* Choose Method selection buttons */
div.stButton > button[key*="select_"] {
    background-color: #ffffff !important;
    color: #4B5563 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 14px !important;
    height: 80px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    box-shadow: none !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
}
div.stButton > button[key*="select_"]:hover {
    border-color: #4F46E5 !important;
    background-color: rgba(79, 70, 229, 0.01) !important;
}

/* Native inputs and text areas */
div[data-baseweb="input"] {
    background-color: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    color: #0F172A !important;
    padding: 2px 4px !important;
    transition: all 0.2s ease !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
}

div[data-baseweb="textarea"] {
    background-color: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    color: #0F172A !important;
    padding: 2px 4px !important;
    transition: all 0.2s ease !important;
}
div[data-baseweb="textarea"]:focus-within {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
}

/* Link buttons (Google Drive & Sheets) styled as outline elements */
div.stLinkButton > a {
    width: 100% !important;
    background-color: #ffffff !important;
    color: #4B5563 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 0.7rem 1.2rem !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
}
div.stLinkButton > a:hover {
    background-color: #F9FAFB !important;
    border-color: #9CA3AF !important;
    color: #111827 !important;
}

/* File uploader container */
div[data-testid="stFileUploader"] {
    border: 2px dashed #E5E7EB !important;
    border-radius: 14px !important;
    padding: 2rem !important;
    background-color: #ffffff !important;
}
div[data-testid="stFileUploader"]:hover {
    border-color: #4F46E5 !important;
}

/* Mobile responsive padding constraints */
@media (max-width: 768px) {
    div[data-testid="column"] {
        margin-bottom: 2rem !important;
    }
    .stApp {
        padding: 12px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Dynamic borders for active input selector (electric indigo highlight #4F46E5)
if st.session_state.upload_method == "file":
    active_style = """
    <style>
    div.stButton > button[key*="select_file"] {
        border-color: #4F46E5 !important;
        background-color: rgba(79, 70, 229, 0.02) !important;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1) !important;
    }
    </style>
    """
else:
    active_style = """
    <style>
    div.stButton > button[key*="select_camera"] {
        border-color: #4F46E5 !important;
        background-color: rgba(79, 70, 229, 0.02) !important;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1) !important;
    }
    </style>
    """
st.markdown(active_style, unsafe_allow_html=True)

# Sleek Header Bar
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid #E5E7EB; margin-bottom: 1.8rem;">
    <div class="brand-title">🧾 Invoice<span class="brand-accent">Processor</span></div>
    <div style="font-size: 0.8rem; color: #6B7280; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;">Hub</div>
</div>
""", unsafe_allow_html=True)

# Minimalist workflow legend
st.markdown("""
<div style="background-color: #ffffff; border: 1px solid #E5E7EB; padding: 1rem; border-radius: 14px; margin-bottom: 1.8rem;">
    <span style="font-weight: 700; font-size: 0.8rem; color: #374151; display: block; margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.5px;">Instructions</span>
    <div style="display: flex; gap: 15px; font-size: 0.85rem; color: #6B7280; flex-wrap: wrap;">
        <div><b>1. Select Method</b>: Upload file or snap photo</div>
        <div style="color: #E5E7EB;">|</div>
        <div><b>2. Verify Details</b>: Review side-by-side with preview</div>
        <div style="color: #E5E7EB;">|</div>
        <div><b>3. Export</b>: Save details directly to Google Sheet</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Choose Input Source - Circular style choice buttons
st.markdown("### Choose Input Method")
with st.container(border=True):
    col_sel1, col_sel2 = st.columns(2, gap="medium")
    with col_sel1:
        if st.button("📁\n\nUpload File", key="select_file", use_container_width=True):
            st.session_state.upload_method = "file"
            st.rerun()
    with col_sel2:
        if st.button("📸\n\nTake Photo", key="select_camera", use_container_width=True):
            st.session_state.upload_method = "camera"
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# Render chosen uploader
if st.session_state.upload_method == "file":
    uploaded_file = st.file_uploader(
        "Upload an invoice document",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Supports PDF, PNG, and JPEG files"
    )
else:
    uploaded_file = st.file_uploader(
        "Snap a photo of the invoice",
        type=["jpg", "jpeg", "png"],
        help="Tapping 'Browse files' on a mobile phone will automatically prompt your native full-screen camera app."
    )

if uploaded_file is not None:
    # Build unique ID for current file based on its metadata to prevent API re-calls on UI adjustments
    file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if st.session_state.get("current_file_id") != file_id:
        with st.spinner("✨ Running extraction... Please wait..."):
            try:
                # Read raw file bytes safely
                file_bytes = uploaded_file.getvalue()
                
                # Instantiate new GenAI SDK client
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                # Perform structured content generation request
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        "Analyze this invoice file and extract the requested fields into a clean JSON structure.",
                        types.Part.from_bytes(
                            data=file_bytes,
                            mime_type=uploaded_file.type
                        )
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=InvoiceData,
                        temperature=0.1,
                    )
                )
                
                # Try parsing the result
                if hasattr(response, 'parsed') and response.parsed:
                    extracted: InvoiceData = response.parsed
                else:
                    # Fallback JSON parsing
                    parsed_json = json.loads(response.text)
                    extracted = InvoiceData(**parsed_json)
                
                # Set initial state fields to match the extracted values
                st.session_state.company_name = extracted.company_name
                st.session_state.invoice_number = extracted.invoice_number
                st.session_state.invoice_date = extracted.invoice_date
                st.session_state.total_amount = extracted.total_amount
                st.session_state.line_items_summary = extracted.line_items_summary
                
                # Update file tracker
                st.session_state.current_file_id = file_id
                # Reset success modal state for a new file
                if "upload_success" in st.session_state:
                    del st.session_state.upload_success
                st.success("✅ Extraction completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Extraction failed. Error detail: {str(e)}")
                # Initialize fields to empty if extraction failed
                if "company_name" not in st.session_state:
                    st.session_state.company_name = ""
                    st.session_state.invoice_number = ""
                    st.session_state.invoice_date = ""
                    st.session_state.total_amount = ""
                    st.session_state.line_items_summary = ""

    # Split screen into columns: Left = Preview, Right = Extracted Fields Form
    col_preview, col_form = st.columns([1, 1], gap="large")
    
    with col_preview:
        st.markdown("### Document Preview")
        with st.container(border=True):
            if uploaded_file.type == "application/pdf":
                # Convert PDF bytes to base64 to display the document itself
                base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" style="border: none; border-radius: 8px;"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.image(uploaded_file, caption="Captured Invoice", use_container_width=True)

    with col_form:
        # Form containing the input fields
        st.markdown("### Edit Extracted Fields")
        with st.container(border=True):
            # Check if upload was already successfully triggered to render the success block
            if st.session_state.get("upload_success"):
                st.markdown("""
                <div style="background-color: #ffffff; border: 1px solid #E5E7EB; border-radius: 16px; padding: 2rem; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.015); margin-top: 1rem; margin-bottom: 1.5rem;">
                  <div style="background-color: #ECFDF5; width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem auto; border: 1px solid #A7F3D0;">
                    <span style="font-size: 2rem; color: #059669;">✓</span>
                  </div>
                  <h3 style="margin-top: 0; margin-bottom: 0.5rem; color: #0F172A; font-weight: 700; font-size: 1.3rem;">Upload Successfully</h3>
                  <p style="color: #6B7280; font-size: 0.9rem; margin-bottom: 0;">The invoice data has been committed and sent to the spreadsheet database.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Option to edit or resend
                if st.button("🔄 Edit & Resubmit"):
                    del st.session_state.upload_success
                    st.rerun()
            else:
                # We bind Streamlit text inputs directly to key="company_name", etc.
                company_name = st.text_input("Company Name", key="company_name")
                invoice_number = st.text_input("Invoice Number", key="invoice_number")
                invoice_date = st.text_input("Invoice Date", key="invoice_date")
                total_amount = st.text_input("Total Amount", key="total_amount")
                line_items_summary = st.text_area("Line Items Summary", key="line_items_summary")

                st.markdown("---")

                # Send payload button
                if st.button("🚀 Confirm & Send to Sheet"):
                    # 1. Read the raw bytes of the uploaded invoice file
                    file_bytes = uploaded_file.getvalue()

                    # 2. Package BOTH the file and the text fields together
                    payload_files = {
                        'file': (uploaded_file.name, file_bytes, uploaded_file.type)
                    }
                    payload_data = {
                        'company_name': company_name,
                        'invoice_number': invoice_number,
                        'invoice_date': invoice_date,
                        'total_amount': total_amount,
                        'line_items_summary': line_items_summary
                    }
                    
                    # Check if Webhook URL is set
                    if MAKE_WEBHOOK_URL == "PASTE_YOUR_MAKE_WEBHOOK_URL_HERE" or not MAKE_WEBHOOK_URL.strip():
                        st.warning("⚠️ Make Webhook URL is not configured. Simulating payload submission.")
                        st.json(payload_data)
                        st.session_state.upload_success = True
                        st.rerun()
                    else:
                        with st.spinner("📤 Transmitting webhook payload..."):
                            try:
                                # 3. Post it all together to Make
                                response = requests.post(MAKE_WEBHOOK_URL, data=payload_data, files=payload_files)
                                if response.status_code in [200, 201, 202]:
                                    st.session_state.upload_success = True
                                    st.rerun()
                                else:
                                    st.error(f"❌ Upload Unsuccessfully\nHTTP Status: {response.status_code}\nResponse: {response.text}")
                            except Exception as e:
                                st.error(f"❌ Upload Unsuccessfully\nError during transmission: {str(e)}")

else:
    st.info("ℹ️ Please upload an invoice file or take a photo to extract details.")

# View Folders & Sheet buttons at the bottom of the page
st.markdown("---")
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    st.link_button("📂 View Files", "https://drive.google.com/drive/folders/1o60fsNB698Vm-qB1MtjelHN1epglbBlN?usp=sharing", use_container_width=True)
with col_btn2:
    st.link_button("📊 View Spreadsheet", "https://docs.google.com/spreadsheets/d/12xbIEF4dLtuEcsq1kqNi-5BdVXHgme8Qtdy-jmyGJPA/edit?usp=sharing", use_container_width=True)
