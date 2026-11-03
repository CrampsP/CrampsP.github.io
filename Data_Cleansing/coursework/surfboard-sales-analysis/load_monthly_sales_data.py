import polars as pl
import numpy as np

file_names = [
    'Jan26.csv','Feb26.csv','March26.csv','April26.csv','May26.csv','June26.csv','July26.csv','Aug26.csv'
]

dfs = {}

for file in file_names:
    key = file.replace('.csv', '').lower()

    df = pl.read_csv(
        file,
        skip_rows=9,
        infer_schema_length=0
    )

    # Remove commas from all columns
    df = df.with_columns(
        pl.all().str.replace_all(",", "")
    )

    # Store the processed DataFrame in the dictionary
    globals()[key] = df

col_list = df.columns

var_names = [file.replace('.csv', '').lower() for file in file_names]

all_dfs = [globals()[name] for name in var_names]

df_full = pl.concat(all_dfs)

print("Column names:")
for column in df_full.columns:
    print(column)

print("\nFull database:")
print(df_full)