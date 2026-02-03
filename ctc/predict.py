import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import openai
import pandas as pd
from openai import APIConnectionError, APIError, RateLimitError

# ===================== CONFIGURATION (Centralized for Easy Modification) =====================
# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

Path("./temp").mkdir(parents=True, exist_ok=True)
Path("./prediction").mkdir(parents=True, exist_ok=True)
Path("./assembled").mkdir(parents=True, exist_ok=True)
Path("./history").mkdir(parents=True, exist_ok=True)

# File path config
INPUT_CSV_PATH = Path("./Chinese_Thermal_Comfort_Dataset/ctc/ctc_questions.csv")
TEMP_OUTPUT_DIR = Path("./temp")
# Root prediction directory (final CSV saved here)
PREDICTION_ROOT_DIR = Path("./prediction")

# Encoding config
CSV_ENCODING = "gbk"

# Batch save setting: save checkpoint every N rows
BATCH_SAVE_INTERVAL = 10

# LLM model & API config
VLLM_MODEL_LIST = [
    "mistral-small3.2",
    "gemma3:27b",
    "qwen3:32b",
    "deepseek-r1:32b",
    "gpt-oss:120b",
    "Qwen3-Next-80B-A3B-Thinking",
]
SELECTED_VLLM_MODEL = VLLM_MODEL_LIST[0]  # Use mistral-small3.2

HOST_LIST = [
    "http://localhost:11434/v1",
    "http://192.168.3.12:11434/v1",
]
SELECTED_API_HOST = HOST_LIST[1]  # Use 192.168.3.12 host
API_KEY = "ollama"  # Required by OpenAI client, unused for local/vLLM

# LLM request hyperparameters
MAX_TOKENS = 10240
TEMPERATURE = 0.4
MAX_RETRY_ATTEMPTS = 5  # Max retries for API calls/JSON parsing failures
SEED = 0  # Reproducibility

# PMV prompt templates
SYSTEM_INSTRUCTION = """Keep the answers clean and neat."""
PMV_EVAL_PROMPT = """
Evaluate the thermal sensation using the Predicted Mean Vote (PMV) scale. 
Fill in missing information based on your reasonable assumptions if needed.
PMV scale rules:
- PMV < -2.5: cold
- -2.5 ≤ PMV < -1.5: cool
- -1.5 ≤ PMV < -0.5: slightly cool
- -0.5 ≤ PMV < 0.5: neutral
- 0.5 ≤ PMV < 1.5: slightly warm
- 1.5 ≤ PMV < 2.5: warm
- PMV ≥ 2.5: hot

Return ONLY a valid JSON object with exactly these two mandatory keys:
1. "P_float": PMV value (a float number between -3 and 3)
2. "P_string": PMV category (must be one of: cold, cool, slightly cool, neutral, slightly warm, warm, hot)

Your output must be a single JSON object wrapped in ```JSON``` markers (case-insensitive).
"""

# Valid PMV categories (for result validation)
VALID_PMV_CATEGORIES = {
    "cold",
    "cool",
    "slightly cool",
    "neutral",
    "slightly warm",
    "warm",
    "hot",
}
# ==========================================================================================


def init_directory(directory: Path) -> Path:
    """Initialize output directory (create if not exists) and return the path"""
    directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory initialized: {directory.absolute()}")
    return directory


def sanitize_model_name(model_name: str) -> str:
    """
    Sanitize model name for valid filename:
    Replace colon (:) with hyphen (-) to avoid invalid filesystem characters
    """
    return model_name.replace(":", "-")


def build_description_sentence(row: pd.Series) -> str:
    """Build a descriptive sentence from a DataFrame row (skip NaN values)."""
    non_nan_pairs = [(col, val) for col, val in row.items() if pd.notna(val)]
    sentence_parts = [f"The value of {col} is {value}." for col, value in non_nan_pairs]
    return " ".join(sentence_parts)


