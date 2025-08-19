import uuid
from fastapi import APIRouter, Form, HTTPException, UploadFile, File, Body

from typing import List, Optional
from .. import models
from ..services import ml_pipeline_service, llm_service, tts_service
from ..state import session_stores
from ..config import UPLOAD_DIR
from ..services.vector_store import VectorStore
import os
import datetime


router = APIRouter(prefix="/collection", tags=["Collection Processing"])

@router.get("/session/new", summary="Start a new session/collection")
def create_new_session():
    """Generates a new unique session ID."""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

@router.get("/files/{session_id}", summary="Get list of files for a session")
async def get_session_files(session_id: str):
    """
    Returns a list of filenames for a given session ID.
    """
    session_upload_dir = UPLOAD_DIR / session_id
    if not session_upload_dir.is_dir():
        # It's not an error if the directory doesn't exist yet, just means no files.
        return {"uploaded_files": []}
    
    files = [f.name for f in session_upload_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
    return {"uploaded_files": files}


@router.post("/upload", summary="Upload a PDF to a session")
async def upload_pdf_to_session(session_id: str = Form(...), files: List[UploadFile] = File(...)):
    """Saves a PDF to the session's directory."""
    session_upload_dir = UPLOAD_DIR / session_id
    session_upload_dir.mkdir(exist_ok=True)
    
    for file in files:
        if file.content_type != "application/pdf":
            print(f"Skipping non-PDF file: {file.filename}")
            continue

        file_path = session_upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
    uploaded_files = [f.name for f in session_upload_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
    return {"message": "File uploaded successfully.", "uploaded_files": uploaded_files}

@router.post("/delete-file", summary="Delete a specific file from a session")
async def delete_file_from_session(
    session_id: str = Form(...),
    filename: str = Form(...)
):
    """
    Finds and deletes a specific file from a session's upload directory.
    """
    session_upload_dir = UPLOAD_DIR / session_id
    file_path = session_upload_dir / filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in session '{session_id}'."
        )

    try:
        os.remove(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {e}"
        )

    # Return the updated list of remaining files
    remaining_files = [f.name for f in session_upload_dir.iterdir() if f.is_file()]
    return {
        "message": f"Successfully deleted '{filename}'.",
        "uploaded_files": remaining_files
    }

@router.post("/process", response_model=models.ProcessingResult, summary="Process the entire collection")
async def process_collection(
    session_id: str = Form(...),
    persona: Optional[str] = Form(None),
    job_to_be_done: Optional[str] = Form(None),
    selected_text: Optional[str]= Form(None)
):
    
    query = ""
    if selected_text:
        if persona or job_to_be_done:
            raise HTTPException(
                status_code=400, 
                detail="Cannot provide both 'selected_text' and 'persona'/'job_to_be_done'."
            )
        query = selected_text
    elif persona and job_to_be_done:
        query = f"""
        Given the user persona of a '{persona}', whose primary goal is to '{job_to_be_done}', 
        find all text sections that directly address this goal. The ideal section would contain 
        actionable insights, data, or key arguments related to the task.
        """
    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either 'selected_text' or both 'persona' and 'job_to_be_done'."
        )

    # --- 1. Run ML Analysis ---
    if session_id not in session_stores:
        session_stores[session_id] = VectorStore()

    session_upload_dir = UPLOAD_DIR / session_id
    pdf_paths = [f for f in session_upload_dir.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
    if not pdf_paths:
        raise HTTPException(status_code=400, detail="No PDFs in this collection to process.")

    ml_output = ml_pipeline_service.run_analysis_pipeline(pdf_paths, query)
    
    # --- 2. Index subsections for future recommendations ---
    store = session_stores[session_id]
    store.add_documents(ml_output.analyzed_sections)
    
    # --- 3. Generate LLM Insights ---
    # We'll use the top 3 most important sections as context for the LLM
    # top_sections = sorted(ml_output.subsection_analysis, key=lambda x: x.importance_rank)[:5]

    # top_sections= ml_output.subsection_analysis[:5]
    top_sections = sorted(ml_output.analyzed_sections, key=lambda x: x.importance_rank)[:5]

    print("DEBUG: Bypassing LLM and TTS services for this test.")
    context_text = [section.refined_text for section in top_sections] # Using title as context for brevity
    
    insights = llm_service.generate_insights_with_gemini("Overall document summary", context_text)

    # --- 4. Generate Podcast Audio ---
    # insights_summary_for_podcast = ". ".join(insights.key_insights)
    # podcast_url = tts_service.generate_audio_podcast(insights_summary_for_podcast, session_upload_dir)

    # # --- 5. Assemble and Return the Final Response ---
    return models.ProcessingResult(
        relevant_sections=top_sections,
        insights=insights
    )


@router.post("/test-insights", response_model=models.InsightDetail, summary="🧪 Test Gemini Insights Directly")
async def test_insights(
    current_text: str = Body(..., embed=True, description="The main text to analyze."),
    related_texts: List[str] = Body(..., embed=True, description="A list of related text snippets.")
):
    """
    A dedicated endpoint to test the llm_service.generate_insights_with_gemini
    function in isolation. This bypasses all PDF processing.
    """
    print("DEBUG: Directly testing insights generation...")
    try:
        # Call the llm_service directly with the provided text
        insights = llm_service.generate_insights_with_gemini(
            current_text=current_text,
            recommended_texts=related_texts
        )
        return insights
    except Exception as e:
        # This will immediately show you any errors from the Gemini API call
        # (like an invalid API key).
        raise HTTPException(status_code=500, detail=f"Error in LLM service: {str(e)}")
    

@router.post("/generate-script", summary="Generate and save a podcast script")
async def generate_script(
    session_id: str = Form(...),
    query: str = Form(...),
    insights_json: str = Form(...),
    sections_json: str = Form(...)
):
    """
    Generates a podcast script from results and saves it to the session directory.
    """
    import json
    session_upload_dir = UPLOAD_DIR / session_id
    if not session_upload_dir.is_dir():
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        insights = json.loads(insights_json)
        sections = json.loads(sections_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format.")

    script = llm_service.generate_podcast_script(query, insights, sections)
    
    # Save the script to a file
    script_path = session_upload_dir / "podcast_script.txt"
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script)

    return {"message": "Script generated successfully."}


@router.get("/get-audio/{session_id}", summary="Generate or retrieve the podcast audio")
async def get_audio(session_id: str):
    """
    Checks for existing audio, generates it if needed, and returns the URL.
    """
    print("absnkd")
    session_upload_dir = UPLOAD_DIR / session_id
    script_path = session_upload_dir / "podcast_script.txt"
    audio_path = session_upload_dir / "podcast.mp3"
    audio_url = f"/uploads/{session_id}/podcast.mp3"

    if not script_path.exists():
        raise HTTPException(status_code=404, detail="Podcast script not found. Please generate results first.")

    # Generate the audio file from the script
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()
    
    tts_service.script_to_audio(script_text, audio_path)
    
    print(audio_url)

    return {"podcast_url": audio_url}