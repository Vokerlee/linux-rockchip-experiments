import pandas as pd
import glob
import sys
import os

if len(sys.argv) != 3:
    print(f"Usage: python {sys.argv[0]} <folder-name> <output-file>")
    sys.exit(1)

folder_name = sys.argv[1]
output_file = sys.argv[2]

if not os.path.isdir(folder_name):
    print(f"Error: The folder '{folder_name}' does not exist.")
    sys.exit(1)

csv_files = glob.glob(os.path.join(folder_name, "*.csv"))

dataframes = [pd.read_csv(filename) for filename in csv_files]
combined_csv = pd.concat(dataframes, ignore_index=True)
combined_csv.to_csv(output_file, index=False)

print(f"Combined CSV saved to '{output_file}'")
