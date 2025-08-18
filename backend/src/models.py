# app/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# --- Models for Ingesting Your Recommendation Data ---

class Metadata(BaseModel):
    input_documents: List[str]
    persona: str
    job_to_be_done: str

# class ExtractedSection(BaseModel):
#     document: str
#     section_title: str
#     importance_rank: int
#     page_number: int

# class SubsectionAnalysis(BaseModel):
#     document: str
#     refined_text: str
#     page_number: int

class AnalyzedSection(BaseModel):
    document: str
    page_number: int
    section_title: str
    refined_text: str
    importance_rank: int
    relevance_score: float

class RecommendationData(BaseModel):
    """The main model for the JSON data you will POST."""
    metadata: Metadata
    analyzed_sections: List[AnalyzedSection]
    # subsection_analysis: List[SubsectionAnalysis]


class InsightDetail(BaseModel):
    key_insights: List[str] = Field(..., description="The most important takeaways or connections.")
    did_you_know: str = Field(..., description="A surprising or little-known fact.")
    contradictions: List[str] = Field(..., description="Potential contradictions or counterpoints.")

class InsightsResponse(BaseModel):
    insights: InsightDetail

class ProcessingResult(BaseModel):

    relevant_sections: List[AnalyzedSection] = Field(..., description="The most important sections identified by the ML model.")
    insights: InsightDetail = Field(..., description="LLM-generated insights based on the content.")
    # podcast_url: str = Field(..., description="The URL to the generated audio podcast.")

# class Recommendation(BaseModel):
#     """Updated response model to include richer context."""
#     source_chunk_id: int
#     document: str
#     page_number: int
#     content: str
#     relevance_score: float

# class RecommendationsResponse(BaseModel):
#     recommendations: List[Recommendation]