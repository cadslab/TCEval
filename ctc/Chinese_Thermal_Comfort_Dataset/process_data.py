import json
import os
import random
import re

import numpy as np
import pandas as pd

folder_path = "."

# loop all csv fies in the folder

file_list = []
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    if os.path.isfile(file_path) and filename.endswith(".csv"):
        file_list.append(file_path)

# read all csv files in the folder and combine them into one dataframe, drop "Unnamed: 53" if it exists
df_list = []
for file in file_list:
    # Read each CSV file
    df = pd.read_csv(file, skiprows=1, encoding="gbk")

    # Drop "Unnamed: 53" column if it exists
    if "Unnamed: 53" in df.columns:
        df = df.drop(columns=["Unnamed: 53"])
    df_list.append(df)
# Combine all cleaned DataFrames
combined_df = pd.concat(df_list, ignore_index=True)

# drop unnecessary columns
df = df.drop(
    columns=[
        "ID",
        "A1.Code",
        "A2.Date",
        "A3.Data Contributor",
        "Measured Height (m).2",
        "Measured Height (m).1",
        "Measured Height (m)",
        "D1.TSV",
        "D2.TCV",
        "D3.TAV",
    ]
)

# rename columns
df.columns = [
    "Season",
    "City",
    "Climate Zone",
    "Building Type",
    "Building Function",
    "Floors",
    "Building Operation Mode",
    "Room Length x Width (m^2)",
    "Room Height (m)",
    "Sex",
    "Age",
    "Height (m)",
    "Weight (kg)",
    "Living Years",
    # "Thermal Sensation Vote",
    # "Thermal Comfort Vote",
    # "Thermal Acceptance Vote",
    "Clothing Insulation (clo)",
    "Metabolic Rate (met)",
    "Indoor Air Temperature (℃)",
    "Indoor Relative Humidity (%)",
    "Indoor Air Velocity (m/s)",
    "Globe Temperature (℃)",
    "Indoor Air Temperature 1 (℃)",
    "Indoor Relative Humidity 1 (%)",
    "Indoor Air Velocity 1 (m/s)",
    "Globe Temperature 1 (℃)",
    "Indoor Air Temperature 2 (℃)",
    "Indoor Relative Humidity 2 (%)",
    "Indoor Air Velocity 2 (m/s)",
    "Globe Temperature 2 (℃)",
    "Roof Temperature (℃)",
    "Wall Temperature (℃)",
    "Floor Temperature (℃)",
    "Operative Temperature (℃)",
    "Mean Radiant Temperature (℃)",
    "Radiant Temperature Asymmetry (℃)",
    "PMV",
    "PPD",
    "Real-Time Outdoor Temperature (℃)",
    "Mean Daily Outdoor Temperature (℃)",
    "Monthly Mean Outdoor Temperature (℃)",
    "7-Day Running Mean Outdoor Temperature (℃)",
    "15-Day Running Mean Outdoor Temperature (℃)",
    "Mean Daily Outdoor Relative Humidity (%)",
    "Mean Daily Outdoor Air Velocity (m/s)",
]

# save the combined dataframe as a new csv file
df.to_csv("./ctc/ctc_combined.csv", encoding="gbk", index=False)

# drop rows with missing values in particular columns
df = df.dropna(
    subset=[
        "PMV",
        "PPD",
    ]
)

df_questions = df.drop(
    columns=[
        "PMV",
        "PPD",
    ]
)
df_questions.to_csv("./ctc/ctc_questions.csv", encoding="gbk", index=False)

