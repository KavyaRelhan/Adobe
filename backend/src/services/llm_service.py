# app/services/llm_service.py
import google.generativeai as genai
import json
from fastapi import HTTPException
from ..config import settings
from ..models import InsightDetail

# --- Configure the Gemini Client ---
# This should only run if Gemini is the selected provider

if settings.LLM_PROVIDER == 'gemini':
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the environment.")
    genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_insights_with_gemini(current_text: str, recommended_texts: list[str]) -> InsightDetail:
    """
    Uses the Gemini API to generate structured insights from text.
    """
    if settings.LLM_PROVIDER != 'gemini':
        raise HTTPException(status_code=501, detail="This endpoint is configured for Gemini only.")

    model = genai.GenerativeModel(settings.GEMINI_MODEL)

    # --- The Prompt is Key ---
    # We instruct the model to return a valid JSON object.
    prompt = f"""
    You are a world-class research assistant. Your task is to analyze a primary text section and several related text sections to extract deep insights.

    Analyze the following texts:

    **Primary Text:**
    ```
    {current_text}
    ```

    **Related Texts:**
    1. ```{recommended_texts[0] if len(recommended_texts) > 0 else "N/A"}```
    2. ```{recommended_texts[1] if len(recommended_texts) > 1 else "N/A"}```
    3. ```{recommended_texts[2] if len(recommended_texts) > 2 else "N/A"}```

    Based on all the provided text, generate a JSON object with the following structure:
    {{
        "key_insights": ["Insight 1", "Insight 2", ...],
        "did_you_know": "A single, surprising fact or piece of trivia related to the texts which user might not know.",
        "contradictions": ["Identify a point of conflict or contradiction between the texts, if any.", ...]
    }}

    key_insights should include some information different from the related text provided to you, something interesting related to it but should not match exactly with what is written in the text sent to you, unknown facts which user might find useful and add extra information to its knowledge.

    Provide only the raw JSON object as your response.
    """

    try:
        # Use JSON mode for reliable, structured output
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse the JSON response from the model
        insights_data = json.loads(response.text)
        
        # Validate the data with our Pydantic model
        return InsightDetail(**insights_data)

    except Exception as e:
        # Handle potential API errors, parsing errors, or validation errors
        raise HTTPException(status_code=500, detail=f"Failed to generate insights from Gemini: {e}")

def generate_podcast_script(query: str, insights: dict, sections: list) -> str:
    """
    Uses the Gemini API to generate a two-person podcast script from raw data.
    """
    if settings.LLM_PROVIDER != 'gemini':
        raise HTTPException(status_code=501, detail="This feature is configured for Gemini only.")

    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- Create a rich context from the input data ---
    insights_summary = ". ".join(insights.get('key_insights', []))
    sections_summary = ". ".join([s.get('refined_text', '') for s in sections[:2]]) # Use top 2 sections

    context = f"""
    **Original User Query:** "{query}"
    **Key AI-Generated Insights:** "{insights_summary}"
    **Excerpts from Top Relevant Sections:** "{sections_summary}"
    """

    # --- The Prompt for Script Generation ---
    prompt = f"""
    You are a creative podcast scriptwriter. Your task is to create a long 2 to 5 minutes, engaging, and natural-sounding podcast conversation between two hosts, "Alex" and "Ben".

    The conversation must be based *only* on the following context. You can add some extra information also, but it should be completely correlated with the context.
    The goal is to make the disconnected facts from the context sound like a fluid and insightful discussion. But don't mention anything like aI mentions, it's written ,you've given etc phrases.

    **Context:**
    {context}

    **Instructions:**
    1.  Create a script that is approximately 2-5 minutes long when spoken.
    2.  The tone should be curious and informative.
    3.  The hosts, Alex and Ben, should build on each other's points.
    4.  The output MUST be only the script, formatted exactly as follows.Initially they may address each other by their names and sometimes in middle of conversation also as it suits.

    **Example Format:**
    Alex: Welcome back to "Insightful Reads"! Today, we're diving into some fascinating documents.
    Ben: Absolutely, Alex. The AI analysis pulled out some really interesting points based on the user's query.
    Alex: It certainly did. For instance, it highlighted that...
    Ben: And that connects directly to another section, which mentioned...

    Now, generate the podcast script based on the provided context.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate podcast script from Gemini: {e}")
