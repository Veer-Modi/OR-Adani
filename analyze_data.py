import pandas as pd
import numpy as np

# Read all sheets
xl = pd.ExcelFile('Dataset_Dummy_Clinker_3MPlan.xlsx')

print('=== CLINKER OPTIMIZATION PROBLEM ANALYSIS ===')

# 1. Demand analysis
demand = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='ClinkerDemand')
print(f'\n1. DEMAND ANALYSIS:')
print(f'   Unique IUGU codes: {demand["IUGU CODE"].nunique()}')
print(f'   Time periods: {sorted(demand["TIME PERIOD"].unique())}')
print(f'   Total demand across all periods: {demand["DEMAND"].sum():,.0f}')
print(f'   Average demand per period: {demand["DEMAND"].mean():,.0f}')

# 2. Capacity analysis  
capacity = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='ClinkerCapacity')
print(f'\n2. CAPACITY ANALYSIS:')
print(f'   Unique IU codes: {capacity["IU CODE"].nunique()}')
print(f'   Time periods: {sorted(capacity["TIME PERIOD"].unique())}')
print(f'   Total capacity across all periods: {capacity["CAPACITY"].sum():,.0f}')
print(f'   Average capacity per IU: {capacity["CAPACITY"].mean():,.0f}')

# 3. Cost analysis
prod_cost = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='ProductionCost')
logistics = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='LogisticsIUGU')
print(f'\n3. COST ANALYSIS:')
print(f'   Production cost range: {prod_cost["PRODUCTION COST"].min():,.0f} - {prod_cost["PRODUCTION COST"].max():,.0f}')
print(f'   Logistics records: {len(logistics)}')
print(f'   Freight cost range: {logistics["FREIGHT COST"].min():,.0f} - {logistics["FREIGHT COST"].max():,.0f}')
print(f'   Handling cost range: {logistics["HANDLING COST"].min():,.0f} - {logistics["HANDLING COST"].max():,.0f}')

# 4. Stock analysis
opening_stock = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='IUGUOpeningStock')
closing_stock = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='IUGUClosingStock')
print(f'\n4. STOCK ANALYSIS:')
print(f'   Total opening stock: {opening_stock["OPENING STOCK"].sum():,.0f}')
print(f'   Locations with closing stock constraints: {closing_stock["IUGU CODE"].nunique()}')

# 5. IUGU types
iugu_type = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='IUGUType')
print(f'\n5. IUGU TYPES:')
print(f'   Plant types: {iugu_type["PLANT TYPE"].value_counts().to_dict()}')

# 6. Constraints analysis
constraints = pd.read_excel('Dataset_Dummy_Clinker_3MPlan.xlsx', sheet_name='IUGUConstraint')
print(f'\n6. CONSTRAINTS ANALYSIS:')
print(f'   Total constraint records: {len(constraints)}')
print(f'   Bound types: {constraints["BOUND TYPEID"].value_counts().to_dict()}')
print(f'   Value types: {constraints["VALUE TYPEID"].value_counts().to_dict()}')

print('\n=== OPTIMIZATION PROBLEM SUMMARY ===')
print('This appears to be a multi-period supply chain optimization problem for clinker production and distribution.')
print('Key elements:')
print('- Production facilities (IU codes) with capacity constraints')
print('- Demand points (IUGU codes) with demand requirements')
print('- Transportation logistics with costs')
print('- Inventory management (opening/closing stocks)')
print('- Multi-period planning horizon')
print('- Objective: Minimize total cost (production + transportation + inventory)')
