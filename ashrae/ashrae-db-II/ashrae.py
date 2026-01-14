import pandas as pd
import numpy as np

def merge_metadata_with_measurements(measurements_path, metadata_path):
    """
    Merge metadata with measurements (in-memory only, no file saved).
    
    Args:
        measurements_path (str): Path to db_measurements_v2.1.0.csv
        metadata_path (str): Path to db_metadata.csv
    
    Returns:
        pd.DataFrame: Merged dataset (measurements + metadata) in memory
    """
    print("=== Step 1: Loading Input Datasets ===")
    df_measurements = pd.read_csv(measurements_path, low_memory=False)
    df_metadata = pd.read_csv(metadata_path)
    print(f"   - Measurements: {df_measurements.shape[0]} rows, {df_measurements.shape[1]} columns")
    print(f"   - Metadata: {df_metadata.shape[0]} rows, {df_metadata.shape[1]} columns")

    print("\n=== Step 2: Verifying Building ID Consistency ===")
    unique_meas_buildings = df_measurements['building_id'].nunique()
    unique_meta_buildings = df_metadata['building_id'].nunique()
    print(f"   - Unique buildings in measurements: {unique_meas_buildings}")
    print(f"   - Unique buildings in metadata: {unique_meta_buildings}")
    
    missing_buildings = set(df_measurements['building_id'].unique()) - set(df_metadata['building_id'].unique())
    print(f"   - {'✓' if len(missing_buildings) == 0 else '⚠ Warning:'} All building_ids have metadata matches")

    print("\n=== Step 3: Merging Datasets (In-Memory) ===")
    df_merged = pd.merge(
        left=df_measurements,
        right=df_metadata,
        on='building_id',
        how='left',
        suffixes=('', '_metadata')
    )
    print(f"   - Merged dataset: {df_merged.shape[0]} rows, {df_merged.shape[1]} columns")
    print(f"   - Columns added from metadata: {df_merged.shape[1] - df_measurements.shape[1]}")
    return df_merged

def process_measurements_for_llm(df_merged, llm_output_path):
    """
    Process merged data into LLM-ready format and save final file.
    
    Args:
        df_merged (pd.DataFrame): In-memory merged dataset
        llm_output_path (str): Path to save measurements.csv
    
    Returns:
        pd.DataFrame: LLM-ready dataset
    """
    print("\n=== Step 4: Filtering Critical Data for LLM ===")
    df_llm = df_merged.loc[
        (~df_merged['ta'].isna()) &
        (~df_merged['pmv'].isna()) &
        (~df_merged['rh'].isna()) &
        (~df_merged['t_out_isd'].isna() | ~df_merged['t_out'].isna())
    ].copy()

    # Calculate retention metrics
    initial_rows = len(df_merged)
    initial_buildings = len(df_merged['building_id'].unique())
    filtered_rows = len(df_llm)
    filtered_buildings = len(df_llm['building_id'].unique())
    
    print(f"   - Rows: {initial_rows} → {filtered_rows} (retention: {round((filtered_rows/initial_rows)*100,2)}%)")
    print(f"   - Buildings: {initial_buildings} → {filtered_buildings} (retention: {round((filtered_buildings/initial_buildings)*100,2)}%)")

    print("\n=== Step 5: Creating Unified Outdoor Temperature ===")
    df_llm['t_out_combined'] = df_llm['t_out_isd'].fillna(df_llm['t_out'])
    print(f"   - ✓ 't_out_combined' has {df_llm['t_out_combined'].isna().sum()} missing values")

    print("\n=== Step 6: Removing Redundant Columns ===")
    df_llm = df_llm.drop(columns=['t_out_isd', 't_out'])
    print("   - Removed: ['t_out_isd', 't_out'] | Added: ['t_out_combined']")

    print("\n=== Step 7: Saving Final LLM Dataset ===")
    # shuffle the database
    df_llm = df_llm.sample(frac=1, random_state=42).reset_index(drop=True)
    df_llm.to_csv(llm_output_path, index=False)
    print(f"   - ✓ Saved to: {llm_output_path}")

    # Final summary
    print("\n=== Final Dataset Summary ===")
    print(f"Total Rows: {len(df_llm)} | Columns: {len(df_llm.columns)}")
    print(f"Key Columns: 'ta', 'thermal_sensation', 'rh', 't_out_combined', 'building_id', 'country'")

    return df_llm

# Main execution
if __name__ == "__main__":
    # Define file paths
    MEASUREMENTS_PATH = "./v2.1.0/db_measurements_v2.1.0.csv"
    METADATA_PATH = "./v2.1.0/db_metadata.csv"
    LLM_OUTPUT_PATH = "measurements.csv"

    # Run pipeline
    merged_data = merge_metadata_with_measurements(MEASUREMENTS_PATH, METADATA_PATH)
    llm_data = process_measurements_for_llm(merged_data, LLM_OUTPUT_PATH)

    # Show sample
    print("\n=== Sample of Final Data (First 3 Rows) ===")
    sample_cols = ['record_id', 'building_id', 'ta', 'rh', 'pmv', 't_out_combined', 'country', 'climate']
    print(llm_data[sample_cols].head(3))