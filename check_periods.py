
import pandas as pd
try:
    df = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='ClinkerDemand')
    print(f"Unique Periods (ClinkerDemand): {df['TIME PERIOD'].unique()}")
    
    df2 = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='ClinkerCapacity')
    print(f"Unique Periods (ClinkerCapacity): {df2['TIME PERIOD'].unique()}")
except Exception as e:
    print(e)
