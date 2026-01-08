"""Excel data loader for optimization.

This module loads data from the Excel dataset file and converts it
to the format expected by the optimization model.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd

from backend.optimization.data_loader import OptimizationData


@dataclass
class ExcelOptimizationData(OptimizationData):
    """Extended optimization data with Excel-specific fields."""
    
    # IUGU code mappings
    iugu_to_plant_id: Dict[str, str]  # Maps IUGU CODE to plant_id
    plant_id_to_iugu: Dict[str, str]  # Maps plant_id to IUGU CODE
    
    # Transport constraints from IUGUConstraint sheet
    transport_bounds: Dict[Tuple[str, str, str, str], Dict[str, float]]  # (IU_CODE, TRANSPORT_CODE, IUGU_CODE, TIME_PERIOD) -> {bound_type: value}
    
    # Min fulfillment percentages
    min_fulfillment: Dict[Tuple[str, str], float]  # (IUGU_CODE, TIME_PERIOD) -> min_fulfillment %
    
    # Closing stock constraints
    min_closing_stock: Dict[Tuple[str, str], float]  # (IUGU_CODE, TIME_PERIOD) -> min_closing_stock
    max_closing_stock: Dict[Tuple[str, str], float]  # (IUGU_CODE, TIME_PERIOD) -> max_closing_stock
    
    # Transport code limits (from IUGUConstraint with bound type L/U)
    transport_code_limits: Dict[Tuple[str, str, str], Dict[str, float]]  # (IU_CODE, TRANSPORT_CODE, TIME_PERIOD) -> {lower: value, upper: value}


def load_excel_data(file_path: str, selected_months: List[str]) -> ExcelOptimizationData:
    """Load optimization data from Excel file.
    
    Args:
        file_path: Path to the Excel file
        selected_months: List of time periods (months) to optimize
        
    Returns:
        ExcelOptimizationData with all required fields
    """
    
    if not os.path.exists(file_path):
        raise ValueError(f"Excel file not found: {file_path}")
    
    xl = pd.ExcelFile(file_path)
    
    # Load all sheets
    demand_df = pd.read_excel(xl, 'ClinkerDemand')
    capacity_df = pd.read_excel(xl, 'ClinkerCapacity')
    prod_cost_df = pd.read_excel(xl, 'ProductionCost')
    logistics_df = pd.read_excel(xl, 'LogisticsIUGU')
    constraints_df = pd.read_excel(xl, 'IUGUConstraint')
    opening_stock_df = pd.read_excel(xl, 'IUGUOpeningStock')
    hub_opening_df = pd.read_excel(xl, 'HubOpeningStock')
    closing_stock_df = pd.read_excel(xl, 'IUGUClosingStock')
    iugu_type_df = pd.read_excel(xl, 'IUGUType')
    
    # Convert selected_months to time periods (assuming format like "2024-01" -> 1, "2024-02" -> 2)
    # For now, assume selected_months are already time period numbers or convert them
    time_periods = []
    for month in selected_months:
        # Try to extract time period number
        try:
            # If month is like "2024-01", extract month number
            if '-' in month:
                period = int(month.split('-')[1])
            else:
                period = int(month)
            time_periods.append(period)
        except:
            # If conversion fails, use month as-is and try to match
            time_periods.append(month)
    
    # Get unique IUGU codes
    all_iugu_codes = set()
    all_iugu_codes.update(demand_df['IUGU CODE'].unique())
    all_iugu_codes.update(capacity_df['IU CODE'].unique())
    all_iugu_codes.update(logistics_df['FROM IU CODE'].unique())
    all_iugu_codes.update(logistics_df['TO IUGU CODE'].unique())
    
    # Create plant_id mapping (using IUGU codes as plant IDs)
    iugu_to_plant_id = {code: code for code in all_iugu_codes if pd.notna(code)}
    plant_id_to_iugu = {v: k for k, v in iugu_to_plant_id.items()}
    
    # Get IU codes (production plants)
    iu_codes = set(capacity_df['IU CODE'].unique())
    
    # Get GU codes (demand points) from IUGUType
    gu_codes = set(iugu_type_df[iugu_type_df['PLANT TYPE'] == 'GU']['IUGU CODE'].unique())
    
    # Plant IDs (all IUGU codes)
    plant_ids = list(all_iugu_codes)
    plant_ids = [p for p in plant_ids if pd.notna(p)]
    
    # Plant names (using IUGU codes as names for now)
    plant_names = {pid: pid for pid in plant_ids}
    
    # Plant types
    plant_type = {}
    for _, row in iugu_type_df.iterrows():
        iugu_code = str(row['IUGU CODE'])
        ptype = str(row['PLANT TYPE'])
        if iugu_code in plant_ids:
            if ptype == 'IU':
                plant_type[iugu_code] = 'Clinker Plant'
            elif ptype == 'GU':
                plant_type[iugu_code] = 'Grinding Unit'
            else:
                plant_type[iugu_code] = 'Other'
    
    # Clinker plants (IU codes)
    clinker_plants = list(iu_codes)
    
    # Production capacity: initialize 0 for all plants, then override IU codes
    production_capacity: Dict[str, float] = {pid: 0.0 for pid in plant_ids}
    for _, row in capacity_df.iterrows():
        iu_code = str(row['IU CODE'])
        period = int(row['TIME PERIOD'])
        capacity = float(row['CAPACITY'])
        if period in time_periods and iu_code in plant_ids:
            production_capacity[iu_code] = capacity  # Use latest capacity for now
    
    # Production cost: initialize 0 for all plants, then override IU codes
    production_cost: Dict[str, float] = {pid: 0.0 for pid in plant_ids}
    for _, row in prod_cost_df.iterrows():
        iu_code = str(row['IU CODE'])
        period = int(row['TIME PERIOD'])
        cost = float(row['PRODUCTION COST'])
        if period in time_periods and iu_code in plant_ids:
            production_cost[iu_code] = cost  # Use latest cost for now
    
    # Demand: (IUGU_CODE, TIME_PERIOD) -> DEMAND
    # Default 0 for all plant/period combinations
    demand: Dict[Tuple[str, str], float] = {}
    for pid in plant_ids:
        for period in time_periods:
            demand[(pid, str(period))] = 0.0
    for _, row in demand_df.iterrows():
        iugu_code = str(row['IUGU CODE'])
        period = int(row['TIME PERIOD'])
        demand_qty = float(row['DEMAND'])
        if period in time_periods and iugu_code in plant_ids:
            demand[(iugu_code, str(period))] += demand_qty
    
    # Min fulfillment: (IUGU_CODE, TIME_PERIOD) -> MIN FULFILLMENT %
    min_fulfillment = {}
    for _, row in demand_df.iterrows():
        iugu_code = str(row['IUGU CODE'])
        period = int(row['TIME PERIOD'])
        min_fulfill = row['MIN FULFILLMENT (%)']
        if pd.notna(min_fulfill) and period in time_periods:
            min_fulfillment[(iugu_code, str(period))] = float(min_fulfill) / 100.0  # Convert to decimal
    
    # Initial inventory from IUGUOpeningStock
    initial_inventory: Dict[str, float] = {}
    for _, row in opening_stock_df.iterrows():
        iugu_code = str(row['IUGU CODE'])
        opening_stock = float(row['OPENING STOCK'])
        if iugu_code in plant_ids:
            initial_inventory[iugu_code] = opening_stock
    
    # Add hub opening stock
    for _, row in hub_opening_df.iterrows():
        iu_code = str(row['IU'])
        iugu_code = str(row['IUGU'])
        opening_stock = float(row['Opening Stock'])
        if iugu_code in plant_ids:
            # Add to existing or set
            initial_inventory[iugu_code] = initial_inventory.get(iugu_code, 0.0) + opening_stock
    
    # Ensure every plant has an initial inventory (default 0.0)
    for pid in plant_ids:
        if pid not in initial_inventory:
            initial_inventory[pid] = 0.0
    
    # Closing stock constraints
    min_closing_stock = {}
    max_closing_stock = {}
    for _, row in closing_stock_df.iterrows():
        iugu_code = str(row['IUGU CODE'])
        period = int(row['TIME PERIOD'])
        min_close = row['MIN CLOSE STOCK']
        max_close = row['MAX CLOSE STOCK']
        if period in time_periods and iugu_code in plant_ids:
            if pd.notna(min_close):
                min_closing_stock[(iugu_code, str(period))] = float(min_close)
            if pd.notna(max_close):
                max_closing_stock[(iugu_code, str(period))] = float(max_close)
    
    # Storage capacity (use max closing stock or a default)
    storage_capacity = {}
    for pid in plant_ids:
        # Find max closing stock across all periods
        max_stock = 0.0
        for period in time_periods:
            key = (pid, str(period))
            if key in max_closing_stock:
                max_stock = max(max_stock, max_closing_stock[key])
        storage_capacity[pid] = max_stock if max_stock > 0 else initial_inventory.get(pid, 0.0) * 2
    
    # Safety stock and max inventory (derive from closing stock)
    safety_stock = {}
    max_inventory = {}
    holding_cost = {}
    for pid in plant_ids:
        # Safety stock = min closing stock for first period
        first_period = str(time_periods[0]) if time_periods else "1"
        safety_stock[pid] = min_closing_stock.get((pid, first_period), 0.0)
        
        # Max inventory = max closing stock
        max_inv = 0.0
        for period in time_periods:
            key = (pid, str(period))
            if key in max_closing_stock:
                max_inv = max(max_inv, max_closing_stock[key])
        max_inventory[pid] = max_inv if max_inv > 0 else storage_capacity[pid]
        
        holding_cost[pid] = 0.0  # Default
    
    # Transport routes from LogisticsIUGU
    routes = []
    transport_cost_per_trip = {}
    transport_capacity_per_trip = {}
    transport_sbq = {}
    route_enabled = {}
    
    for _, row in logistics_df.iterrows():
        from_iu = str(row['FROM IU CODE'])
        to_iugu = str(row['TO IUGU CODE'])
        transport_code = str(row['TRANSPORT CODE'])
        period = int(row['TIME PERIOD'])
        freight_cost = float(row['FREIGHT COST'])
        handling_cost = float(row['HANDLING COST'])
        qty_multiplier = float(row['QUANTITY MULTIPLIER'])
        
        if period in time_periods and from_iu in plant_ids and to_iugu in plant_ids:
            # Total cost = freight + handling
            total_cost = freight_cost + handling_cost
            
            # Capacity per trip: use QUANTITY MULTIPLIER from dataset
            # This represents how many units can be moved per trip / lane.
            capacity_per_trip = max(qty_multiplier, 0.0) if qty_multiplier is not None else 0.0
            
            # SBQ (minimum shipment quantity)
            sbq = 0.0  # Default
            
            route_key = (from_iu, to_iugu, transport_code)
            
            if route_key not in routes:
                routes.append(route_key)
            
            # Use period-specific or aggregate values
            transport_cost_per_trip[route_key] = total_cost
            transport_capacity_per_trip[route_key] = capacity_per_trip
            transport_sbq[route_key] = sbq
            route_enabled[route_key] = True
    
    # Transport constraints from IUGUConstraint
    transport_bounds = {}
    transport_code_limits = {}
    
    for _, row in constraints_df.iterrows():
        iu_code = str(row['IU CODE']) if pd.notna(row['IU CODE']) else None
        transport_code = str(row['TRANSPORT CODE']) if pd.notna(row['TRANSPORT CODE']) else None
        iugu_code = str(row['IUGU CODE']) if pd.notna(row['IUGU CODE']) else None
        period = int(row['TIME PERIOD'])
        bound_type = str(row['BOUND TYPEID'])  # L=Lower, E=Equal, U=Upper
        value_type = str(row['VALUE TYPEID'])  # C=Capacity, Q=Quantity
        value = float(row['Value'])
        
        if period in time_periods:
            if iu_code and transport_code:
                # Transport code level constraint
                key = (iu_code, transport_code, str(period))
                if key not in transport_code_limits:
                    transport_code_limits[key] = {'lower': None, 'upper': None}
                
                if bound_type == 'L':
                    transport_code_limits[key]['lower'] = value
                elif bound_type == 'U':
                    transport_code_limits[key]['upper'] = value
            
            if iu_code and transport_code and iugu_code:
                # Route-specific constraint
                constraint_key = (iu_code, transport_code, iugu_code, str(period))
                if constraint_key not in transport_bounds:
                    transport_bounds[constraint_key] = {}
                transport_bounds[constraint_key][bound_type] = value
    
    return ExcelOptimizationData(
        months=[str(tp) for tp in time_periods],
        plant_ids=plant_ids,
        plant_names=plant_names,
        plant_type=plant_type,
        clinker_plants=clinker_plants,
        storage_capacity=storage_capacity,
        initial_inventory=initial_inventory,
        safety_stock=safety_stock,
        max_inventory=max_inventory,
        holding_cost=holding_cost,
        production_capacity=production_capacity,
        production_cost=production_cost,
        demand=demand,
        routes=routes,
        transport_cost_per_trip=transport_cost_per_trip,
        transport_capacity_per_trip=transport_capacity_per_trip,
        transport_sbq=transport_sbq,
        route_enabled=route_enabled,
        iugu_to_plant_id=iugu_to_plant_id,
        plant_id_to_iugu=plant_id_to_iugu,
        transport_bounds=transport_bounds,
        min_fulfillment=min_fulfillment,
        min_closing_stock=min_closing_stock,
        max_closing_stock=max_closing_stock,
        transport_code_limits=transport_code_limits,
    )
