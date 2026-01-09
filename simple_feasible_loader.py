"""
Simple feasible data loader for Streamlit app without backend dependencies.
"""

import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SimpleFeasibleData:
    """Simple feasible data structure for optimization."""
    months: List[str]
    plant_ids: List[str]
    plant_names: Dict[str, str]
    clinker_plants: List[str]
    production_capacity: Dict[str, float]
    production_cost: Dict[str, float]
    demand: Dict[Tuple[str, str], float]
    initial_inventory: Dict[str, float]
    routes: List[Tuple[str, str, str]]
    transport_cost_per_trip: Dict[Tuple[str, str, str], float]
    transport_capacity_per_trip: Dict[Tuple[str, str, str], float]
    transport_sbq: Dict[Tuple[str, str, str], float]
    route_enabled: Dict[Tuple[str, str, str], bool]


def load_simple_feasible_data(file_path: str, selected_months: List[str]) -> SimpleFeasibleData:
    """Load feasible optimization data from Excel file."""
    
    if not selected_months:
        selected_months = ['1']  # Default to first period
    
    # Load Excel data
    xl = pd.ExcelFile(file_path)
    
    demand_df = pd.read_excel(xl, 'ClinkerDemand')
    capacity_df = pd.read_excel(xl, 'ClinkerCapacity')
    prod_cost_df = pd.read_excel(xl, 'ProductionCost')
    logistics_df = pd.read_excel(xl, 'LogisticsIUGU')
    opening_stock_df = pd.read_excel(xl, 'IUGUOpeningStock')
    iugu_type_df = pd.read_excel(xl, 'IUGUType')
    
    # Get unique codes
    all_iugu_codes = set()
    all_iugu_codes.update(demand_df['IUGU CODE'].unique())
    all_iugu_codes.update(capacity_df['IU CODE'].unique())
    all_iugu_codes.update(logistics_df['FROM IU CODE'].unique())
    all_iugu_codes.update(logistics_df['TO IUGU CODE'].unique())
    
    plant_ids = [code for code in all_iugu_codes if pd.notna(code)]
    plant_names = {code: code for code in plant_ids}
    
    # Get clinker plants
    iu_codes = set(capacity_df['IU CODE'].unique())
    clinker_plants = list(iu_codes)
    
    # Time periods
    months = selected_months
    
    # Check if we have a mismatch
    available_periods = set()
    if 'TIME PERIOD' in capacity_df.columns:
        available_periods.update(capacity_df['TIME PERIOD'].astype(str).unique())
    if 'TIME PERIOD' in demand_df.columns:
        available_periods.update(demand_df['TIME PERIOD'].astype(str).unique())
    
    # If none of the selected months are in available periods, fallback to available periods
    # This fixes the issue where UI passes '2024-01' but Excel has '1'
    if not any(m in available_periods for m in months):
        print(f"Warning: Selected months {months} not found in Excel {available_periods}. Falling back to available periods.")
        # Filter out 'nan'
        months = sorted([p for p in available_periods if p != 'nan'])

    
    # Production capacity (with feasibility adjustment)
    production_capacity = {}
    for _, row in capacity_df.iterrows():
        iu_code = str(row['IU CODE'])
        period = str(row['TIME PERIOD'])
        capacity = float(row['CAPACITY'])
        if period in months and iu_code in plant_ids:
            # Apply 20% capacity expansion for feasibility
            production_capacity[iu_code] = capacity * 1.2
    
    # Production cost
    production_cost = {}
    for _, row in prod_cost_df.iterrows():
        iu_code = str(row['IU CODE'])
        period = str(row['TIME PERIOD'])
        cost = float(row['PRODUCTION COST'])
        if period in months and iu_code in plant_ids:
            production_cost[iu_code] = cost
    
    # Demand (with feasibility adjustment)
    demand = {}
    for pid in plant_ids:
        for period in months:
            demand[(pid, period)] = 0.0
    
    for _, row in demand_df.iterrows():
        iugu_code = str(row['IUGU CODE'])
        period = str(row['TIME PERIOD'])
        demand_qty = float(row['DEMAND'])
        if period in months and iugu_code in plant_ids:
            # Apply 30% demand reduction for feasibility
            demand[(iugu_code, period)] += demand_qty * 0.7
    
    # Initial inventory (with feasibility adjustment)
    initial_inventory = {}
    for _, row in opening_stock_df.iterrows():
        iugu_code = str(row['IUGU CODE'])
        opening_stock = float(row['OPENING STOCK'])
        if iugu_code in plant_ids:
            # Apply 50% stock expansion for feasibility
            initial_inventory[iugu_code] = opening_stock * 1.5
    
    # Ensure all plants have inventory
    for pid in plant_ids:
        if pid not in initial_inventory:
            initial_inventory[pid] = 1000.0  # Default small inventory
    
    # Transport routes
    routes = []
    transport_cost_per_trip = {}
    transport_capacity_per_trip = {}
    transport_sbq = {}
    route_enabled = {}
    
    for _, row in logistics_df.iterrows():
        from_iu = str(row['FROM IU CODE'])
        to_iugu = str(row['TO IUGU CODE'])
        transport_code = str(row['TRANSPORT CODE'])
        period = str(row['TIME PERIOD'])
        freight_cost = float(row['FREIGHT COST'])
        handling_cost = float(row['HANDLING COST'])
        qty_multiplier = float(row['QUANTITY MULTIPLIER'])
        
        if period in months and from_iu in plant_ids and to_iugu in plant_ids:
            route_key = (from_iu, to_iugu, transport_code)
            
            if route_key not in routes:
                routes.append(route_key)
            
            transport_cost_per_trip[route_key] = freight_cost + handling_cost
            transport_capacity_per_trip[route_key] = max(qty_multiplier, 1.0)
            transport_sbq[route_key] = 0.0
            route_enabled[route_key] = True
    
    return SimpleFeasibleData(
        months=months,
        plant_ids=plant_ids,
        plant_names=plant_names,
        clinker_plants=clinker_plants,
        production_capacity=production_capacity,
        production_cost=production_cost,
        demand=demand,
        initial_inventory=initial_inventory,
        routes=routes,
        transport_cost_per_trip=transport_cost_per_trip,
        transport_capacity_per_trip=transport_capacity_per_trip,
        transport_sbq=transport_sbq,
        route_enabled=route_enabled,
    )
