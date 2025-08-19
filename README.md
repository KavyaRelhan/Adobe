# Connecting the Dots through Docs 🧠📄

A powerful AI-driven web application that allows users to upload multiple PDF files, extract the most relevant sections from those documents using Gemini AI, and generate meaningful insights and even a 3–4 minute conversational podcast script between two speakers (male & female voice).

---

## 🚀 Features

- ✅ Upload multiple PDFs at once
- 2 ways to analyze content:
  - 📌 **Type-based:** Enter a persona and job description to generate relevant sections, insights and podcast content.
  - ✍️ **Selection-based:** Directly select any text from the PDF and get insights & podcast script for that specific selection.
- 📚 View extracted relevant sections from all uploaded PDFs
- 🧐 Click on snippets to open and read the original PDF section
- 💡 Generate AI-powered insights and 'Did You Know' facts using Gemini API
- 🎙️ Auto-generate a 3–4 minute conversational podcast script with male & female roles
- ♻️ Add more files to your collection anytime and re-analyze content

---

## 🛠️ Setup and Installation

### Clone the Repository

```bash
git clone https://github.com/KavyaRelhan/Adobe.git
cd Adobe
```
### Backend Setup (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate           # (or source venv/bin/activate on Linux/Mac)
pip install -r requirements.txt
```
Create a .env file inside the backend folder:
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_KEY

TTS_PROVIDER=google
TTS_API=YOUR_TTS_KEY
MOCK_TTS=false

###  Run Backend
```bash
uvicorn src.main:app --reload
```

### Frontend Setup (React)
```bash
cd frontend
npm install
npm run dev
```

---

## 👥 Contributors


- Kavya
- Tarushi



### 🏆 Hackathon Context

This project was built as part of the **Adobe India Hackathon 2025 – Grand Finale, Connecting the Dots Challenge** under the theme:

> _From Brains to Experience – Make It Real_

---

## ✅ Usage Flow

1. Upload PDFs using drag & drop or click-to-upload

2. Once analysis completes, explore relevant sections and insights

3. View AI-generated facts and podcast script

4. Optionally upload more PDFs or delete existing ones

5. Generate again for updated insights

---

## ✅ Future Improvements (Optional Add-on section)

- Save project sessions for future review

- User authentication & history of uploaded content
