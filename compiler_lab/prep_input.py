import os
import pandas as pd

BASE_DIR = "/mnt/d/btech_jgec/2026-27/compiler_lab"
INPUT_XLSX = os.path.join(BASE_DIR, "input.xlsx")
TXT_INPUT = os.path.join(BASE_DIR, "matrix_input.txt")

def convert_excel_to_txt():
    df = pd.read_excel(INPUT_XLSX)
    symbols = list(df.columns[1:])
    n = len(symbols)
    
    with open(TXT_INPUT, "w") as f:
        f.write(f"{n}\n")
        f.write(" ".join(symbols) + "\n")
        
        for idx, row in df.iterrows():
            row_vals = []
            for sym in symbols:
                val = str(row[sym]).strip() if pd.notna(row[sym]) else "E"
                row_vals.append(val if val in ["<", ">", "="] else "E")
            f.write(" ".join(row_vals) + "\n")

if __name__ == "__main__":
    convert_excel_to_txt()
    print(f"[✓] Generated {TXT_INPUT}")