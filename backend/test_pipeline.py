import sys
import os
from pathlib import Path
from pprint import pprint

# This adds your project's 'src' directory to the Python path,
# allowing this script to import your modules correctly.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now we can import the function we want to test
from src.services.ml_pipeline_service import run_analysis_pipeline

def main():
    """A simple script to test the ML pipeline service."""
    print("--- Starting ML Pipeline Test ---")

    # --- CONFIGURE YOUR TEST HERE ---

    # 1. Point this to a folder with the PDFs you want to test.
    #    For example, create a folder 'uploads/my_test_collection'
    #    and place your PDFs inside it.
    pdf_folder = Path("uploads/03c63bcd-4df4-4e0e-9281-d01fb16a907e")
    
    # 2. Define the query you want to test.
    test_query = "Nice, located on the French Riviera, has been a popular destination for centuries. Its history dates back to the ancient Greeks, who founded the city around 350 BC. Nice later became a  Roman colony and has since evolved into a glamorous resort town. In the 19th century, Nice  became a favorite winter retreat for European aristocrats, which contributed to its development as a luxurious destination."
    
    # --- END CONFIGURATION ---

    if not pdf_folder.exists():
        print(f"Error: Test folder '{pdf_folder}' not found. Please create it and add PDFs.")
        return

    test_pdf_paths = list(pdf_folder.glob("*.pdf"))
    if not test_pdf_paths:
        print(f"Error: No PDF files found in '{pdf_folder}'.")
        return
        
    print(f"Analyzing {len(test_pdf_paths)} PDF(s) with query: '{test_query}'")

    try:
        # Call your pipeline function directly
        result = run_analysis_pipeline(
            pdf_paths=test_pdf_paths,
            query=test_query
        )

        print("\n--- ✅ Pipeline Execution Successful ---")
        print("--- Result: ---")
        # Use pprint to print the output in a readable format
        pprint(result.model_dump())

    except Exception as e:
        print(f"\n--- ❌ Pipeline Failed ---")
        print(f"Error: {e}")
        
if __name__ == "__main__":
    main()