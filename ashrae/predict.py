import json
import os
import re
import time
from pathlib import Path

import openai
import pandas as pd

# ===================== 1. Define Column Description Dictionary =====================
column_descriptions = {
    # Metadata Columns
    "building_id": "Unique building identifier [integer]. Note: some building IDs are inferred - see building_id_inf in metadata table",
    "building_id_inf": "Flag indicating if unique building identifier was from original data source [no] or inferred [yes] from unique groupings of publication, country, city, season, building type, and cooling type",
    "contributor": "Principal contact person regarding the data",
    "publication": "Published paper describing the project from where the data was collected",
    "region": "Region of field study",
    "country": "Country of field study",
    "city": "City of field study",
    "lat": "Latitude of city [°]",
    "lon": "Longitude of city [°]",
    "climate": "Type of climate according to Köppen climate classification",
    "building_type": "Type of building [office, multifamily housing, classroom, senior center, other]",
    "cooling_type": "Cooling strategy of building [air conditioned, mixed mode, naturally ventilated]",
    "year": "Year of field study [yyyy]",
    "records": "Number of records for that building ID",
    "has_age": "Flag indicating if there age was recorded [yes, no] and if it was a categorical variable in the original data source [categorical]",
    "has_ec": "Flag indicating if environmental controls were in the original data source [yes, no]",
    "has_timestamp": "Flag indicating if measurement timestamp was in the original data source [yes, no]",
    "timezone": "IANA time zone of field study",
    "met_source": "Source of meteorological data for t_out and rh_out [ghcn_d = from GHCN-D, original_data = from original data source; rp884 = from RP884 database]",
    "isd_station": "ISD station code for t_out_isd, rh_out_isd and t_mot_isd",
    "isd_distance": "Estimated distance of ISD station to city of field study [km]",
    "database": "Version of database when data source was added [1, 2, 2.1]",
    "quality_assurance": "Flag indicating if dataset from contributor passed automated quality assurance check [pass, fail]",
    # Measurements Columns
    "timestamp": "Timestamp of measurement [yyyy-mm-dd]",
    "season": "Season measurement was made [summer, winter, hot/wet, cool/dry]. Note: based on the following assumptions when timestamp and location are known: northern hemisphere latitudes <20 are hot/wet from May-Oct and cool/dry from Nov-Apr; northern hemisphere latitudes >=20 are summer May-Oct and winter from Nov-Apr; vice versa for Southern Hemisphere",
    "subject_id": "Unique subject identifier for future studies with repeat samples [integer]",
    "age": "Age of subject [years]. Note: some studies used age ranges instead of years - see has_age in metadata table",
    "gender": "Gender of subject [female, male]",
    "ht": "Height of subject [m]",
    "wt": "Weight of subject [kg]",
    "ta": "Air temperature measured in the occupied zone [°C]",
    "ta_h": "Air temperature measured at 1.1 m above the floor [°C]",
    "ta_m": "Air temperature measured at 0.6 m above the floor [°C]",
    "ta_l": "Air temperature measured at 0.1 m above the floor [°C]",
    "top": "Operative temperature calculated for the occupied zone [°C]",
    "tr": "Radiant temperature measured in the occupied zone [°C]",
    "tg": "Globe temperature measured in the occupied zone [°C]",
    "tg_h": "Globe temperature measured at 1.1 m above the floor [°C]",
    "tg_m": "Globe temperature measured at 0.6 m above the floor [°C]",
    "tg_l": "Globe temperature measured at 0.1 m above the floor [°C]",
    "rh": "Relative humidity [%]",
    "vel": "Air speed measured in the occupied zone [m/s]",
    "vel_h": "Air speed measured at 1.1 m above the floor [m/s]",
    "vel_m": "Air speed measured at 0.6 m above the floor [m/s]",
    "vel_l": "Air speed measured at 0.1 m above the floor [m/s]",
    "vel_r": "Relative air speed used to calculate the PMV [m/s]",
    "met": "Average metabolic rate of the subject [met]",
    "clo": "Intrinsic clothing ensemble insulation of the subject [clo]",
    "clo_d": "Dynamic clothing, used to calculate the PMV [clo]",
    "activity_10": "Average metabolic rate of the subject in the last 10 minutes [met]",
    "activity_20": "Average metabolic rate of the subject in the last 20 minutes [met]",
    "activity_30": "Average metabolic rate of the subject in the last 30 minutes [met]",
    "activity_60": "Average metabolic rate of the subject in the last 60 minutes [met]",
    "thermal_sensation": "Vote on the ASHRAE thermal sensation scale [-3 (cold) to 0 (neutral) +3 (hot)]",
    "pmv": "Predicted mean vote, calculated in compliance with the ISO 7730",
    "pmv_ce": "Predicted mean vote, calculated in compliance with the ASHRAE 55 2020",
    "ppd": "Predicted percentage dissatisfied [%] calculated in compliance with the ISO 7730",
    "ppd_ce": "Predicted percentage dissatisfied [%] calculated in compliance with the ASHRAE 55 2020",
    "set": "Standard effective temperature [°C]",
    "thermal_acceptability": "Thermal acceptability [acceptable, unacceptable]",
    "thermal_preference": "Thermal preference [cooler, no change, warmer]",
    "thermal_comfort": "Thermal comfort [1 (very uncomfortable) to 6 (very comfortable)]",
    "air_movement_acceptability": "Air movement acceptability [acceptable, unacceptable]",
    "air_movement_preference": "Air movement preference [less, no change, more]",
    "blind_curtain": "State of blinds or curtains [0 = open; 1 = closed]",
    "fan": "State of fan [0 = off, 1 = on]",
    "window": "State of window [0 = open, 1 = closed]",
    "door": "State of doors [0 = open, 1 = closed]",
    "heater": "State of heater [0 = off, 1 = on]",
    "t_out": "Outdoor air temperature from original dataset [°C]",
    "rh_out": "Outdoor relative humidity from original dataset [%]",
    "t_out_isd": "Average daily outdoor air temperature from ISD [°C]",
    "rh_out_isd": "Average relative humidity from ISD [%]",
    "t_mot_isd": "Calculated 7-day running mean outdoor temperature [°C]",
}

