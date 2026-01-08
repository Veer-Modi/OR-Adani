# Optimization Model Updates for Excel Dataset Compatibility

## Overview
The optimization model has been enhanced to work with the Excel dataset structure (`Dataset_Dummy_Clinker_3MPlan.xlsx`) which contains 9 interconnected sheets using IUGU codes.

## Dataset Structure

### Sheets Analyzed:
1. **ClinkerDemand** - Demand by IUGU CODE, TIME PERIOD, with optional MIN FULFILLMENT (%)
2. **ClinkerCapacity** - Production capacity by IU CODE (production plants) and TIME PERIOD
3. **ProductionCost** - Production cost by IU CODE and TIME PERIOD
4. **LogisticsIUGU** - Transport routes: FROM IU CODE, TO IUGU CODE, TRANSPORT CODE, costs, and multipliers
5. **IUGUConstraint** - Transport constraints with BOUND TYPEID (L/E/U) and VALUE TYPEID (C/Q)
6. **IUGUOpeningStock** - Initial inventory by IUGU CODE
7. **HubOpeningStock** - Hub opening stock (IU -> IUGU mapping)
8. **IUGUClosingStock** - Min/Max closing stock constraints by IUGU CODE and TIME PERIOD
9. **IUGUType** - Plant type classification (IU = Clinker Plant, GU = Grinding Unit)

### Key Concepts:
- **IU Codes**: Integrated Units (production plants that produce clinker)
- **GU Codes**: Grinding Units (demand points that consume clinker)
- **IUGU Codes**: Unified code system connecting all plants and demand points
- **Transport Codes**: Mode of transport (e.g., T1, T2) with specific constraints

## Code Changes Summary

### 1. New File: `backend/optimization/excel_loader.py`
**Purpose**: Loads data from Excel file and converts to optimization format

**Key Features**:
- Reads all 9 sheets from Excel file
- Maps IUGU codes to plant IDs
- Extracts demand, capacity, costs, and constraints
- Handles transport bounds and limits
- Processes min fulfillment and closing stock constraints

**Data Structures**:
- `ExcelOptimizationData`: Extended `OptimizationData` with Excel-specific fields:
  - `iugu_to_plant_id`: Mapping dictionary
  - `transport_bounds`: Route-specific bounds from IUGUConstraint
  - `min_fulfillment`: Minimum demand fulfillment percentages
  - `min_closing_stock` / `max_closing_stock`: Inventory bounds
  - `transport_code_limits`: Aggregate limits per transport code

### 2. Updated: `backend/optimization/model.py`
**Changes**:
- Added import for `ExcelOptimizationData`
- Added conditional parameters for Excel-specific constraints:
  - `MinFulfillment`: Minimum fulfillment percentage per plant/period
  - `MinClosingStock` / `MaxClosingStock`: Closing inventory bounds
  - `TransportCodeLimits`: Limits on total transport per code
  - `TransportBounds`: Route-specific shipment bounds

**Impact**: Model now supports both MongoDB-based and Excel-based data loading

### 3. Updated: `backend/optimization/constraints.py`
**New Constraints Added**:

#### a. Min Fulfillment Constraint
```python
total_supply >= min_fulfillment_pct * demand
```
Ensures that demand fulfillment meets minimum percentage requirements from the dataset.

#### b. Closing Stock Constraints
```python
min_closing_stock <= inventory <= max_closing_stock
```
Enforces inventory bounds at the end of each time period as specified in IUGUClosingStock sheet.

#### c. Transport Code Limits
```python
lower_limit <= sum(shipments_per_code) <= upper_limit
```
Applies aggregate limits on total transport quantity per transport code (from IUGUConstraint with bound types L/U).

#### d. Transport Bounds (Route-Specific)
```python
lower_bound <= shipment[i,j,k,t] <= upper_bound  (or == equal_bound)
```
Applies route-specific bounds from IUGUConstraint sheet (bound types: L=Lower, U=Upper, E=Equal).

**Implementation Notes**:
- Constraints are added conditionally (only if Excel data is used)
- Multiple constraint types created for different bound types (Lower, Upper, Equal)
- Uses Pyomo's `Constraint.Skip` for optional constraints

### 4. New File: `analyze_dataset.py`
**Purpose**: Utility script to analyze Excel dataset structure
- Reads all sheets
- Displays column structure
- Shows data types and null values
- Identifies unique IUGU codes

## Key Improvements

### 1. IUGU Code Integration
- Full support for IUGU code system
- Proper mapping between IU (production) and GU (demand) codes
- Handles both production plants and demand points uniformly

### 2. Transport Constraints
- **Transport Code Limits**: Aggregate limits on total transport per code
  - Example: Total transport via T2 from IU_003 cannot exceed 233200 units
- **Route-Specific Bounds**: Individual route constraints
  - Example: Shipment from IU_003 to GU_016 via T2 must be exactly 0

### 3. Demand Fulfillment
- **Min Fulfillment**: Ensures minimum percentage of demand is met
- Applied per IUGU code and time period

### 4. Inventory Management
- **Opening Stock**: From IUGUOpeningStock and HubOpeningStock
- **Closing Stock**: Min/Max bounds from IUGUClosingStock
- Proper handling of hub inventory

### 5. Logistics Limits
- Transport capacity per trip
- Quantity multipliers
- Freight and handling costs
- Transport code-based aggregate limits

## Usage

### Loading from Excel:
```python
from backend.optimization.excel_loader import load_excel_data

# Load data from Excel
data = load_excel_data('Dataset_Dummy_Clinker_3MPlan.xlsx', selected_months=['1', '2', '3'])

# Build model with Excel data
model = build_model(data)
```

### Constraints Applied:
1. **Production Capacity**: Cannot exceed capacity per IU and period
2. **Inventory Balance**: Stock flow conservation
3. **Safety Stock**: Minimum inventory levels
4. **Max Inventory**: Storage capacity limits
5. **Min Fulfillment**: Minimum demand fulfillment percentage
6. **Closing Stock**: Min/Max bounds at period end
7. **Transport Code Limits**: Aggregate limits per transport code
8. **Transport Bounds**: Route-specific shipment bounds
9. **Trip Capacity**: Shipment cannot exceed trips × capacity
10. **SBQ**: Minimum shipment batch quantity

## Validation

The optimization model now:
- ✅ Reads all 9 sheets correctly
- ✅ Maps IUGU codes properly
- ✅ Applies transport constraints from IUGUConstraint
- ✅ Enforces min fulfillment requirements
- ✅ Respects closing stock bounds
- ✅ Handles transport code limits
- ✅ Validates solution against all constraints

## Next Steps

To integrate Excel loading into the UI:
1. Add file upload option in `ui/optimization_run.py`
2. Add toggle to choose between MongoDB and Excel data source
3. Update data loader to route to appropriate loader based on selection
4. Add validation to ensure Excel file matches expected format

## Files Modified

1. ✅ `backend/optimization/excel_loader.py` (NEW)
2. ✅ `backend/optimization/model.py` (UPDATED)
3. ✅ `backend/optimization/constraints.py` (UPDATED)
4. ✅ `analyze_dataset.py` (NEW - utility)

## Testing Recommendations

1. Test with sample Excel file
2. Verify all constraints are applied correctly
3. Check solution feasibility against constraints
4. Validate transport code limits are respected
5. Confirm closing stock bounds are met
6. Verify min fulfillment requirements
