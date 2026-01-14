import os

import pandas as pd

target_file_path = "./ashrae-db-II/measurements.csv"
df = pd.read_csv(target_file_path, nrows=8100)
df_pmv = pd.DataFrame(columns=["PMV_float_base", "PMV_string_base"])
df_pmv["PMV_float_base"] = df["pmv"]
# convert captial PMV values to lowercase
df_pmv["PMV_string_base"] = df_pmv["PMV_string_base"].str.lower()


for i in range(0, len(df_pmv["PMV_float_base"])):
    if df_pmv.loc[i, "PMV_float_base"] < -2.5:
        df_pmv.loc[i, "PMV_string_base"] = "cold"
    elif df_pmv.loc[i, "PMV_float_base"] < -1.5:
        df_pmv.loc[i, "PMV_string_base"] = "cool"
    elif df_pmv.loc[i, "PMV_float_base"] < -0.5:
        df_pmv.loc[i, "PMV_string_base"] = "slightly cool"
    elif df_pmv.loc[i, "PMV_float_base"] < 0.5:
        df_pmv.loc[i, "PMV_string_base"] = "neutral"
    elif df_pmv.loc[i, "PMV_float_base"] < 1.5:
        df_pmv.loc[i, "PMV_string_base"] = "slightly warm"
    elif df_pmv.loc[i, "PMV_float_base"] < 2.5:
        df_pmv.loc[i, "PMV_string_base"] = "warm"
    else:
        df_pmv.loc[i, "PMV_string_base"] = "hot"

pmv_path = "./prediction"

# loop all fies in the folder
for filename in os.listdir(pmv_path):
    file_path = os.path.join(pmv_path, filename)
    df = pd.read_csv(file_path)
    df_pmv_llm = pd.concat([df_pmv, df], axis=1)
    df_pmv_llm.to_csv(f"./assembled/{filename.rsplit('.',1)[0]}.csv", index=False)
