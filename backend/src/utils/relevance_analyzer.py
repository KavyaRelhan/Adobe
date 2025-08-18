# src/relevance_analyzer.py

import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple

# We no longer need the summarizer for this retrieval task
# from transformers import T5ForConditionalGeneration, T5Tokenizer

from ..models import AnalyzedSection
from ..config import settings, RELEVANCE_THRESHOLD, MAX_RESULTS

class RelevanceAnalyzer:
    def __init__(self):
        """Initializes models. Note: Summarizer is removed for this logic."""
        print("Initializing RelevanceAnalyzer... Loading embedding model...")
        self.device = "cpu"
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device=self.device)
        print("RelevanceAnalyzer is ready.")

    def analyze(self, structured_doc: List[Dict], query: str) -> Tuple[List[Dict], List[Dict]]:
        """
        New logic: Finds all relevant paragraphs above a threshold, maps them to their
        heading and source document, and returns them without summarization.
        """
        # query = f"""
        # Given the user persona of a '{persona}', whose primary goal is to '{job_to_be_done}', 
        # find all text sections that directly address this goal. The ideal section would contain 
        # actionable insights, data, or key arguments related to the task.
        # """

        # 1. Filter for paragraphs and add their original document source
        paragraphs = []
        last_heading_text = "General Information"
        for i, item in enumerate(structured_doc):
            if item['type'] == 'paragraph':
                # Important: Carry the original index and document source forward
                item['original_index'] = i
                paragraphs.append(item)
            elif item['type'] == 'heading':
                last_heading_text = item['text']

        if not paragraphs:
            return [], []

        # 2. Calculate relevance for all paragraphs
        para_texts = [p['text'] for p in paragraphs]
        query_embedding = self.embedding_model.encode([query])
        para_embeddings = self.embedding_model.encode(para_texts)
        similarities = cosine_similarity(query_embedding, para_embeddings)[0]

        # 3. Filter for all paragraphs that meet the relevance threshold
        relevant_paragraphs = []
        for i, p in enumerate(paragraphs):
            score = similarities[i]
            if score >= RELEVANCE_THRESHOLD:
                p['relevance_score'] = score
                relevant_paragraphs.append(p)

        # 4. Sort the relevant paragraphs by score and limit the results
        sorted_paragraphs = sorted(relevant_paragraphs, key=lambda x: x['relevance_score'], reverse=True)[:MAX_RESULTS]

        # 5. Format the final output for each relevant paragraph
        # output_sections, output_analysis = [], []

        final_analyzed_sections = []

        for rank, para in enumerate(sorted_paragraphs, start=1):
            # Find the parent heading for the current paragraph
            # parent_heading_text = "General Information" # Default heading
            # for i in range(para['original_index'] - 1, -1, -1):
            #     if structured_doc[i]['type'] == 'heading':
            #         parent_heading_text = structured_doc[i]['text']
            #         break
            
            # The 'document' key is already in the block from the parser!
            doc_name = para.get('document', 'Unknown Document')
            page_num = para.get('page', 0)
            # parent_heading_text = para.get('parent_heading', "General Information")

            # Create the entry for "extracted_sections"
            # output_sections.append({
            #     "document": doc_name,
            #     "section_title": parent_heading_text,
            #     "importance_rank": rank,
            #     "page_number": page_num
            # })

            # # Create the corresponding entry for "subsection_analysis"
            # # The "refined_text" is now the actual paragraph text.
            # output_analysis.append({
            #     "document": doc_name,
            #     "refined_text": para['text'],
            #     "page_number": page_num
            # })

            final_analyzed_sections.append(
                AnalyzedSection(
                    document=doc_name,
                    page_number=page_num,
                    section_title=last_heading_text,
                    refined_text=para['text'],
                    importance_rank=rank,
                    relevance_score=para['relevance_score']
                )
            )

        return final_analyzed_sections

relevance_analyzer = RelevanceAnalyzer()