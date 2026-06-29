import streamlit as st
import requests
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# Constants
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
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

# Enterprise Dashboard Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Primary confirm action button */
div.stButton > button {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.7rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

div.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4) !important;
}

/* Input elements styling */
div[data-baseweb="input"] {
    background-color: rgba(128, 128, 128, 0.03) !important;
    border: 1px solid rgba(128, 128, 128, 0.15) !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
div[data-baseweb="input"]:focus-within {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
}

/* Text area styling */
div[data-baseweb="textarea"] {
    background-color: rgba(128, 128, 128, 0.03) !important;
    border: 1px solid rgba(128, 128, 128, 0.15) !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
div[data-baseweb="textarea"]:focus-within {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15) !important;
}

/* Radio button items container */
div[data-testid="stRadio"] > label {
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] {
    gap: 12px !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] {
    background-color: rgba(128, 128, 128, 0.03) !important;
    border: 1px solid rgba(128, 128, 128, 0.15) !important;
    padding: 8px 18px !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover {
    border-color: #4F46E5 !important;
    background-color: rgba(79, 70, 229, 0.04) !important;
}

/* High contrast View Files and View Spreadsheet link buttons */
div.stLinkButton > a {
    background-color: rgba(79, 70, 229, 0.06) !important;
    color: #4F46E5 !important;
    border: 1px solid rgba(79, 70, 229, 0.3) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.2s ease !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
}
div.stLinkButton > a:hover {
    background-color: rgba(79, 70, 229, 0.12) !important;
    border-color: #4F46E5 !important;
    transform: translateY(-1px) !important;
}

/* File uploader styling */
div[data-testid="stFileUploader"] {
    border: 1px dashed rgba(79, 70, 229, 0.25) !important;
    border-radius: 10px !important;
    padding: 1.5rem !important;
    background-color: rgba(79, 70, 229, 0.01) !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stFileUploader"]:hover {
    border-color: #4F46E5 !important;
    background-color: rgba(79, 70, 229, 0.03) !important;
}
</style>
""", unsafe_allow_html=True)

# Sleek Navbar Header
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 1.2rem 0; border-bottom: 1px solid rgba(128,128,128,0.18); margin-bottom: 1.8rem;">
    <div style="font-weight: 800; font-size: 1.8rem; letter-spacing: -0.5px; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">🧾 InvoiceProcessor.ai</div>
    <div style="font-size: 0.85rem; color: #6B7280; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase;">Corporate Hub</div>
</div>
""", unsafe_allow_html=True)

# Minimalist workflow legend
st.markdown("""
<div style="background-color: rgba(128,128,128,0.02); border: 1px solid rgba(128,128,128,0.08); padding: 1rem; border-radius: 10px; margin-bottom: 1.8rem;">
    <span style="font-weight: 600; font-size: 0.85rem; color: #4B5563; display: block; margin-bottom: 0.4rem; text-transform: uppercase; letter-spacing: 0.5px;">Processing Workflow</span>
    <div style="display: flex; gap: 15px; font-size: 0.85rem; color: #6B7280; flex-wrap: wrap;">
        <div><b>1. Select</b>: Upload file or capture photo</div>
        <div style="color: #A855F7;">•</div>
        <div><b>2. Verify</b>: Review details side-by-side with preview</div>
        <div style="color: #A855F7;">•</div>
        <div><b>3. Export</b>: Save data to Google Sheet</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Choose Input Source
input_source = st.radio("Choose Input Method:", ["📁 Upload File", "📸 Take Photo"], horizontal=True)

if "Upload File" in input_source:
    uploaded_file = st.file_uploader(
        "Upload an invoice image or PDF document",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Supports JPEG, PNG, and PDF files"
    )
else:
    uploaded_file = st.camera_input("Take a photo of the invoice")

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
                    import json
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
                import base64
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
                    st.success("✅ Upload Successfully")
                else:
                    with st.spinner("📤 Transmitting webhook payload..."):
                        try:
                            # 3. Post it all together to Make
                            response = requests.post(MAKE_WEBHOOK_URL, data=payload_data, files=payload_files)
                            if response.status_code in [200, 201, 202]:
                                st.success("🎉 Upload Successfully")
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
