from vn30_quant_bot import get_data, analyze_signal
import pandas as pd

def check_cols():
    df = get_data('HPG')
    if df is None:
        print("Failed to get data")
        return
    
    analyze_signal(df)
    print("Columns:", df.columns.tolist())
    
    bbu = [c for c in df.columns if c.startswith('BBU_')]
    print("BBU Columns:", bbu)
    
if __name__ == "__main__":
    check_cols()

