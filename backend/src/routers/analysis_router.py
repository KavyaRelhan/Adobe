import json
import os
import uuid

from pathlib import Path
from typing import List, Optional

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    UploadFile,
    File,
    Body
)

from .. import models
from ..services import llm_service, tts_service
from ..services import ml_pipeline_service
from ..state import get_vector_store
from ..config import UPLOAD_DIR, MAX_RESULTS
from ..models import AnalyzedSection


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

@router.post(
    "/upload",
    summary="Upload and index PDFs"
)
async def upload_pdf_to_session(
    session_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Upload PDFs, extract their paragraphs, generate embeddings,
    and add the embeddings to the session's FAISS index.

    All indexing happens here, during upload.
    """

    session_upload_dir = UPLOAD_DIR / session_id
    session_upload_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    store = get_vector_store(session_id)

    indexed_files = []
    errors = []

    for file in files:

        if not file.filename:
            errors.append("A file has no filename.")
            continue

        # Validate the extension rather than relying only
        # on the client-supplied MIME type.
        safe_filename = Path(file.filename).name

        if Path(safe_filename).suffix.lower() != ".pdf":
            errors.append(
                f"{safe_filename}: only PDF files are supported."
            )
            continue

        file_path = session_upload_dir / safe_filename

        try:
            # Read and save the uploaded file.
            content = await file.read()

            if not content:
                raise ValueError("The uploaded file is empty.")

            with open(file_path, "wb") as output_file:
                output_file.write(content)

            # If this filename already has an index entry,
            # remove the old vectors before re-indexing it.
            #
            # This is necessary when a user replaces an
            # existing PDF with a new version.
            store.remove_document(safe_filename)

            # Process ONLY the newly uploaded PDF.
            processed = ml_pipeline_service.process_documents(
                [file_path]
            )

            paragraphs = processed.get(
                safe_filename,
                []
            )

            # Convert paragraph records into the existing
            # Pydantic model used by the vector store.
            sections = [
                AnalyzedSection(
                    document=item["document"],
                    page_number=item["page_number"],
                    section_title=item["section_title"],
                    refined_text=item["refined_text"],
                    importance_rank=0,
                    relevance_score=0.0
                )
                for item in paragraphs
            ]

            # Generate embeddings and add them to FAISS.
            indexed_count = store.add_documents(
                sections,
                source_file=safe_filename
            )

            indexed_files.append({
                "filename": safe_filename,
                "paragraphs_indexed": indexed_count
            })

        except Exception as error:

            # Do not leave an old index entry pointing to
            # a file that failed to be processed.
            store.remove_document(safe_filename)

            errors.append(
                f"{safe_filename}: {str(error)}"
            )

    uploaded_files = [
        path.name
        for path in session_upload_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".pdf"
    ]

    return {
        "message": (
            "Upload and indexing completed."
            if not errors
            else "Upload completed with some errors."
        ),
        "uploaded_files": uploaded_files,
        "indexed_files": indexed_files,
        "errors": errors,
        "total_vectors": store.index.ntotal
    }

@router.post(
    "/delete-file",
    summary="Delete a PDF and its indexed paragraphs"
)
async def delete_file_from_session(
    session_id: str = Form(...),
    filename: str = Form(...)
):
    """
    Remove a PDF from the collection and remove its vectors
    from the session's FAISS index.
    """

    safe_filename = Path(filename).name

    if safe_filename != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    session_upload_dir = UPLOAD_DIR / session_id
    file_path = session_upload_dir / safe_filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"File '{safe_filename}' was not found."
        )

    store = get_vector_store(session_id)

    try:
        # Remove the vectors and metadata first.
        store.remove_document(safe_filename)

        # Then remove the physical PDF.
        os.remove(file_path)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file: {error}"
        )

    remaining_files = [
        path.name
        for path in session_upload_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".pdf"
    ]

    return {
        "message": f"Deleted '{safe_filename}'.",
        "uploaded_files": remaining_files,
        "total_vectors": store.index.ntotal
    }

@router.post(
    "/process",
    response_model=models.ProcessingResult,
    summary="Retrieve relevant paragraphs and generate optional insights"
)
async def process_collection(
    session_id: str = Form(...),
    persona: Optional[str] = Form(None),
    job_to_be_done: Optional[str] = Form(None),
    selected_text: Optional[str] = Form(None)
):
    # --------------------------------------------------
    # 1. Construct the search query
    # --------------------------------------------------
    if selected_text and selected_text.strip():
        if persona or job_to_be_done:
            raise HTTPException(
                status_code=400,
                detail="Cannot provide both selected_text and persona/job_to_be_done."
            )

        query = selected_text.strip()

    elif (
        persona and persona.strip()
        and job_to_be_done and job_to_be_done.strip()
    ):
        query = (
            f"User persona: {persona.strip()}. "
            f"Goal: {job_to_be_done.strip()}. "
            "Find paragraphs that directly address this goal and contain "
            "relevant information, evidence, actionable insights, or arguments."
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either selected_text or both persona and job_to_be_done."
        )

    # --------------------------------------------------
    # 2. Retrieve paragraphs FIRST. This does not require Gemini.
    # --------------------------------------------------
    try:
        store = get_vector_store(session_id)

        if store.index.ntotal == 0:
            raise HTTPException(
                status_code=400,
                detail="No indexed paragraphs are available. Upload PDFs first."
            )

        search_results = store.search(
            query_text=query,
            k=MAX_RESULTS
        )

        relevant_sections = []

        for rank, (_, section, score) in enumerate(
            search_results, start=1
        ):
            section.importance_rank = rank
            section.relevance_score = float(score)
            relevant_sections.append(section)

        if not relevant_sections:
            raise HTTPException(
                status_code=404,
                detail="No relevant paragraphs were found for this query."
            )

    except HTTPException:
        raise

    except Exception as error:
        print(f"Paragraph retrieval failed: {error}")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve paragraphs. Please try again."
        )

    # --------------------------------------------------
    # 3. Prepare fallback insights.
    # These are returned if Gemini is unavailable.
    # --------------------------------------------------
    fallback_insights = models.InsightDetail(
        key_insights=[],
        did_you_know=(
            "Couldn't generate AI insights right now. "
            "Your relevant paragraphs are available below. Please try again later."
        ),
        contradictions=[]
    )

    insights = fallback_insights
    warnings = []

    # Use only the top paragraphs as context for Gemini.
    top_sections = relevant_sections[:5]
    context_text = [
        section.refined_text for section in top_sections
    ]

    # --------------------------------------------------
    # 4. Gemini is OPTIONAL. Its failure must not affect retrieval.
    # --------------------------------------------------
    try:
        insights = llm_service.generate_insights_with_gemini(
            current_text=query,
            recommended_texts=context_text
        )

    except Exception as error:
        print(f"Gemini insight generation failed: {error}")

        warnings.append(
            "Couldn't generate AI insights right now. "
            "Your relevant paragraphs are available. Please try again later."
        )

    # --------------------------------------------------
    # 5. Always return retrieved paragraphs.
    # --------------------------------------------------
    return models.ProcessingResult(
        relevant_sections=top_sections,
        insights=insights,
        warnings=warnings
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
    

@router.post("/generate-script", summary="Generate podcast script")
async def generate_script(
    session_id: str = Form(...),
    query: str = Form(...),
    insights_json: str = Form(...),
    sections_json: str = Form(...)
):
    import json

    session_upload_dir = UPLOAD_DIR / session_id

    if not session_upload_dir.is_dir():
        return {
            "script_generated": False,
            "message": "Session not found. Please try again."
        }

    try:
        insights = json.loads(insights_json)
        sections = json.loads(sections_json)

        script = llm_service.generate_podcast_script(
            query,
            insights,
            sections
        )

        if not script or not script.strip():
            raise ValueError("The generated script was empty.")

        script_path = session_upload_dir / "podcast_script.txt"

        with open(script_path, "w", encoding="utf-8") as file:
            file.write(script)

        return {
            "script_generated": True,
            "message": "Podcast script generated successfully."
        }

    except Exception as error:
        print(f"Podcast script generation failed: {error}")

        return {
            "script_generated": False,
            "message": (
                "Couldn't generate the podcast script right now. "
                "Your analysis results are still available. Please try again later."
            )
        }

@router.get("/get-audio/{session_id}")
async def get_audio(session_id: str):
    session_upload_dir = UPLOAD_DIR / session_id

    script_path = session_upload_dir / "podcast_script.txt"
    audio_path = session_upload_dir / "podcast.mp3"

    if not script_path.exists():
        return {
            "audio_generated": False,
            "podcast_url": None,
            "message": (
                "The podcast script isn't available. "
                "Please try generating it again later."
            )
        }

    try:
        with open(script_path, "r", encoding="utf-8") as file:
            script_text = file.read()

        if not script_text.strip():
            raise ValueError("The podcast script is empty.")

        tts_service.script_to_audio(
            script_text,
            audio_path
        )

        return {
            "audio_generated": True,
            "podcast_url": f"/uploads/{session_id}/podcast.mp3",
            "message": "Podcast audio generated successfully."
        }

    except Exception as error:
        print(f"TTS audio generation failed: {error}")

        return {
            "audio_generated": False,
            "podcast_url": None,
            "message": (
                "Couldn't generate audio right now. "
                "Your analysis results are still available. Please try again later."
            )
        }
