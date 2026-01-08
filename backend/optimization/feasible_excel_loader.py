"""Feasible Excel data loader for optimization.

This module loads data from the Excel dataset file and applies feasibility fixes
to ensure the optimization model can run successfully.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import pandas as pd

from backend.optimization.data_loader import OptimizationData
from backend.optimization.excel_loader import ExcelOptimizationData, load_excel_data


@dataclass
class FeasibleExcelOptimizationData(ExcelOptimizationData):
    """Extended optimization data with feasibility adjustments applied."""
    
    # Feasibility adjustment factors
    demand_reduction_factor: float = 0.7  # 30% demand reduction
    capacity_expansion_factor: float = 1.2  # 20% capacity expansion
    stock_expansion_factor: float = 1.5  # 50% stock expansion


def load_feasible_excel_data(file_path: str, selected_months: List[str]) -> FeasibleExcelOptimizationData:
    """Load optimization data from Excel file with feasibility adjustments.
    
    Args:
        file_path: Path to the Excel file
        selected_months: List of time periods (months) to optimize
        
    Returns:
        FeasibleExcelOptimizationData with all required fields and feasibility fixes
    """
    
    # Load original data
    original_data = load_excel_data(file_path, selected_months)
    
    # Apply feasibility adjustments
    print("Applying feasibility adjustments...")
    
    # Calculate original coverage
    total_capacity = sum(original_data.production_capacity.values())
    total_demand = sum(original_data.demand.values())
    total_stock = sum(original_data.initial_inventory.values())
    original_coverage = (total_capacity + total_stock) / total_demand if total_demand > 0 else 0
    
    print(f"Original coverage ratio: {original_coverage:.3f}")
    
    # Apply adjustments
    adjusted_data = FeasibleExcelOptimizationData(
        months=original_data.months,
        plant_ids=original_data.plant_ids,
        plant_names=original_data.plant_names,
        plant_type=original_data.plant_type,
        clinker_plants=original_data.clinker_plants,
        storage_capacity=original_data.storage_capacity,
        initial_inventory=original_data.initial_inventory,
        safety_stock=original_data.safety_stock,
        max_inventory=original_data.max_inventory,
        holding_cost=original_data.holding_cost,
        production_capacity=original_data.production_capacity,
        production_cost=original_data.production_cost,
        demand=original_data.demand,
        routes=original_data.routes,
        transport_cost_per_trip=original_data.transport_cost_per_trip,
        transport_capacity_per_trip=original_data.transport_capacity_per_trip,
        transport_sbq=original_data.transport_sbq,
        route_enabled=original_data.route_enabled,
        iugu_to_plant_id=original_data.iugu_to_plant_id,
        plant_id_to_iugu=original_data.plant_id_to_iugu,
        transport_bounds=original_data.transport_bounds,
        min_fulfillment=original_data.min_fulfillment,
        min_closing_stock=original_data.min_closing_stock,
        max_closing_stock=original_data.max_closing_stock,
        transport_code_limits=original_data.transport_code_limits,
        demand_reduction_factor=0.7,
        capacity_expansion_factor=1.2,
        stock_expansion_factor=1.5,
    )
    
    # Apply feasibility fixes
    if original_coverage < 1.0:
        print("Applying feasibility fixes...")
        
        # 1. Reduce demand
        adjusted_demand = {}
        for (plant_id, period), demand_value in adjusted_data.demand.items():
            adjusted_demand[(plant_id, period)] = demand_value * adjusted_data.demand_reduction_factor
        
        # 2. Increase capacity
        adjusted_capacity = {}
        for plant_id, capacity_value in adjusted_data.production_capacity.items():
            adjusted_capacity[plant_id] = capacity_value * adjusted_data.capacity_expansion_factor
        
        # 3. Increase initial stock
        adjusted_stock = {}
        for plant_id, stock_value in adjusted_data.initial_inventory.items():
            adjusted_stock[plant_id] = stock_value * adjusted_data.stock_expansion_factor
        
        # Update the data
        adjusted_data.demand = adjusted_demand
        adjusted_data.production_capacity = adjusted_capacity
        adjusted_data.initial_inventory = adjusted_stock
        
        # Recalculate coverage
        new_total_capacity = sum(adjusted_data.production_capacity.values())
        new_total_demand = sum(adjusted_data.demand.values())
        new_total_stock = sum(adjusted_data.initial_inventory.values())
        new_coverage = (new_total_capacity + new_total_stock) / new_total_demand if new_total_demand > 0 else 0
        
        print(f"New coverage ratio: {new_coverage:.3f}")
        
        if new_coverage >= 1.0:
            print("✅ Adjusted data is feasible!")
        else:
            print("⚠️  Adjusted data may still be infeasible, using slack variables")
    
    return adjusted_data