# ===================== 2. Data Preparation =====================
# Load data and preprocess
df_measurements = pd.read_csv("./ashrae-db-II/measurements.csv", nrows=8100)
df_measurements["t_out"] = df_measurements["t_out_combined"]
df_measurements = df_measurements.drop(
    columns=[
        "t_out_combined",
        "building_id",
        "subject_id",
        "building_id_inf",
        "contributor",
        "publication",
        "year",
        "records",
        "has_age",
        "has_ec",
        "has_timestamp",
        "timezone",
        "met_source",
        "isd_station",
        "isd_distance",
        "database",
        "quality_assurance",
        "thermal_sensation",
        "pmv",
        "pmv_ce",
        "ppd",
        "ppd_ce",
        "set",
        "thermal_acceptability",
        "thermal_preference",
        "thermal_comfort",
    ]
)

# Generate descriptive sentences for each row (fixed value formatting)
sentences = []
for index, row in df_measurements.iterrows():
    non_nan_pairs = [(col, value) for col, value in row.items() if pd.notna(value)]
    sentence_parts = []

    for col, value in non_nan_pairs:
        # Get full column description
        col_desc = column_descriptions.get(col, col)

        # Value formatting (supports int/float)
        if isinstance(value, int):
            formatted_value = str(value)
        elif isinstance(value, float):
            formatted_value = str(int(value)) if value.is_integer() else f"{value:.2f}"
        else:
            formatted_value = str(value).strip()

        sentence_parts.append(f"The {col_desc} is {formatted_value}.")

    sentence = " ".join(sentence_parts)
    sentences.append(sentence)

# Save to new DataFrame
questions = pd.DataFrame({"sentences": sentences})

# ===================== 3. LLM Configuration =====================
prompt = """
Evaluate the thermal sensation using the Predicted Mean Vote (PMV) scale. 
Fill in missing information based on your assumptions if needed.
PMV scale rules:
- PMV < -2.5: cold
- -2.5 ≤ PMV < -1.5: cool
- -1.5 ≤ PMV < -0.5: slightly cool
- -0.5 ≤ PMV < 0.5: neutral
- 0.5 ≤ PMV < 1.5: slightly warm
- 1.5 ≤ PMV < 2.5: warm
- PMV ≥ 2.5: hot

Return ONLY a valid JSON object with exactly these two keys:
1. "P_float": PMV value (float between -3 and 3)
2. "P_string": PMV category (one of: cold, cool, slightly cool, neutral, slightly warm, warm, hot)

Your output must be a single JSON object wrapped in ```JSON``` markers.
"""

