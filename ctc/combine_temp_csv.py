import os

import pandas as pd

# set folder path
folder_path = "./temp"

# loop all fies in the folder
file_list = []
for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    # check if it is a file
    if os.path.isfile(file_path):
        file_list.append(file_path)

# read all csv files in the folder and combine them into one dataframe
df = pd.concat([pd.read_csv(file) for file in file_list])
# save the combined dataframe as a new csv file
df.to_csv("combined.csv", index=False)
