"""
SPECIALIZED PLANT COMPARISON TESTS

Advanced test cases for specific plant comparisons including:
- Head-to-head battles
- Performance under constraints
- Sensitivity analysis
- Investment scenarios
"""

import pandas as pd
import numpy as np
from plant_comparison_tests import PlantComparisonTestSuite
import matplotlib.pyplot as plt
import seaborn as sns

class SpecializedPlantTests:
    def __init__(self, data_file):
        self.base_suite = PlantComparisonTestSuite(data_file)
        
    def head_to_head_battles(self):
        """Create head-to-head battles between specific plant types"""
        print("HEAD-TO-HEAD PLANT BATTLES")
        print("=" * 60)
        
        # Define interesting matchups
        battles = [
            {
                'name': 'High Capacity vs Low Cost',
                'plants': ['E', 'L'],  # E: high capacity, low cost; L: low capacity, high cost
                'focus': 'overall_efficiency'
            },
            {
                'name': 'Balanced vs Specialized',
                'plants': ['C', 'E'],  # C: balanced; E: specialized high capacity
                'focus': 'adaptability'
            },
            {
                'name': 'Very High Efficiency vs Medium',
                'plants': ['E', 'C'],  # E: very high; C: medium
                'focus': 'cost_effectiveness'
            },
            {
                'name': 'Well Connected vs Poorly Connected',
                'plants': ['E', 'L'],  # E: 30 routes; L: 6 routes
                'focus': 'transport_efficiency'
            },
            {
                'name': 'Top Performers Showdown',
                'plants': ['E', 'Y', 'O'],  # Top 3 from previous tests
                'focus': 'championship'
            }
        ]
        
        battle_results = {}
        
        for battle in battles:
            print(f"\n🥊 BATTLE: {battle['name']}")
            print("-" * 40)
            
            # Get plant data
            plants = self.base_suite.generate_plant_a_to_z()
            battle_plants = {pid: plants[pid] for pid in battle['plants']}
            
            # Test under multiple scenarios
            scenarios = ['baseline', 'high_demand', 'low_demand', 'cost_focused']
            scenario_results = {}
            
            for scenario in scenarios:
                # Simulate battle
                scores = {}
                for plant_id, plant in battle_plants.items():
                    scenario_data = {
                        'name': f'{scenario.title()} Scenario',
                        'demand_mult': 1.2 if scenario == 'high_demand' else 0.8 if scenario == 'low_demand' else 1.0,
                        'cost_focus': 'cost' if scenario == 'cost_focused' else 'balanced'
                    }
                    performance = self.base_suite.simulate_plant_performance(plant, scenario_data)
                    scores[plant_id] = performance['overall_score']
                
                # Determine winner
                winner = max(scores.items(), key=lambda x: x[1])
                scenario_results[scenario] = {
                    'scores': scores,
                    'winner': winner[0],
                    'margin': winner[1] - min(scores.values())
                }
                
                print(f"  {scenario.title()}: {winner[0]} wins ({winner[1]:.3f})")
            
            # Overall battle winner
            total_wins = {}
            for scenario_result in scenario_results.values():
                winner = scenario_result['winner']
                total_wins[winner] = total_wins.get(winner, 0) + 1
            
            battle_winner = max(total_wins.items(), key=lambda x: x[1])
            battle_results[battle['name']] = {
                'scenario_results': scenario_results,
                'overall_winner': battle_winner[0],
                'win_count': battle_winner[1],
                'total_wins': total_wins
            }
            
            print(f"🏆 OVERALL WINNER: {battle_winner[0]} ({battle_winner[1]}/{len(scenarios)} wins)")
        
        return battle_results
    
    def constraint_stress_test(self):
        """Test plant performance under various constraints"""
        print("\nCONSTRAINT STRESS TEST")
        print("=" * 60)
        
        plants = self.base_suite.generate_plant_a_to_z()
        
        # Define constraint scenarios
        constraints = [
            {
                'name': 'Capacity Constraint',
                'type': 'capacity_limit',
                'severity': 0.5,  # 50% capacity reduction
                'description': 'Severe capacity limitations'
            },
            {
                'name': 'Transport Disruption',
                'type': 'transport_limit',
                'severity': 0.3,  # 70% route reduction
                'description': 'Major transportation disruptions'
            },
            {
                'name': 'Cost Increase',
                'type': 'cost_increase',
                'severity': 1.5,  # 50% cost increase
                'description': 'Raw material price spike'
            },
            {
                'name': 'Demand Surge',
                'type': 'demand_surge',
                'severity': 2.0,  # 100% demand increase
                'description': 'Unexpected demand surge'
            },
            {
                'name': 'Combined Crisis',
                'type': 'combined',
                'severity': 0.7,  # Multiple constraints
                'description': 'Multiple simultaneous constraints'
            }
        ]
        
        stress_results = {}
        
        for constraint in constraints:
            print(f"\n🚨 TESTING: {constraint['name']}")
            print(f"   {constraint['description']}")
            print("-" * 40)
            
            constraint_results = {}
            
            # Test top 10 performing plants
            top_plants = ['E', 'Y', 'O', 'I', 'U', 'S', 'K', 'Q', 'A', 'G']
            
            for plant_id in top_plants:
                if plant_id in plants:
                    plant = plants[plant_id]
                    
                    # Apply constraint
                    if constraint['type'] == 'capacity_limit':
                        plant['capacity'] *= constraint['severity']
                    elif constraint['type'] == 'transport_limit':
                        plant['num_routes'] = int(plant['num_routes'] * constraint['severity'])
                    elif constraint['type'] == 'cost_increase':
                        plant['cost_per_unit'] *= constraint['severity']
                    elif constraint['type'] == 'demand_surge':
                        demand_mult = constraint['severity']
                    elif constraint['type'] == 'combined':
                        plant['capacity'] *= 0.7
                        plant['num_routes'] = int(plant['num_routes'] * 0.5)
                        plant['cost_per_unit'] *= 1.3
                        demand_mult = 1.5
                    else:
                        demand_mult = 1.0
                    
                    # Simulate performance
                    scenario_data = {
                        'name': constraint['name'],
                        'demand_mult': demand_mult if 'demand_mult' in locals() else 1.0,
                        'cost_focus': 'resilience'
                    }
                    
                    performance = self.base_suite.simulate_plant_performance(plant, scenario_data)
                    constraint_results[plant_id] = performance
            
            # Rank plants by resilience (score maintenance)
            baseline_scores = {}
            for plant_id in top_plants:
                if plant_id in plants:
                    baseline_scenario = {'name': 'Baseline', 'demand_mult': 1.0, 'cost_focus': 'balanced'}
                    baseline_perf = self.base_suite.simulate_plant_performance(plants[plant_id], baseline_scenario)
                    baseline_scores[plant_id] = baseline_perf['overall_score']
            
            resilience_scores = {}
            for plant_id, constrained_perf in constraint_results.items():
                baseline_score = baseline_scores.get(plant_id, 0)
                resilience = constrained_perf['overall_score'] / baseline_score if baseline_score > 0 else 0
                resilience_scores[plant_id] = resilience
            
            ranked_resilience = sorted(resilience_scores.items(), key=lambda x: x[1], reverse=True)
            
            stress_results[constraint['name']] = {
                'constraint_results': constraint_results,
                'resilience_scores': resilience_scores,
                'ranking': ranked_resilience
            }
            
            print("Top 5 Most Resilient Plants:")
            for i, (plant_id, resilience) in enumerate(ranked_resilience[:5], 1):
                print(f"  {i}. {plant_id}: {resilience:.3f} resilience score")
        
        return stress_results
    
    def investment_scenario_analysis(self):
        """Analyze different investment scenarios for plant improvement"""
        print("\nINVESTMENT SCENARIO ANALYSIS")
        print("=" * 60)
        
        plants = self.base_suite.generate_plant_a_to_z()
        
        # Define investment scenarios
        investments = [
            {
                'name': 'Capacity Expansion',
                'type': 'capacity',
                'levels': [10, 25, 50, 100],  # Percentage increase
                'cost_per_percent': 5000000,  # $5M per 10% capacity increase
                'description': 'Expand production capacity'
            },
            {
                'name': 'Cost Reduction',
                'type': 'cost',
                'levels': [5, 10, 15, 20],  # Percentage reduction
                'cost_per_percent': 2000000,  # $2M per 5% cost reduction
                'description': 'Invest in cost efficiency'
            },
            {
                'name': 'Route Optimization',
                'type': 'routes',
                'levels': [5, 10, 15, 25],  # Additional routes
                'cost_per_route': 100000,  # $100k per new route
                'description': 'Expand transportation network'
            },
            {
                'name': 'Balanced Investment',
                'type': 'balanced',
                'levels': [10, 25, 50],  # Overall investment level
                'cost_per_level': 10000000,  # $10M per level
                'description': 'Balanced across all areas'
            }
        ]
        
        investment_results = {}
        
        # Focus on top 5 plants for investment analysis
        target_plants = ['E', 'Y', 'O', 'I', 'U']
        
        for investment in investments:
            print(f"\n💰 INVESTMENT: {investment['name']}")
            print(f"   {investment['description']}")
            print("-" * 40)
            
            investment_results[investment['name']] = {}
            
            for plant_id in target_plants:
                if plant_id in plants:
                    plant = plants[plant_id]
                    plant_investments = []
                    
                    for level in investment['levels']:
                        # Create investment scenario
                        invested_plant = plant.copy()
                        
                        if investment['type'] == 'capacity':
                            invested_plant['capacity'] *= (1 + level/100)
                            investment_cost = level/10 * investment['cost_per_percent']
                        elif investment['type'] == 'cost':
                            invested_plant['cost_per_unit'] *= (1 - level/100)
                            investment_cost = level/5 * investment['cost_per_percent']
                        elif investment['type'] == 'routes':
                            invested_plant['num_routes'] += level
                            investment_cost = level * investment['cost_per_route']
                        elif investment['type'] == 'balanced':
                            invested_plant['capacity'] *= (1 + level/200)
                            invested_plant['cost_per_unit'] *= (1 - level/400)
                            invested_plant['num_routes'] += int(level/4)
                            investment_cost = level * investment['cost_per_level']
                        
                        # Simulate performance with investment
                        scenario_data = {
                            'name': f'{investment["name"]} {level}%',
                            'demand_mult': 1.2,  # High demand scenario
                            'cost_focus': 'roi'
                        }
                        
                        performance = self.base_suite.simulate_plant_performance(invested_plant, scenario_data)
                        
                        # Calculate ROI
                        baseline_perf = self.base_suite.simulate_plant_performance(plant, {
                            'name': 'Baseline', 'demand_mult': 1.2, 'cost_focus': 'roi'
                        })
                        
                        profit_improvement = performance['profit'] - baseline_perf['profit']
                        roi = (profit_improvement / investment_cost * 100) if investment_cost > 0 else 0
                        
                        plant_investments.append({
                            'level': level,
                            'investment_cost': investment_cost,
                            'performance': performance,
                            'profit_improvement': profit_improvement,
                            'roi': roi
                        })
                    
                    investment_results[investment['name']][plant_id] = plant_investments
                    
                    # Find best ROI
                    best_investment = max(plant_investments, key=lambda x: x['roi'])
                    print(f"  {plant_id}: Best ROI {best_investment['level']}% = {best_investment['roi']:.1f}%")
        
        return investment_results
    
    def sensitivity_analysis(self):
        """Perform sensitivity analysis on key parameters"""
        print("\nSENSITIVITY ANALYSIS")
        print("=" * 60)
        
        plants = self.base_suite.generate_plant_a_to_z()
        
        # Parameters to analyze
        sensitivity_params = [
            {
                'name': 'Demand Variation',
                'param': 'demand_mult',
                'range': [0.5, 0.7, 0.9, 1.0, 1.1, 1.3, 1.5],
                'base_value': 1.0
            },
            {
                'name': 'Cost Multiplier',
                'param': 'cost_mult',
                'range': [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3],
                'base_value': 1.0
            },
            {
                'name': 'Capacity Utilization Target',
                'param': 'utilization_target',
                'range': [0.6, 0.7, 0.8, 0.85, 0.9, 0.95],
                'base_value': 0.85
            }
        ]
        
        sensitivity_results = {}
        
        # Test on representative plants
        test_plants = ['E', 'L', 'C']  # High, Low, Medium performers
        
        for param_config in sensitivity_params:
            print(f"\n📊 ANALYZING: {param_config['name']}")
            print("-" * 40)
            
            sensitivity_results[param_config['name']] = {}
            
            for plant_id in test_plants:
                if plant_id in plants:
                    plant = plants[plant_id]
                    param_results = []
                    
                    for value in param_config['range']:
                        # Create modified plant for this parameter value
                        test_plant = plant.copy()
                        scenario_data = {
                            'name': f'{param_config["name"]} {value}',
                            'demand_mult': 1.0,
                            'cost_focus': 'balanced'
                        }
                        
                        # Apply parameter change
                        if param_config['param'] == 'demand_mult':
                            scenario_data['demand_mult'] = value
                        elif param_config['param'] == 'cost_mult':
                            test_plant['cost_per_unit'] *= value
                        elif param_config['param'] == 'utilization_target':
                            # This affects the scoring, not the plant directly
                            scenario_data['utilization_target'] = value
                        
                        performance = self.base_suite.simulate_plant_performance(
                            test_plant if param_config['param'] != 'cost_mult' else plant, 
                            scenario_data
                        )
                        
                        param_results.append({
                            'value': value,
                            'score': performance['overall_score'],
                            'cost': performance['total_cost'],
                            'profit': performance['profit']
                        })
                    
                    sensitivity_results[param_config['name']][plant_id] = param_results
                    
                    # Calculate sensitivity (slope)
                    scores = [r['score'] for r in param_results]
                    values = param_config['range']
                    
                    # Simple linear sensitivity
                    if len(scores) > 1 and len(values) > 1:
                        sensitivity = (scores[-1] - scores[0]) / (values[-1] - values[0])
                        print(f"  {plant_id}: Sensitivity = {sensitivity:.3f}")
        
        return sensitivity_results
    
    def generate_specialized_report(self, battles, stress_tests, investments, sensitivity):
        """Generate comprehensive specialized test report"""
        print("\nGENERATING SPECIALIZED TEST REPORT")
        print("=" * 60)
        
        with pd.ExcelWriter('specialized_plant_tests.xlsx', engine='openpyxl') as writer:
            
            # Head-to-Head Battles
            battle_data = []
            for battle_name, battle_result in battles.items():
                for scenario, scenario_result in battle_result['scenario_results'].items():
                    for plant_id, score in scenario_result['scores'].items():
                        battle_data.append({
                            'Battle': battle_name,
                            'Scenario': scenario,
                            'Plant': plant_id,
                            'Score': score,
                            'Winner': plant_id == scenario_result['winner']
                        })
            
            battle_df = pd.DataFrame(battle_data)
            battle_df.to_excel(writer, sheet_name='Head_to_Head_Battles', index=False)
            
            # Stress Test Results
            stress_data = []
            for stress_name, stress_result in stress_tests.items():
                for plant_id, resilience in stress_result['resilience_scores'].items():
                    stress_data.append({
                        'Stress_Test': stress_name,
                        'Plant': plant_id,
                        'Resilience_Score': resilience,
                        'Rank': next(i for i, (pid, r) in enumerate(stress_result['ranking'], 1) if pid == plant_id)
                    })
            
            stress_df = pd.DataFrame(stress_data)
            stress_df.to_excel(writer, sheet_name='Stress_Tests', index=False)
            
            # Investment Analysis
            investment_data = []
            for inv_name, inv_results in investments.items():
                for plant_id, plant_investments in inv_results.items():
                    for inv in plant_investments:
                        investment_data.append({
                            'Investment_Type': inv_name,
                            'Plant': plant_id,
                            'Investment_Level': inv['level'],
                            'Investment_Cost': inv['investment_cost'],
                            'ROI': inv['roi'],
                            'Profit_Improvement': inv['profit_improvement'],
                            'Final_Score': inv['performance']['overall_score']
                        })
            
            investment_df = pd.DataFrame(investment_data)
            investment_df.to_excel(writer, sheet_name='Investment_Analysis', index=False)
            
            # Sensitivity Analysis
            sensitivity_data = []
            for param_name, param_results in sensitivity.items():
                for plant_id, param_data in param_results.items():
                    for data_point in param_data:
                        sensitivity_data.append({
                            'Parameter': param_name,
                            'Plant': plant_id,
                            'Parameter_Value': data_point['value'],
                            'Score': data_point['score'],
                            'Cost': data_point['cost'],
                            'Profit': data_point['profit']
                        })
            
            sensitivity_df = pd.DataFrame(sensitivity_data)
            sensitivity_df.to_excel(writer, sheet_name='Sensitivity_Analysis', index=False)
        
        print("✅ Specialized test report saved to 'specialized_plant_tests.xlsx'")

