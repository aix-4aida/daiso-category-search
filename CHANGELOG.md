# Changelog

All notable changes to this project will be documented in this file.

## [0.3.1] - 2026-01-19

### Added (RAG Robustness PoC)
- **Integration**: Merged RAG Optimization PoC from `search-roca` into main repo.
- **Scripts** (`poc/`):
    - `RAG_System_experiment_keyword.py`: Verified K=30/Keyword Optimization script.
    - `RAG_System_experiment_baseline.py`: Sentence-input baseline script.
    - `generate_large_data.py`: 200-product scaling data generator.
- **Reports** (`docs/`):
    - `RAG_ROBUSTNESS.md`: Final optimization report (K=30 Success).
    - `RAG_BASELINE.md`: Baseline failure analysis.
- **Prompts**: `poc/prompts/intent_rules_prompt.txt` (Rule-based Intent Classification).

---

## [0.3.0] - 2026-01-16

### Added (LangGraph Migration)
- **Logic**: Migrated backend logic to `LangGraph` (Cyclic State Machine)
- **Agent**: Implemented 5-node workflow (`NLU`, `Search`, `AmbiguityCheck`, `Clarification`, `Response`)
- **Context**: Full conversation history persistence using `MemorySaver`
- **Frontend**: Added `/kioskmode` route and Landing Page UI
- **Dependencies**: `langgraph`, `langchain`, `langchain-google-genai`

### Improved
- **Clarification**: Added "Drill-Down" logic to clarify broad categories (e.g., Cleaning -> Detergent vs Tools)
- **Loop Prevention**: Fixed infinite loop bug where AI kept asking same questions
- **Language**: Strictly enforced Korean output in system prompts

## [0.2.0] - 2026-01-16

### Added
- **Category System**: Product categorization with major/middle categories (대분류/중분류)
- `category_matcher.py`: Keyword-based category matching script
- `categories` table: 48 category entries (12 major × multiple middle)
- Products table now has `category_major` and `category_middle` columns

### Stats
- 401 products matched (67%)
- 200 products unmatched (to be fixed with full re-crawl)

## [0.1.1] - 2026-01-16

### Fixed
- Updated `requirements.txt` with exact package versions from search-roca conda environment
- Added missing dependencies: `sentence-transformers`, `huggingface-hub`, `tokenizers`, `safetensors`, `scipy`, `scikit-learn`

## [0.1.0] - 2026-01-16

### Added
- **Product Database** (`backend/database/`)
  - `products.db`: SQLite database with 601 crawled products
  - `images/`: 601 product images from Daiso Mall ranking
  - `database.py`: Database operations module
  - `embeddings.py`: CLIP-based multimodal embeddings (text + image)
  - `generate_test_data.py`: 3000 test utterances generator (85% normal, 15% hard)

### Database Schema
- `products`: id, rank, name, price, image_url, image_name, image_path
- `test_utterances`: utterance, difficulty, expected_product_id
- `product_embeddings`: text_embedding, image_embedding (CLIP 512-dim vectors)

### Dependencies Added
- `selenium`, `webdriver-manager`: Web crawling
- `transformers`, `torch`: CLIP embeddings
- `Pillow`: Image processing

---

## [0.0.0] - Initial

- Initial project setup
- Basic FastAPI backend structure
- Frontend placeholder
