"""
PLANT COMPARISON TEST CASES A-Z

Comprehensive test suite for comparing plants A-Z with different scenarios,
performance metrics, and optimization results.
"""

import pandas as pd
import numpy as np
from optimization_formulation import ClinkerOptimizationData
import time
import random
from datetime import datetime

class PlantComparisonTestSuite:
    def __init__(self, data_file):
        self.data = ClinkerOptimizationData(data_file)
        self.test_results = {}
        
    def generate_plant_a_to_z(self):
        """Generate test plants A-Z with different characteristics"""
        print("GENERATING TEST PLANTS A-Z")
        print("=" * 60)
        
        plants = {}
        
        # Define plant characteristics
        plant_types = {
            'A': {'capacity_mult': 1.5, 'cost_mult': 0.8, 'routes': 25, 'efficiency': 'high'},
            'B': {'capacity_mult': 1.2, 'cost_mult': 0.9, 'routes': 20, 'efficiency': 'high'},
            'C': {'capacity_mult': 1.0, 'cost_mult': 1.0, 'routes': 15, 'efficiency': 'medium'},
            'D': {'capacity_mult': 0.8, 'cost_mult': 1.1, 'routes': 12, 'efficiency': 'medium'},
            'E': {'capacity_mult': 1.8, 'cost_mult': 0.7, 'routes': 30, 'efficiency': 'very_high'},
            'F': {'capacity_mult': 0.6, 'cost_mult': 1.3, 'routes': 8, 'efficiency': 'low'},
            'G': {'capacity_mult': 1.3, 'cost_mult': 0.85, 'routes': 22, 'efficiency': 'high'},
            'H': {'capacity_mult': 0.9, 'cost_mult': 1.05, 'routes': 14, 'efficiency': 'medium'},
            'I': {'capacity_mult': 1.6, 'cost_mult': 0.75, 'routes': 28, 'efficiency': 'very_high'},
            'J': {'capacity_mult': 0.7, 'cost_mult': 1.25, 'routes': 10, 'efficiency': 'low'},
            'K': {'capacity_mult': 1.4, 'cost_mult': 0.82, 'routes': 24, 'efficiency': 'high'},
            'L': {'capacity_mult': 0.5, 'cost_mult': 1.4, 'routes': 6, 'efficiency': 'very_low'},
            'M': {'capacity_mult': 1.1, 'cost_mult': 0.95, 'routes': 18, 'efficiency': 'medium'},
            'N': {'capacity_mult': 0.85, 'cost_mult': 1.15, 'routes': 13, 'efficiency': 'medium'},
            'O': {'capacity_mult': 1.7, 'cost_mult': 0.72, 'routes': 26, 'efficiency': 'very_high'},
            'P': {'capacity_mult': 0.75, 'cost_mult': 1.2, 'routes': 11, 'efficiency': 'low'},
            'Q': {'capacity_mult': 1.25, 'cost_mult': 0.88, 'routes': 21, 'efficiency': 'high'},
            'R': {'capacity_mult': 0.65, 'cost_mult': 1.35, 'routes': 9, 'efficiency': 'low'},
            'S': {'capacity_mult': 1.35, 'cost_mult': 0.78, 'routes': 23, 'efficiency': 'high'},
            'T': {'capacity_mult': 0.95, 'cost_mult': 1.02, 'routes': 16, 'efficiency': 'medium'},
            'U': {'capacity_mult': 1.45, 'cost_mult': 0.76, 'routes': 25, 'efficiency': 'very_high'},
            'V': {'capacity_mult': 0.55, 'cost_mult': 1.38, 'routes': 7, 'efficiency': 'very_low'},
            'W': {'capacity_mult': 1.15, 'cost_mult': 0.92, 'routes': 19, 'efficiency': 'medium'},
            'X': {'capacity_mult': 0.8, 'cost_mult': 1.12, 'routes': 12, 'efficiency': 'medium'},
            'Y': {'capacity_mult': 1.55, 'cost_mult': 0.73, 'routes': 27, 'efficiency': 'very_high'},
            'Z': {'capacity_mult': 0.45, 'cost_mult': 1.45, 'routes': 5, 'efficiency': 'very_low'}
        }
        
        # Generate plant data
        base_capacity = 500000  # Base capacity
        base_cost = 1800  # Base production cost
        
        for plant_id, characteristics in plant_types.items():
            plants[plant_id] = {
                'plant_id': f'TEST_{plant_id}',
                'capacity': base_capacity * characteristics['capacity_mult'],
                'cost_per_unit': base_cost * characteristics['cost_mult'],
                'num_routes': characteristics['routes'],
                'efficiency': characteristics['efficiency'],
                'capacity_multiplier': characteristics['capacity_mult'],
                'cost_multiplier': characteristics['cost_mult']
            }
        
        # Display plant summary
        print(f"Generated {len(plants)} test plants (A-Z)")
        print("\nPlant Summary:")
        print("Plant | Capacity | Cost/Unit | Routes | Efficiency")
        print("-" * 55)
        
        for plant_id in sorted(plants.keys()):
            plant = plants[plant_id]
            print(f"{plant_id:5s} | {plant['capacity']:8.0f} | {plant['cost_per_unit']:8.0f} | "
                  f"{plant['num_routes']:6d} | {plant['efficiency']:10s}")
        
        return plants
    
    def create_test_scenarios(self):
        """Create different test scenarios for comparison"""
        print("\nCREATING TEST SCENARIOS")
        print("=" * 60)
        
        scenarios = {
            'baseline': {
                'name': 'Baseline Scenario',
                'demand_mult': 1.0,
                'cost_focus': 'balanced',
                'description': 'Current demand and cost structure'
            },
            'high_demand': {
                'name': 'High Demand Scenario',
                'demand_mult': 1.3,
                'cost_focus': 'balanced',
                'description': '30% increase in demand'
            },
            'low_demand': {
                'name': 'Low Demand Scenario',
                'demand_mult': 0.7,
                'cost_focus': 'balanced',
                'description': '30% decrease in demand'
            },
            'cost_focused': {
                'name': 'Cost Optimization Scenario',
                'demand_mult': 1.0,
                'cost_focus': 'cost',
                'description': 'Focus on minimizing production costs'
            },
            'capacity_focused': {
                'name': 'Capacity Utilization Scenario',
                'demand_mult': 1.0,
                'cost_focus': 'capacity',
                'description': 'Focus on maximizing capacity utilization'
            },
            'transport_focused': {
                'name': 'Transport Optimization Scenario',
                'demand_mult': 1.0,
                'cost_focus': 'transport',
                'description': 'Focus on minimizing transportation costs'
            }
        }
        
        print(f"Created {len(scenarios)} test scenarios:")
        for scenario_id, scenario in scenarios.items():
            print(f"  {scenario_id:15s}: {scenario['name']}")
            print(f"                    {scenario['description']}")
        
        return scenarios
    
    def run_plant_comparison(self, plants, scenarios):
        """Run comparison tests for all plants and scenarios"""
        print("\nRUNNING PLANT COMPARISON TESTS")
        print("=" * 60)
        
        results = {}
        
        for scenario_id, scenario in scenarios.items():
            print(f"\nTesting Scenario: {scenario['name']}")
            print("-" * 40)
            
            scenario_results = {}
            
            for plant_id, plant in plants.items():
                # Simulate plant performance
                performance = self.simulate_plant_performance(plant, scenario)
                scenario_results[plant_id] = performance
                
                # Print key metrics
                print(f"{plant_id}: Cost=${performance['total_cost']:,.0f}, "
                      f"Util={performance['capacity_util']*100:.1f}%, "
                      f"Score={performance['overall_score']:.2f}")
            
            results[scenario_id] = scenario_results
            
            # Rank plants for this scenario
            ranked = sorted(scenario_results.items(), 
                          key=lambda x: x[1]['overall_score'], 
                          reverse=True)
            
            print(f"\nTop 5 Plants for {scenario['name']}:")
            for i, (plant_id, perf) in enumerate(ranked[:5], 1):
                print(f"  {i}. {plant_id} - Score: {perf['overall_score']:.2f}")
        
        return results
    
    def simulate_plant_performance(self, plant, scenario):
        """Simulate individual plant performance"""
        # Base calculations
        demand_mult = scenario['demand_mult']
        cost_focus = scenario['cost_focus']
        
        # Calculate effective demand for this plant
        base_demand = 400000  # Base demand per plant
        effective_demand = base_demand * demand_mult * plant['capacity_multiplier']
        
        # Calculate production
        production = min(plant['capacity'], effective_demand)
        capacity_util = production / plant['capacity']
        
        # Calculate costs
        production_cost = production * plant['cost_per_unit']
        
        # Simulate transportation costs (based on number of routes)
        avg_transport_cost_per_unit = 1200  # Average transport cost
        transport_cost = production * avg_transport_cost_per_unit * (1 / plant['num_routes']) * 15
        
        # Calculate inventory holding cost
        avg_inventory = production * 0.1  # 10% average inventory
        holding_cost = avg_inventory * plant['cost_per_unit'] * 0.05  # 5% holding rate
        
        # Total cost
        total_cost = production_cost + transport_cost + holding_cost
        
        # Calculate revenue (assuming selling price)
        selling_price = 2500  # $ per unit
        revenue = production * selling_price
        
        # Calculate profit
        profit = revenue - total_cost
        
        # Calculate efficiency score
        efficiency_score = self.calculate_efficiency_score(plant, capacity_util, cost_focus)
        
        # Calculate cost efficiency
        cost_per_unit_actual = total_cost / production if production > 0 else float('inf')
        cost_efficiency = 2500 / cost_per_unit_actual if cost_per_unit_actual > 0 else 0
        
        # Overall score (weighted combination)
        if cost_focus == 'cost':
            overall_score = (efficiency_score * 0.3 + 
                          cost_efficiency * 0.5 + 
                          (1 - abs(capacity_util - 0.85)) * 0.2)
        elif cost_focus == 'capacity':
            overall_score = (efficiency_score * 0.3 + 
                          capacity_util * 0.5 + 
                          cost_efficiency * 0.2)
        elif cost_focus == 'transport':
            overall_score = (efficiency_score * 0.4 + 
                          (1 / (transport_cost / production + 1)) * 0.4 + 
                          capacity_util * 0.2)
        else:  # balanced
            overall_score = (efficiency_score * 0.35 + 
                          cost_efficiency * 0.35 + 
                          capacity_util * 0.3)
        
        return {
            'plant_id': plant['plant_id'],
            'production': production,
            'capacity_util': capacity_util,
            'production_cost': production_cost,
            'transport_cost': transport_cost,
            'holding_cost': holding_cost,
            'total_cost': total_cost,
            'revenue': revenue,
            'profit': profit,
            'efficiency_score': efficiency_score,
            'cost_efficiency': cost_efficiency,
            'overall_score': overall_score
        }
    
    def calculate_efficiency_score(self, plant, capacity_util, cost_focus):
        """Calculate efficiency score based on plant characteristics"""
        base_score = 0.5  # Base score
        
        # Efficiency rating bonus
        efficiency_bonuses = {
            'very_low': -0.2,
            'low': -0.1,
            'medium': 0.0,
            'high': 0.1,
            'very_high': 0.2
        }
        base_score += efficiency_bonuses.get(plant['efficiency'], 0)
        
        # Capacity utilization bonus
        if 0.7 <= capacity_util <= 0.9:
            base_score += 0.2  # Optimal range
        elif 0.5 <= capacity_util < 0.7:
            base_score += 0.1  # Good range
        elif capacity_util > 0.9:
            base_score += 0.05  # High utilization (stress)
        
        # Cost multiplier bonus
        if plant['cost_multiplier'] < 0.8:
            base_score += 0.15  # Very cost effective
        elif plant['cost_multiplier'] < 0.9:
            base_score += 0.1  # Cost effective
        elif plant['cost_multiplier'] > 1.2:
            base_score -= 0.1  # Expensive
        
        # Route diversity bonus
        if plant['num_routes'] >= 20:
            base_score += 0.1  # Well connected
        elif plant['num_routes'] >= 15:
            base_score += 0.05  # Good connectivity
        
        return max(0, min(1, base_score))  # Normalize to 0-1
    
    def generate_comparison_report(self, plants, scenarios, results):
        """Generate comprehensive comparison report"""
        print("\nGENERATING COMPARISON REPORT")
        print("=" * 60)
        
        # Create summary DataFrame
        summary_data = []
        
        for scenario_id, scenario_results in results.items():
            scenario_name = scenarios[scenario_id]['name']
            
            # Get top 5 plants for this scenario
            ranked = sorted(scenario_results.items(), 
                          key=lambda x: x[1]['overall_score'], 
                          reverse=True)
            
            for rank, (plant_id, performance) in enumerate(ranked[:5], 1):
                summary_data.append({
                    'Scenario': scenario_name,
                    'Rank': rank,
                    'Plant': plant_id,
                    'Overall Score': performance['overall_score'],
                    'Total Cost': performance['total_cost'],
                    'Profit': performance['profit'],
                    'Capacity Utilization': performance['capacity_util'],
                    'Cost Efficiency': performance['cost_efficiency'],
                    'Efficiency Score': performance['efficiency_score']
                })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Save to Excel
        with pd.ExcelWriter('plant_comparison_report.xlsx', engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Detailed results for each scenario
            for scenario_id, scenario_results in results.items():
                scenario_name = scenarios[scenario_id]['name']
                detailed_data = []
                
                for plant_id, performance in scenario_results.items():
                    detailed_data.append({
                        'Plant': plant_id,
                        'Production': performance['production'],
                        'Capacity Utilization': performance['capacity_util'],
                        'Production Cost': performance['production_cost'],
                        'Transport Cost': performance['transport_cost'],
                        'Holding Cost': performance['holding_cost'],
                        'Total Cost': performance['total_cost'],
                        'Revenue': performance['revenue'],
                        'Profit': performance['profit'],
                        'Overall Score': performance['overall_score']
                    })
                
                detailed_df = pd.DataFrame(detailed_data)
                detailed_df.to_excel(writer, sheet_name=scenario_name[:31], index=False)
            
            # Plant characteristics
            plant_data = []
            for plant_id, plant in plants.items():
                plant_data.append({
                    'Plant': plant_id,
                    'Plant ID': plant['plant_id'],
                    'Capacity': plant['capacity'],
                    'Cost per Unit': plant['cost_per_unit'],
                    'Number of Routes': plant['num_routes'],
                    'Efficiency': plant['efficiency'],
                    'Capacity Multiplier': plant['capacity_multiplier'],
                    'Cost Multiplier': plant['cost_multiplier']
                })
            
            plant_df = pd.DataFrame(plant_data)
            plant_df.to_excel(writer, sheet_name='Plant_Characteristics', index=False)
        
        print("✅ Comparison report saved to 'plant_comparison_report.xlsx'")
        
        # Print summary statistics
        print("\nSUMMARY STATISTICS")
        print("-" * 40)
        
        # Best overall performers
        all_scores = []
        for scenario_results in results.values():
            for performance in scenario_results.values():
                all_scores.append(performance['overall_score'])
        
        print(f"Average Overall Score: {np.mean(all_scores):.3f}")
        print(f"Best Overall Score: {max(all_scores):.3f}")
        print(f"Worst Overall Score: {min(all_scores):.3f}")
        
        # Most consistent performers
        plant_avg_scores = {}
        for plant_id in plants.keys():
            scores = []
            for scenario_results in results.values():
                if plant_id in scenario_results:
                    scores.append(scenario_results[plant_id]['overall_score'])
            if scores:
                plant_avg_scores[plant_id] = np.mean(scores)
        
        consistent = sorted(plant_avg_scores.items(), key=lambda x: x[1], reverse=True)
        print("\nMost Consistent Performers (Average Score):")
        for i, (plant_id, avg_score) in enumerate(consistent[:5], 1):
            print(f"  {i}. {plant_id}: {avg_score:.3f}")
        
        return summary_df
    
    def create_visualization_data(self, plants, results):
        """Create data for visualizations"""
        print("\nCREATING VISUALIZATION DATA")
        print("=" * 60)
        
        viz_data = {
            'plant_performance': [],
            'scenario_comparison': [],
            'efficiency_analysis': []
        }
        
        # Plant performance across scenarios
        for plant_id in plants.keys():
            plant_scores = []
            for scenario_results in results.values():
                if plant_id in scenario_results:
                    plant_scores.append(scenario_results[plant_id]['overall_score'])
            
            if plant_scores:
                viz_data['plant_performance'].append({
                    'Plant': plant_id,
                    'Average Score': np.mean(plant_scores),
                    'Max Score': max(plant_scores),
                    'Min Score': min(plant_scores),
                    'Score Range': max(plant_scores) - min(plant_scores),
                    'Consistency': 1 - (np.std(plant_scores) / np.mean(plant_scores) if np.mean(plant_scores) > 0 else 0)
                })
        
        # Scenario comparison
        for scenario_id, scenario_results in results.items():
            scores = [perf['overall_score'] for perf in scenario_results.values()]
            costs = [perf['total_cost'] for perf in scenario_results.values()]
            profits = [perf['profit'] for perf in scenario_results.values()]
            
            viz_data['scenario_comparison'].append({
                'Scenario': scenario_id,
                'Avg Score': np.mean(scores),
                'Avg Cost': np.mean(costs),
                'Avg Profit': np.mean(profits),
                'Best Score': max(scores),
                'Worst Score': min(scores)
            })
        
        # Efficiency analysis
        for plant_id, plant in plants.items():
            for scenario_id, scenario_results in results.items():
                if plant_id in scenario_results:
                    perf = scenario_results[plant_id]
                    viz_data['efficiency_analysis'].append({
                        'Plant': plant_id,
                        'Scenario': scenario_id,
                        'Efficiency Score': perf['efficiency_score'],
                        'Cost Efficiency': perf['cost_efficiency'],
                        'Capacity Utilization': perf['capacity_util'],
                        'Overall Score': perf['overall_score']
                    })
        
        # Save visualization data
        viz_df1 = pd.DataFrame(viz_data['plant_performance'])
        viz_df2 = pd.DataFrame(viz_data['scenario_comparison'])
        viz_df3 = pd.DataFrame(viz_data['efficiency_analysis'])
        
        with pd.ExcelWriter('plant_visualization_data.xlsx', engine='openpyxl') as writer:
            viz_df1.to_excel(writer, sheet_name='Plant_Performance', index=False)
            viz_df2.to_excel(writer, sheet_name='Scenario_Comparison', index=False)
            viz_df3.to_excel(writer, sheet_name='Efficiency_Analysis', index=False)
        
        print("✅ Visualization data saved to 'plant_visualization_data.xlsx'")
        
        return viz_data

def main():
    """Main function to run all plant comparison tests"""
    try:
        print("=" * 80)
        print("PLANT COMPARISON TEST SUITE A-Z")
        print("=" * 80)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data Source: Dataset_Dummy_Clinker_3MPlan.xlsx")
        
        # Initialize test suite
        test_suite = PlantComparisonTestSuite('Dataset_Dummy_Clinker_3MPlan.xlsx')
        
        # Generate test plants A-Z
        plants = test_suite.generate_plant_a_to_z()
        
        # Create test scenarios
        scenarios = test_suite.create_test_scenarios()
        
        # Run comparison tests
        results = test_suite.run_plant_comparison(plants, scenarios)
        
        # Generate comparison report
        summary_df = test_suite.generate_comparison_report(plants, scenarios, results)
        
        # Create visualization data
        viz_data = test_suite.create_visualization_data(plants, results)
        
        print("\n" + "=" * 80)
        print("PLANT COMPARISON TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        print("\nFiles Generated:")
        print("📊 plant_comparison_report.xlsx - Comprehensive comparison results")
        print("📈 plant_visualization_data.xlsx - Data for visualizations")
        
        print("\nKey Insights:")
        print("• 26 test plants (A-Z) with varying characteristics")
        print("• 6 different scenarios tested")
        print("• Performance scores calculated for each combination")
        print("• Rankings provided for each scenario")
        print("• Consistency analysis across scenarios")
        
        print("\nNext Steps:")
        print("1. Review plant_comparison_report.xlsx for detailed results")
        print("2. Use plant_visualization_data.xlsx for charts")
        print("3. Identify best-performing plant types")
        print("4. Apply insights to real plant optimization")
        
    except Exception as e:
        print(f"Error in plant comparison tests: {e}")

if __name__ == "__main__":
    main()
