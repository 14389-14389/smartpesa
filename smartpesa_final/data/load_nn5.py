import arff
import pandas as pd
import os

file_path = os.path.expanduser('nn5_daily_dataset_with_missing_values.ts')
with open(file_path, 'r') as f:
    data = arff.load(f)

df = pd.DataFrame(data['data'], columns=[attr[0] for attr in data['attributes']])
print("Data shape:", df.shape)
print("First 5 rows:")
print(df.head())
print("\nColumn names:", df.columns.tolist())
print("Data types:\n", df.dtypes)