def generate_all_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Generate descriptive sentences for all rows (vectorized, faster than iterrows)."""
    logger.info("Generating descriptive sentences for all data rows...")
    df["sentences"] = df.apply(build_description_sentence, axis=1)
    return df[["sentences"]]


def extract_valid_json(llm_output: str) -> Optional[Dict[str, Any]]:
    """
    Extract and parse valid JSON from LLM output.
    First try ```json``` markers, then fallback to raw JSON matching.
    Clean invalid characters and validate JSON structure.
    """
    if not isinstance(llm_output, str) or not llm_output.strip():
        logger.warning("LLM output is empty or non-string")
        return None

    # Step 1: Match JSON wrapped in ```JSON```/```json``` markers
    marker_pattern = r"```[jJ][sS][oO][nN](.*?)```"
    marker_matches = re.findall(marker_pattern, llm_output, re.DOTALL)
    json_candidates = marker_matches if marker_matches else [llm_output]

    # Step 2: Clean and parse each candidate
    for candidate in json_candidates:
        cleaned_json = candidate.strip()
        # Remove invisible control characters (common LLM output noise)
        cleaned_json = re.sub(r"[\x00-\x1F\x7F]", "", cleaned_json)

        try:
            parsed_json = json.loads(cleaned_json)
            if isinstance(
                parsed_json, dict
            ):  # Ensure output is a JSON object (not list/string)
                return parsed_json
        except json.JSONDecodeError:
            continue

    logger.warning("No valid JSON found in LLM output")
    return None


def validate_pmv_response(pmv_data: Dict[str, Any]) -> bool:
    """
    Validate LLM's PMV response for mandatory keys and valid values.
    Checks: 1) required keys exist 2) P_float is in [-3,3] 3) P_string is a valid category.
    """
    # Check mandatory keys
    required_keys = {"P_float", "P_string"}
    if not required_keys.issubset(pmv_data.keys()):
        logger.warning(
            f"Missing required keys (need {required_keys}), got {list(pmv_data.keys())}"
        )
        return False

    # Validate P_float (type + range)
    pmv_float = pmv_data["P_float"]
    if not isinstance(pmv_float, (int, float)) or not (-3 <= pmv_float <= 3):
        logger.warning(
            f"Invalid P_float: {pmv_float} (must be a number between -3 and 3)"
        )
        return False

    # Validate P_string (valid category)
    pmv_str = pmv_data["P_string"]
    if pmv_str not in VALID_PMV_CATEGORIES:
        logger.warning(
            f"Invalid P_string: {pmv_str} (must be one of {VALID_PMV_CATEGORIES})"
        )
        return False

    return True


def call_llm_for_pmv(
    client: openai.OpenAI, input_sentence: str
) -> Optional[Dict[str, Any]]:
    """
    Call LLM API to get PMV evaluation with retry logic for common failures.
    Returns valid PMV dict if successful, None otherwise.
    Handles: API errors, connection errors, JSON parsing errors, invalid PMV results.
    """
    # Build full user prompt
    full_prompt = f"Previous tasks finished. Prepare for the next task. \n{input_sentence}{PMV_EVAL_PROMPT}"

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            # Call OpenAI-compatible vLLM API
            response = client.chat.completions.create(
                model=SELECTED_VLLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": full_prompt},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                n=1,
                stop=None,
                seed=SEED,
                response_format={"type": "json_object"},
            )

            # Extract raw LLM output
            llm_raw_output = response.choices[0].message.content
            # Parse and validate JSON
            pmv_json = extract_valid_json(llm_raw_output)
            if pmv_json and validate_pmv_response(pmv_json):
                logger.info(f"LLM call successful (attempt {attempt})")
                return pmv_json

        except (APIError, RateLimitError, APIConnectionError) as e:
            logger.error(
                f"LLM API error (attempt {attempt}/{MAX_RETRY_ATTEMPTS}): {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error (attempt {attempt}/{MAX_RETRY_ATTEMPTS}): {str(e)}",
                exc_info=True,
            )

        # Log retry for non-final attempts
        if attempt < MAX_RETRY_ATTEMPTS:
            logger.info(
                f"Retrying LLM call (attempt {attempt + 1}/{MAX_RETRY_ATTEMPTS})..."
            )

    logger.error(f"LLM call failed after {MAX_RETRY_ATTEMPTS} attempts")
    return None


def save_batch_checkpoint(
    batch_data: List[Dict], batch_num: int, output_dir: Path, encoding: str
) -> None:
    """Save a batch of results as a CSV checkpoint file"""
    if not batch_data:
        logger.warning(f"Batch {batch_num} is empty, skipping save")
        return
    checkpoint_path = output_dir / f"pmv_checkpoint_batch_{batch_num}.csv"
    df_batch = pd.DataFrame(batch_data)
    df_batch.to_csv(checkpoint_path, index=False, encoding=encoding)
    logger.info(f"Checkpoint saved: {checkpoint_path.name} (rows: {len(batch_data)})")


def main():
    """Main execution workflow for PMV evaluation with batch checkpointing"""
    # 1. Initialize temp and prediction root directories
    init_directory(TEMP_OUTPUT_DIR)
    init_directory(PREDICTION_ROOT_DIR)

    # 2. Generate sanitized filename and final output path
    clean_model_name = sanitize_model_name(SELECTED_VLLM_MODEL)
    final_result_path = PREDICTION_ROOT_DIR / f"{clean_model_name}.csv"

    # 3. Load input CSV data
    try:
        logger.info(f"Loading input data from: {INPUT_CSV_PATH.absolute()}")
        df_input = pd.read_csv(INPUT_CSV_PATH, encoding=CSV_ENCODING)
        logger.info(f"Input data loaded successfully (total rows: {len(df_input)})")
    except FileNotFoundError:
        logger.critical(f"Input file not found: {INPUT_CSV_PATH}")
        return
    except Exception as e:
        logger.critical(f"Failed to load input CSV: {str(e)}")
        return

    # 4. Generate descriptive sentences for all rows
    df_sentences = generate_all_descriptions(df_input)

    # 5. Initialize OpenAI-compatible client for vLLM
    try:
        llm_client = openai.OpenAI(base_url=SELECTED_API_HOST, api_key=API_KEY)
        logger.info(
            f"LLM client initialized (host: {SELECTED_API_HOST}, model: {SELECTED_VLLM_MODEL})"
        )
    except Exception as e:
        logger.critical(f"Failed to initialize LLM client: {str(e)}")
        return

    # 6. Process rows with batch checkpointing
    all_results: List[Dict[str, Any]] = []
    current_batch: List[Dict[str, Any]] = []
    batch_number = 1
    total_rows = len(df_sentences)

    for row_idx, sentence in enumerate(df_sentences["sentences"]):
        logger.info(f"Processing row {row_idx} / {total_rows - 1}")

        # Get PMV evaluation from LLM
        pmv_data = call_llm_for_pmv(llm_client, sentence)

        # Build result row
        if pmv_data:
            result_row = {
                "row_index": row_idx,
                "PMV_float": pmv_data["P_float"],
                "PMV_string": pmv_data["P_string"],
                "processing_status": "success",
            }
        else:
            result_row = {
                "row_index": row_idx,
                "PMV_float": None,
                "PMV_string": None,
                "processing_status": "failed",
            }

        # Add to batch and full results
        current_batch.append(result_row)
        all_results.append(result_row)

        # Save checkpoint every N rows
        if len(current_batch) >= BATCH_SAVE_INTERVAL:
            save_batch_checkpoint(
                current_batch, batch_number, TEMP_OUTPUT_DIR, CSV_ENCODING
            )
            batch_number += 1
            current_batch = []  # Reset batch buffer

    # Save final partial batch (remaining rows < 10)
    if current_batch:
        save_batch_checkpoint(
            current_batch, batch_number, TEMP_OUTPUT_DIR, CSV_ENCODING
        )

    # 7. Save full consolidated results to ./prediction/[sanitized_model_name].csv
    df_final = pd.DataFrame(all_results)
    try:
        df_final.to_csv(final_result_path, index=False, encoding=CSV_ENCODING)
        # Log processing statistics
        success_cnt = sum(df_final["processing_status"] == "success")
        fail_cnt = sum(df_final["processing_status"] == "failed")
        logger.info("=" * 50)
        logger.info(f"Processing completed | Total rows: {total_rows}")
        logger.info(f"Successful: {success_cnt} | Failed: {fail_cnt}")
        logger.info(f"Final results saved to: {final_result_path.absolute()}")
        logger.info(f"Batch checkpoints saved to: {TEMP_OUTPUT_DIR.absolute()}")
        logger.info("=" * 50)
    except Exception as e:
        logger.critical(f"Failed to save final results: {str(e)}")


if __name__ == "__main__":
    main()