MAX_NUM_TOKENS = 10240
llm_list = [
    "mistral-small3.2",
    "gemma3:27b",
    "qwen3:32b",
    "deepseek-r1:32b",
    "gpt-oss:120b",
    "Qwen3-Next-80B-A3B-Thinking",
]
llm_model = llm_list[3]
host_list = [
    "http://192.168.3.12:11434/v1",
    "http://192.168.3.9:11434/v1",
    "http://192.168.3.9:8000/v1",
]
server_url = host_list[0]  # Fixed typo: sever_url -> server_url

# Create temporary folders
Path("./temp").mkdir(parents=True, exist_ok=True)
Path("./prediction").mkdir(parents=True, exist_ok=True)
Path("./assembled").mkdir(parents=True, exist_ok=True)

# Initialize OpenAI client
client = openai.OpenAI(
    base_url=server_url,  # Updated variable name
    api_key="tceval",
)


# ===================== 4. Core Functions =====================
def get_llm_response(client, user_message, temperature=0.4, max_retries=3):
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = client.chat.completions.create(
                model=llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "keep the answers clean and neat.",  # Fixed typo: net -> neat
                    },
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=MAX_NUM_TOKENS,
                n=1,
                stop=None,
                seed=0,
                enable_thinking=True,  # set to false to disable thinking prompt
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            retry_count += 1
            print(f"API call failed (retry {retry_count}/{max_retries}): {str(e)}")
            time.sleep(1)
    raise Exception(f"Maximum retry limit {max_retries} reached, API call failed")


def extract_json_between_markers(llm_output):
    json_pattern = r"```(?:json|JSON)(.*?)```"
    matches = re.findall(json_pattern, llm_output, re.DOTALL)

    if not matches:
        json_pattern = r"\{[\s\S]*\}"
        matches = re.findall(json_pattern, llm_output, re.DOTALL)

    for json_string in matches:
        json_string = json_string.strip()
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            try:
                json_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_string)
                json_clean = json_clean.replace("'", '"')
                return json.loads(json_clean)
            except:
                continue

    return None


# ===================== 5. Main Execution Logic (Index Removed) =====================
start_idx = 0
end_idx = len(questions["sentences"])
all_results = []

for i in range(start_idx, end_idx):
    try:
        print(f"Processing PMV evaluation for record {i}...")  # Progress print only
        user_question = f"""
        Previous tasks finished. New task, based on the following thermal comfort measurements, describe your thermal sensation with PMV:
        {questions['sentences'][i]}
        
        {prompt}
        """

        pmv_response = get_llm_response(client, user_question, temperature=0.4)
        pmv_json = extract_json_between_markers(pmv_response)

        # Retry JSON parsing
        retry_count = 0
        while pmv_json is None and retry_count < 3:
            print(f"JSON parsing failed, retrying {retry_count+1}...")
            pmv_response = get_llm_response(client, user_question, temperature=0.4)
            pmv_json = extract_json_between_markers(pmv_response)
            retry_count += 1

        # Extract results (index removed)
        result = {
            "PMV_float": pmv_json.get("P_float"),
            "PMV_string": pmv_json.get("P_string"),
        }
        all_results.append(result)
        print(f"Record {i} processed successfully: {result}")

        # Save single record result (PMV fields only)
        temp_df = pd.DataFrame([result])
        temp_df.to_csv(f"./temp/temp_df_{i}.csv", index=False)

        time.sleep(0.5)

    except Exception as e:
        print(f"Error processing record {i}: {str(e)}")
        result = {"PMV_float": None, "PMV_string": None}
        temp_df = pd.DataFrame([result])
        temp_df.to_csv(f"./temp/temp_df_{i}.csv", index=False)
        continue

# Final save of all results (no index)
if all_results:
    final_df = pd.DataFrame(all_results)
    final_df.to_csv(f"./prediction/{llm_model.replace(':', '-')}.csv", index=False)
    print(
        f"All records processed. Final results saved to {llm_model.replace(':', '-')}.csv"
    )
else:
    print("No valid data was processed")
