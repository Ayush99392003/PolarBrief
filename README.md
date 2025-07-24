# ⚖️ PolarBrief: AI Driven Pro/Con Argument Miner

PolarBrief is a Streamlit-based web app that allows you to upload a legal PDF brief, extract its contents, analyze each paragraph using LLMs, and identify and rank **Pro** and **Con** legal arguments. The results are downloadable in both JSON and PDF formats.

---

## 🚀 How to Run It Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Ayush99392003/PolarBrief.git
cd polarbrief
```

### 2. Create and Activate a Virtual Environment (optional but recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Change api key



Add your own api key:

```
GROQ_API_KEY=your_groq_api_key_here
```



### 5. Start the Streamlit App

```bash
streamlit run app.py
```

---

## 📦 Project Structure

```bash
├── app.py                 # Streamlit frontend
├── logic.py               # Core logic and PDF/LLM handling
├── requirements.txt       # Required Python packages
├── .gitattributes         # GitHub/LFS file handling
└── README.md              # You're reading it :)
```

---

## 🧠 Features

- 📄 Upload a PDF legal brief.
- 📜 Extract lines and form paragraphs.
- 🧠 Analyze arguments using Groq-hosted LLaMA 3 model.
- ⚖️ Automatically classify arguments as Pro or Con.
- 🏆 Score arguments based on relevance and clarity.
- 📥 Download all results in JSON and PDF format, including a ZIP bundle.

---


## 📄 License

MIT License © 2025

---

## 👤 Author

**Ayush Agarwal** – [@ayushagrwl]([https://github.com/ayushagrwl](https://github.com/Ayush99392003)
