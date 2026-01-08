# Clinker Supply Chain Optimization Project

## Overview
This project implements optimization models for a multi-period clinker production and distribution supply chain problem using Gurobi and Pyomo frameworks.

## Problem Description
The optimization problem involves:
- **20 production facilities** (IU codes) with capacity constraints
- **44 demand points** (IUGU codes) with demand requirements  
- **3 time periods** for planning horizon
- **Transportation logistics** with associated costs
- **Inventory management** with opening and closing stock constraints
- **Objective**: Minimize total costs (production + transportation + inventory holding)

## Data Structure
The Excel file `Dataset_Dummy_Clinker_3MPlan.xlsx` contains 9 sheets:

1. **ClinkerDemand** (132 rows): Demand requirements by IUGU and time period
2. **ClinkerCapacity** (60 rows): Production capacity by IU and time period
3. **ProductionCost** (60 rows): Production costs by IU and time period
4. **LogisticsIUGU** (348 rows): Transportation costs and routes
5. **IUGUConstraint** (75 rows): Additional business constraints
6. **IUGUOpeningStock** (44 rows): Initial inventory levels
7. **HubOpeningStock** (3 rows): Hub-specific opening stocks
8. **IUGUClosingStock** (132 rows): Minimum/maximum closing stock requirements
9. **IUGUType** (46 rows): Plant type classifications

### Key Data Summary
- **Total Demand**: 22,662,135 units across all periods
- **Total Capacity**: 13,846,272 units (61% of demand)
- **Opening Stock**: 1,334,619 units
- **Transport Routes**: 348 possible routes
- **Cost Ranges**:
  - Production: 1,410 - 2,275 per unit
  - Freight: 0 - 3,628 per shipment
  - Handling: 0 - 440 per shipment

## Model Formulation

### Decision Variables
- `x[i,t]`: Production quantity at IU i in period t
- `y[i,j,t]`: Shipment quantity from IU i to IUGU j in period t  
- `s[j,t]`: Inventory at IUGU j at end of period t

### Objective Function
```
Minimize: Σ(production_cost[i,t] * x[i,t]) + Σ(transport_cost[i,j,t] * y[i,j,t]) + Σ(holding_cost * s[j,t])
```

### Constraints
1. **Production Capacity**: `x[i,t] ≤ capacity[i,t]`
2. **Demand Fulfillment**: `opening_stock[j] + Σ(y[i,j,t]) ≥ demand[j,t]`
3. **Flow Balance**: `s[j,t] = s[j,t-1] + Σ(y[i,j,t]) - demand[j,t]`
4. **Inventory Limits**: `min_stock[j,t] ≤ s[j,t] ≤ max_stock[j,t]`
5. **Transport Capacity**: `Σ(y[i,j,t]) ≤ x[i,t]`

## Implementation Files

### 1. `optimization_formulation.py`
- Data loading and processing class
- Creates structured data dictionaries for optimization
- Handles Excel file reading and data validation

### 2. `gurobi_model.py`
- Complete Gurobi implementation
- Full-scale model with all constraints
- Commercial solver required (license needed)
- Features:
  - 60 production variables
  - 348 transport variables  
  - 132 inventory variables
  - Advanced constraint handling

### 3. `pyomo_model.py`
- Complete Pyomo implementation
- Open-source alternative to Gurobi
- Requires external solver installation (GLPK/CBC)
- Algebraic modeling approach

### 4. `pulp_model.py`
- Simplified demonstration model
- Uses PuLP library with built-in CBC solver
- Reduced problem size for testing:
  - First period only
  - 10 production facilities
  - 10 demand points
- Good for validation and learning

### 5. `analyze_data.py`
- Data analysis and exploration script
- Provides insights into problem structure
- Generates summary statistics

## Installation Requirements

### Core Dependencies
```bash
pip install pandas openpyxl
```

### For Gurobi Model
```bash
pip install gurobipy
# Requires Gurobi license installation
```

### For Pyomo Model
```bash
pip install pyomo
# Install external solver:
# - GLPK: conda install -c conda-forge glpk
# - CBC: conda install -c conda-forge coincbc
```

### For PuLP Model (Recommended for Testing)
```bash
pip install pulp
# Includes built-in CBC solver
```

## Usage Examples

### Running the Simplified PuLP Model
```python
from pulp_model import ClinkerPulpModel

# Create and solve model
model = ClinkerPulpModel('Dataset_Dummy_Clinker_3MPlan.xlsx')
model.build_simplified_model()
status = model.solve()

if status == 'Optimal':
    model.save_results('results.xlsx')
```

### Running the Full Pyomo Model
```python
from pyomo_model import ClinkerPyomoModel

# Create and solve model
model = ClinkerPyomoModel('Dataset_Dummy_Clinker_3MPlan.xlsx')
model.build_model()
status = model.solve(solver_name='cbc')  # or 'glpk'

if status == 'ok':
    model.save_results('pyomo_results.xlsx')
```

### Running the Gurobi Model
```python
from gurobi_model import ClinkerGurobiModel

# Create and solve model
model = ClinkerGurobiModel('Dataset_Dummy_Clinker_3MPlan.xlsx')
model.build_model()
status = model.solve()

if status == GRB.OPTIMAL:
    model.save_results('gurobi_results.xlsx')
```

## Key Insights and Challenges

### 1. Capacity-Demand Gap
- Total production capacity (13.8M) is significantly less than total demand (22.7M)
- This creates feasibility challenges that require:
  - Strategic use of opening stocks
  - Potential demand relaxation
  - Multi-period inventory optimization

### 2. Model Complexity
- Large-scale MILP with 540+ variables
- Complex multi-period constraints
- Network flow optimization structure

### 3. Data Quality Issues
- Missing values in some constraint fields
- Inconsistent data formats across sheets
- Requires careful data preprocessing

## Results Interpretation

### Output Files
All models generate Excel results with:
- **Production Sheet**: Optimal production quantities by facility and period
- **Transport Sheet**: Optimal shipment quantities and routes
- **Inventory Sheet**: Inventory levels by location and period
- **Summary Sheet**: Key metrics and total costs

### Key Performance Indicators
- Total cost optimization
- Capacity utilization rates
- Demand fulfillment percentages
- Inventory turnover metrics
- Transportation efficiency

## Future Enhancements

1. **Stochastic Optimization**: Handle demand uncertainty
2. **Multi-objective Optimization**: Balance cost vs service level
3. **Scenario Analysis**: What-if analysis for different parameters
4. **Real-time Integration**: Connect to live data systems
5. **Advanced Visualization**: Interactive dashboards for results
6. **Machine Learning**: Demand forecasting integration

## Troubleshooting

### Common Issues
1. **Infeasible Solutions**: Check capacity vs demand balance
2. **Solver Not Found**: Install external solvers for Pyomo
3. **Memory Issues**: Reduce problem size for testing
4. **License Issues**: Gurobi requires commercial license

### Performance Tips
1. Use simplified models for initial testing
2. Implement warm starts for large problems
3. Consider decomposition techniques for very large instances
4. Use appropriate solver parameters for time limits

## Conclusion

This project provides a comprehensive framework for clinker supply chain optimization with multiple implementation options suitable for different use cases:

- **PuLP Model**: Quick testing and validation
- **Pyomo Model**: Open-source production deployment  
- **Gurobi Model**: High-performance commercial solution

The modular design allows for easy extension and customization based on specific business requirements.
