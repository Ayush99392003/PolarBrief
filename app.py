import streamlit as st
from logic import (
    extract_pdf_lines,
    chunk_lines_into_paragraphs,
    parse_argument_results,
    create_pdf_from_dict,
    create_pdf_from_top10,
    create_zip_archive
)
import json
import os

if "lines" not in st.session_state:
    st.session_state.lines = None
if "paragraphs" not in st.session_state:
    st.session_state.paragraphs = None
if "parsed_results" not in st.session_state:
    st.session_state.parsed_results = None
if "top_10" not in st.session_state:
    st.session_state.top_10 = None

BACKGROUND_IMAGE_URL = "https://images.pexels.com/photos/159832/justice-law-case-hearing-159832.jpeg"

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

st.set_page_config(page_title="PolarBrief", layout="wide")

st.markdown('<div class="title-box"><h1>PolarBrief : AI Driven Pro/Con Argument Miner</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="main-box"> <h2>Upload a legal brief PDF and analyze it line by line, paragraph by paragraph using LLMs.</h2></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📄 Upload PDF", type="pdf")

if uploaded_file:
    st.markdown('<div class="section-header">📑 Extracting Lines from PDF</div>', unsafe_allow_html=True)
    with st.spinner("Extracting lines..."):
        st.session_state.lines = extract_pdf_lines(uploaded_file)
        st.success(f"✅ Extracted {len(st.session_state.lines)} lines.")

    st.markdown('<div class="section-header">🧾 Chunking Lines into Paragraphs</div>', unsafe_allow_html=True)
    with st.spinner("Chunking..."):
        st.session_state.paragraphs = chunk_lines_into_paragraphs(st.session_state.lines)
        st.success(f"✅ Chunked into {len(st.session_state.paragraphs)} paragraphs.")

    st.markdown('<div class="section-header">⚖️ Argument Analysis</div>', unsafe_allow_html=True)
    with st.spinner("Analyzing with LLM..."):
        st.session_state.parsed_results = parse_argument_results(st.session_state.paragraphs)

        pro_args = sorted(
            [p for p in st.session_state.parsed_results if p["polarity"].lower() == "pro"],
            key=lambda x: x["score"],
            reverse=True
        )[:5]
        con_args = sorted(
            [p for p in st.session_state.parsed_results if p["polarity"].lower() == "con"],
            key=lambda x: x["score"],
            reverse=True
        )[:5]
        st.session_state.top_10 = {"top_5_pro": pro_args, "top_5_con": con_args}

if st.session_state.top_10:
    st.markdown('<div class="section-header">🟢 Top 5 Pro Arguments</div>', unsafe_allow_html=True)
    for i, arg in enumerate(st.session_state.top_10["top_5_pro"], 1):
        st.markdown(f"**{i}.** *Score: {arg['score']} | Page: {arg['page']}*")
        st.info(arg["summary"])

    st.markdown('<div class="section-header">🔴 Top 5 Con Arguments</div>', unsafe_allow_html=True)
    for i, arg in enumerate(st.session_state.top_10["top_5_con"], 1):
        st.markdown(f"**{i}.** *Score: {arg['score']} | Page: {arg['page']}*")
        st.error(arg["summary"])

    st.markdown('<div class="section-header">📥 Download All Results</div>', unsafe_allow_html=True)

    files_to_zip = {
        "lines.json": json.dumps(st.session_state.lines, indent=2, ensure_ascii=False),
        "lines.pdf": create_pdf_from_dict(st.session_state.lines, "Line-by-Line Text").getvalue(),
        "paragraphs.json": json.dumps(st.session_state.paragraphs, indent=2, ensure_ascii=False),
        "paragraphs.pdf": create_pdf_from_dict(st.session_state.paragraphs, "Paragraph-by-Paragraph Text").getvalue(),
        "arguments.json": json.dumps(st.session_state.parsed_results, indent=2, ensure_ascii=False),
        "arguments.pdf": create_pdf_from_dict(st.session_state.parsed_results, "All Legal Arguments").getvalue(),
        "top_10.json": json.dumps(st.session_state.top_10, indent=2, ensure_ascii=False),
        "top_10.pdf": create_pdf_from_top10(st.session_state.top_10).getvalue(),
    }

    zip_data = create_zip_archive(files_to_zip)

    st.download_button(
        "📦 Download All as ZIP",
        data=zip_data,
        file_name="polarbrief_outputs.zip",
        mime="application/zip"
    )
    if st.button("🔁 Reset App"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)