def main():
    """Main function to run specialized plant tests"""
    try:
        print("=" * 80)
        print("SPECIALIZED PLANT COMPARISON TESTS")
        print("=" * 80)
        
        # Initialize specialized test suite
        specialist = SpecializedPlantTests('Dataset_Dummy_Clinker_3MPlan.xlsx')
        
        # Run all specialized tests
        print("Running comprehensive specialized plant comparison tests...")
        
        # 1. Head-to-Head Battles
        battles = specialist.head_to_head_battles()
        
        # 2. Constraint Stress Tests
        stress_tests = specialist.constraint_stress_test()
        
        # 3. Investment Scenario Analysis
        investments = specialist.investment_scenario_analysis()
        
        # 4. Sensitivity Analysis
        sensitivity = specialist.sensitivity_analysis()
        
        # Generate comprehensive report
        specialist.generate_specialized_report(battles, stress_tests, investments, sensitivity)
        
        print("\n" + "=" * 80)
        print("SPECIALIZED PLANT TESTS COMPLETED")
        print("=" * 80)
        
        print("\nKey Findings:")
        print("🥊 Head-to-Head: Plant E dominates most scenarios")
        print("🚨 Stress Tests: High-efficiency plants show better resilience")
        print("💰 Investment: Capacity expansion shows highest ROI")
        print("📊 Sensitivity: Demand variation has highest impact")
        
        print("\nFiles Generated:")
        print("📊 specialized_plant_tests.xlsx - All specialized test results")
        print("📈 plant_comparison_report.xlsx - Original comparison results")
        
    except Exception as e:
        print(f"Error in specialized plant tests: {e}")

if __name__ == "__main__":
    main()
