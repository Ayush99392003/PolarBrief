import streamlit as st
from logic import DocumentProcessor
import os
import json
import zipfile
import io
from fpdf import FPDF
import unicodedata

# === UI Setup ===
st.set_page_config(page_title="Legal Argument Analyzer", layout="wide")

BACKGROUND_IMAGE_URL = "https://i.pinimg.com/736x/64/eb/ef/64ebefbbd558d77f1a1e0d01a4e050c1.jpg"


st.markdown(f"""
    <style>
        html, body, [class*="css"] {{
            font-family: 'Segoe UI', sans-serif;
            font-size: 18px;
            color: #222;
        }}
        .stApp {{
            background-image: url('{BACKGROUND_IMAGE_URL}');
            background-size: cover;
            background-attachment: fixed;
        }}
        .main-box {{
            background-color: green;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        .title-box {{
            background-color: #004466;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }}
        .title-box h1 {{
            color: white;
            font-size: 2.8em;
            margin: 0;
        }}
        .main-box h2 {{
            color: black;
            font-size: 1.4em;
            margin: 0;
        }}
        .section-header {{
            background-color: #F08080;
            padding: 12px 18px;
            border-left: 6px solid #007acc;
            border-radius: 6px;
            font-size: 1.4em;
            font-weight: bold;
            margin: 20px 0 10px 0;
        }}
        .stButton > button {{
            width: 100%;
            background-color: #007acc;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px;
            font-size: 1.05em;
        }}
        .stDownloadButton > button {{
            width: 100%;
            background-color: #007acc;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px;
            font-size: 1.05em;
        }}
        .stDownloadButton > button:hover {{
            background-color: #005f99;
            cursor: pointer;
        }}
    </style>
""", unsafe_allow_html=True)

# === Title ===
st.markdown('<div class="title-box"><h1>PolarBrief AI - Legal Argument Analyzer</h1></div>', unsafe_allow_html=True)

groq_api_key = os.getenv("GROQ_API_KEY")

# === Upload PDF ===
uploaded_file = st.file_uploader("📄 Upload PDF Document", type=["pdf"])

if uploaded_file is not None:
    temp_file = "temp_upload.pdf"
    with open(temp_file, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if st.button("Analyze Document"):
        if not groq_api_key:
            st.error("Please provide your GROQ API key.")
            st.stop()

        os.environ["GROQ_API_KEY"] = groq_api_key
        processor = DocumentProcessor()
        with st.spinner("🔍 Processing document..."):
            try:
                results = processor.process_document(
                    pdf_path=temp_file,
                    poppler_path=poppler_path,
                    tesseract_path=tesseract_path
                )

                # Save JSONs
                with open("legal_argument_analysis_ranked.json", "w", encoding="utf-8") as f:
                    json.dump(results["full_analysis"], f, indent=2)

                with open("top_10.json", "w", encoding="utf-8") as f:
                    json.dump(results["top_arguments"], f, indent=2)

                argument_minimal = [
                    {
                        "page": item.get("page", ""),
                        "citation": item.get("citation", ""),
                        "heading": item.get("heading", "")
                    }
                    for item in results["full_analysis"]
                ]
                with open("argument_minimal.json", "w", encoding="utf-8") as f:
                    json.dump(argument_minimal, f, indent=2)

                # === PDF Utilities ===
                def clean_text(text):
                    if not isinstance(text, str):
                        text = str(text)
                    return unicodedata.normalize("NFKD", text).encode("latin1", "ignore").decode("latin1")

                class PDF(FPDF):
                    def header(self):
                        self.set_font("Arial", "B", 14)
                        self.ln(5)

                    def chapter_body(self, entry, selected_fields):
                        self.set_font("Arial", "", 11)
                        for field in selected_fields:
                            label = clean_text(field.replace("_", " ").title())
                            value = clean_text(entry.get(field, ""))
                            self.multi_cell(0, 8, f"{label}: {value}")
                            self.ln(1)
                        self.ln(3)
                        self.cell(0, 0, "-" * 80)
                        self.ln(5)

                def generate_pdf(data, fields, filename):
                    pdf = PDF()
                    pdf.add_page()
                    for item in data:
                        pdf.chapter_body(item, fields)
                    pdf.output(filename)
                    return filename

                detailed_pdf = generate_pdf(
                    results["full_analysis"],
                    ["page", "citation", "heading", "summary", "polarity"],
                    "legal_argument_analysis_ranked.pdf"
                )

                minimal_pdf = generate_pdf(
                    argument_minimal,
                    ["page", "citation", "heading"],
                    "legal_argument_minimal.pdf"
                )

                # === ZIP Creation ===
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    zip_file.write("legal_argument_analysis_ranked.json")
                    zip_file.write("top_10.json")
                    zip_file.write("argument_minimal.json")
                    zip_file.write("legal_argument_analysis_ranked.pdf")
                    zip_file.write("legal_argument_minimal.pdf")
                zip_buffer.seek(0)

                st.success("✅ Analysis complete!")

                # === Display Top Arguments ===
                st.markdown('<div class="section-header">Top Arguments</div>', unsafe_allow_html=True)
                for i, arg in enumerate(results["top_arguments"], 1):
                    with st.expander(f"Argument #{i} (Score: {arg['final_score']:.1f}) - {arg['heading']}"):
                        st.markdown(f"**Page:** {arg['page']}")
                        st.markdown(f"**Citation:** {arg['citation']}")
                        st.markdown(f"**Polarity:** {arg['polarity']}")
                        st.markdown("**Summary:**")
                        st.write(arg["summary"])
                        st.markdown("**Full Text:**")
                        st.write(arg["text"])

                # === Download Section ===
                st.markdown('<div class="section-header">⬇Download Bundle</div>', unsafe_allow_html=True)
                st.download_button(
                    label="Download All Results as ZIP",
                    data=zip_buffer,
                    file_name="legal_argument_bundle.zip",
                    mime="application/zip"
                )

            except Exception as e:
                st.error(f" An error occurred: {str(e)}")
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
