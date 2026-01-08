"""Analyze the Excel dataset to understand structure and constraints."""

import pandas as pd
import sys

def analyze_excel(file_path):
    """Read and analyze all sheets from the Excel file."""
    
    xl = pd.ExcelFile(file_path)
    
    print("=" * 80)
    print("DATASET ANALYSIS")
    print("=" * 80)
    print(f"\nTotal sheets: {len(xl.sheet_names)}\n")
    
    sheets_data = {}
    
    for sheet_name in xl.sheet_names:
        print(f"\n{'='*80}")
        print(f"SHEET: {sheet_name}")
        print(f"{'='*80}")
        
        df = pd.read_excel(xl, sheet_name)
        sheets_data[sheet_name] = df
        
        print(f"Shape: {df.shape} (rows x columns)")
        print(f"\nColumns: {list(df.columns)}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        print(f"\nData types:")
        print(df.dtypes)
        print(f"\nNull values:")
        print(df.isnull().sum())
        
        # Check for IUGU CODE column
        if 'IUGU CODE' in df.columns:
            unique_codes = df['IUGU CODE'].unique()
            print(f"\nUnique IUGU Codes: {len(unique_codes)}")
            print(f"Sample codes: {list(unique_codes[:10])}")
    
    return sheets_data

if __name__ == "__main__":
    file_path = "Dataset_Dummy_Clinker_3MPlan.xlsx"
    try:
        data = analyze_excel(file_path)
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
