import asyncio
import sys
from pathlib import Path

# Fix relative imports
sys.path.append(str(Path(__file__).parent))

from backend.services_kms.run_all_pipeline import run_pipeline_for_voice
from backend.database.database import get_product_by_id

async def main():
    print("Running verification pipeline...")
    
    # Use real audio path if checking specific case
    audio = "c:/kms/daiso-category-search/data/test_audio/01_general/김민서_일반01.m4a"
    # Or just dummy path if file access is issue (the pipeline might fail STT but run search if text provided)
    
    try:
        res = await run_pipeline_for_voice(audio, "마스크팩 있어?", 0.5)
        
        final = res.get("final_results", [])
        if not final:
            print("Pipeline returned no final_results.")
            return

        first = final[0]
        # Check both keys
        ids = first.get("retrieved_ids", first.get("retrieved_results", []))
        print(f"Retrieved IDs from pipeline: {ids}")
        
        found_any = False
        for item in ids:
            doc_id = item.split("(")[0].strip() if "(" in item else item.strip()
            try:
                p = get_product_by_id(int(doc_id))
                exists = p is not None
                print(f"ID {doc_id} -> Found in DB: {exists}")
                if exists:
                    found_any = True
            except Exception as e:
                print(f"ID {doc_id} -> Error checking DB: {e}")
        
        if found_any:
            print("Unknown Issue: IDs exist in DB. Likely main.py logic error or Frontend issue.")
        else:
            print("Root Cause: IDs retrieved by pipeline DO NOT exist in DB. Re-indexing required.")
            
    except Exception as e:
        print(f"Verification crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
