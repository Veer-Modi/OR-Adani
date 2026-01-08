"""
CLINKER SUPPLY CHAIN OPTIMIZATION PROBLEM FORMULATION

PROBLEM DESCRIPTION:
Multi-period supply chain optimization for clinker production and distribution
across 3 time periods with 20 production facilities (IU) and 44 demand points (IUGU).

DECISION VARIABLES:
- x[i,t]: Production quantity at IU i in period t
- y[i,j,t]: Shipment quantity from IU i to IUGU j in period t
- s[j,t]: Inventory at IUGU j at end of period t

OBJECTIVE:
Minimize total cost = Production cost + Transportation cost + Inventory holding cost

CONSTRAINTS:
1. Production capacity constraints
2. Demand fulfillment constraints
3. Flow balance constraints
4. Inventory constraints
5. Transportation constraints
6. Additional business constraints
"""

import pandas as pd
import numpy as np

class ClinkerOptimizationData:
    def __init__(self, excel_file):
        self.excel_file = excel_file
        self.load_data()
        self.process_data()
        
    def load_data(self):
        """Load all data from Excel sheets"""
        self.demand = pd.read_excel(self.excel_file, sheet_name='ClinkerDemand')
        self.capacity = pd.read_excel(self.excel_file, sheet_name='ClinkerCapacity')
        self.prod_cost = pd.read_excel(self.excel_file, sheet_name='ProductionCost')
        self.logistics = pd.read_excel(self.excel_file, sheet_name='LogisticsIUGU')
        self.constraints = pd.read_excel(self.excel_file, sheet_name='IUGUConstraint')
        self.opening_stock = pd.read_excel(self.excel_file, sheet_name='IUGUOpeningStock')
        self.closing_stock = pd.read_excel(self.excel_file, sheet_name='IUGUClosingStock')
        self.iugu_type = pd.read_excel(self.excel_file, sheet_name='IUGUType')
        
    def process_data(self):
        """Process and organize data for optimization"""
        # Sets
        self.IU_codes = sorted(self.capacity['IU CODE'].unique())
        self.IUGU_codes = sorted(self.demand['IUGU CODE'].unique())
        self.periods = sorted(self.demand['TIME PERIOD'].unique())
        
        # Parameters
        self.demand_dict = self.create_demand_dict()
        self.capacity_dict = self.create_capacity_dict()
        self.prod_cost_dict = self.create_prod_cost_dict()
        self.transport_cost_dict = self.create_transport_cost_dict()
        self.opening_stock_dict = self.create_opening_stock_dict()
        self.closing_stock_dict = self.create_closing_stock_dict()
        
        # Transportation network
        self.transport_routes = self.create_transport_routes()
        
    def create_demand_dict(self):
        """Create demand dictionary: demand[iugu, period]"""
        demand_dict = {}
        for _, row in self.demand.iterrows():
            demand_dict[(row['IUGU CODE'], row['TIME PERIOD'])] = row['DEMAND']
        return demand_dict
    
    def create_capacity_dict(self):
        """Create capacity dictionary: capacity[iu, period]"""
        capacity_dict = {}
        for _, row in self.capacity.iterrows():
            capacity_dict[(row['IU CODE'], row['TIME PERIOD'])] = row['CAPACITY']
        return capacity_dict
    
    def create_prod_cost_dict(self):
        """Create production cost dictionary: prod_cost[iu, period]"""
        prod_cost_dict = {}
        for _, row in self.prod_cost.iterrows():
            prod_cost_dict[(row['IU CODE'], row['TIME PERIOD'])] = row['PRODUCTION COST']
        return prod_cost_dict
    
    def create_transport_cost_dict(self):
        """Create transport cost dictionary: transport_cost[iu, iugu, period]"""
        transport_cost_dict = {}
        for _, row in self.logistics.iterrows():
            total_cost = row['FREIGHT COST'] + row['HANDLING COST']
            transport_cost_dict[(row['FROM IU CODE'], row['TO IUGU CODE'], row['TIME PERIOD'])] = total_cost
        return transport_cost_dict
    
    def create_opening_stock_dict(self):
        """Create opening stock dictionary: opening_stock[iugu]"""
        opening_stock_dict = {}
        for _, row in self.opening_stock.iterrows():
            opening_stock_dict[row['IUGU CODE']] = row['OPENING STOCK']
        return opening_stock_dict
    
    def create_closing_stock_dict(self):
        """Create closing stock dictionary: closing_stock[iugu, period, type]"""
        closing_stock_dict = {}
        for _, row in self.closing_stock.iterrows():
            if not pd.isna(row['MIN CLOSE STOCK']):
                closing_stock_dict[(row['IUGU CODE'], row['TIME PERIOD'], 'min')] = row['MIN CLOSE STOCK']
            if not pd.isna(row['MAX CLOSE STOCK']):
                closing_stock_dict[(row['IUGU CODE'], row['TIME PERIOD'], 'max')] = row['MAX CLOSE STOCK']
        return closing_stock_dict
    
    def create_transport_routes(self):
        """Create list of valid transport routes"""
        routes = []
        for _, row in self.logistics.iterrows():
            routes.append((row['FROM IU CODE'], row['TO IUGU CODE'], row['TIME PERIOD']))
        return routes
    
    def print_summary(self):
        """Print data summary"""
        print("=== OPTIMIZATION DATA SUMMARY ===")
        print(f"Production facilities (IU): {len(self.IU_codes)}")
        print(f"Demand points (IUGU): {len(self.IUGU_codes)}")
        print(f"Time periods: {len(self.periods)}")
        print(f"Transport routes: {len(self.transport_routes)}")
        print(f"Total demand: {sum(self.demand_dict.values()):,.0f}")
        print(f"Total capacity: {sum(self.capacity_dict.values()):,.0f}")
        print(f"Total opening stock: {sum(self.opening_stock_dict.values()):,.0f}")

if __name__ == "__main__":
    # Test the data loading
    data = ClinkerOptimizationData('Dataset_Dummy_Clinker_3MPlan.xlsx')
    data.print_summary()
