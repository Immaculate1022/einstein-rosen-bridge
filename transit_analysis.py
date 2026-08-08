"""
Transit Corridor Analysis

Analyzes the safe transit corridor through the wormhole:
- Identifies optimal trajectories
- Calculates safety margins
- Estimates transit time vs survivability tradeoffs
- Provides mission planning recommendations
"""

import numpy as np
from wormhole_transit import simulate_transit_mission, ParticleTrajectory, WormholeGeometry
from stabilized_bridge import SIGMA, X, DX


class TransitCorridorAnalysis:
    """
    Comprehensive analysis of wormhole transit safety and efficiency.
    """

    def __init__(self, T00_field, phi_field):
        """
        Initialize corridor analysis.
        """
        self.T00 = T00_field
        self.phi = phi_field
        self.geometry = WormholeGeometry(T00_field, phi_field)
        
        self.optimal_trajectory = None
        self.safety_margin = None
        self.transit_corridor = None

    def find_optimal_trajectory(self, num_samples=20):
        """
        Search for the optimal transit trajectory that minimizes tidal stress
        while maintaining traversability.
        """
        print("\nSearching for optimal trajectory...")
        
        # Sample initial conditions
        x0_values = np.linspace(-15, 15, num_samples)
        v0_values = np.linspace(0.05, 0.8, num_samples)
        
        best_trajectory = None
        best_score = float('inf')
        best_result = None
        
        for x0 in x0_values:
            for v0 in v0_values:
                particle = ParticleTrajectory(self.geometry, x0, v0)
                particle.integrate_trajectory(t_max=100, num_steps=500)
                
                is_traversable, violations, max_violation = particle.check_traversability()
                
                if is_traversable:
                    tidal_stress = particle.calculate_tidal_stress()
                    
                    # Optimization score: minimize tidal stress, prefer shorter transit time
                    score = (tidal_stress['max_tidal_stress'] + 
                            0.1 * particle.trajectory_t[-1])
                    
                    if score < best_score:
                        best_score = score
                        best_trajectory = particle
                        best_result = {
                            'x0': x0,
                            'v0': v0,
                            'tidal_stress': tidal_stress,
                            'score': score
                        }
        
        self.optimal_trajectory = best_trajectory
        
        if best_result:
            print(f"✓ Optimal trajectory found:")
            print(f"  Initial Position: x₀ = {best_result['x0']:.2f}")
            print(f"  Initial Velocity: v₀ = {best_result['v0']:.3f}")
            print(f"  Max Tidal Stress: {best_result['tidal_stress']['max_tidal_stress']:.6f}")
            print(f"  Survivability: {best_result['tidal_stress']['survivability_factor']:.3f}")
        else:
            print("✗ No traversable trajectory found in search space")
        
        return best_trajectory, best_result

    def calculate_safety_corridor(self, optimal_trajectory, tolerance=0.2):
        """
        Calculate the safe corridor around the optimal trajectory.
        Particles within this corridor experience acceptable tidal forces.
        """
        print("\nCalculating safety corridor...")
        
        if optimal_trajectory is None:
            print("No optimal trajectory available")
            return None
        
        # Define corridor as ±tolerance around optimal path
        x_optimal = optimal_trajectory.trajectory_x
        v_optimal = optimal_trajectory.trajectory_v
        
        corridor_bounds = {
            'x_lower': x_optimal - tolerance,
            'x_upper': x_optimal + tolerance,
            'v_lower': v_optimal * (1 - tolerance),
            'v_upper': v_optimal * (1 + tolerance),
        }
        
        # Test trajectories within corridor
        test_trajectories = []
        for offset in np.linspace(-tolerance, tolerance, 5):
            test_x0 = optimal_trajectory.x0 + offset
            test_v0 = optimal_trajectory.v0 * (1 + offset / 10)
            
            particle = ParticleTrajectory(self.geometry, test_x0, test_v0)
            particle.integrate_trajectory(t_max=100, num_steps=500)
            
            is_traversable, _, _ = particle.check_traversability()
            test_trajectories.append({
                'particle': particle,
                'traversable': is_traversable,
                'x0': test_x0,
                'v0': test_v0
            })
        
        traversable_count = sum(1 for t in test_trajectories if t['traversable'])
        
        print(f"✓ Safety corridor identified:")
        print(f"  Traversable trajectories: {traversable_count}/{len(test_trajectories)}")
        print(f"  Position tolerance: ±{tolerance:.2f}")
        print(f"  Velocity tolerance: ±{tolerance*100:.1f}%")
        
        self.transit_corridor = {
            'bounds': corridor_bounds,
            'test_trajectories': test_trajectories,
            'traversable_fraction': traversable_count / len(test_trajectories)
        }
        
        return self.transit_corridor

    def estimate_mission_profile(self, num_particles=10):
        """
        Estimate mission profile for a convoy of particles.
        """
        print("\nEstimating mission profile...")
        
        trajectories, results = simulate_transit_mission(self.T00, self.phi, num_particles)
        
        # Analyze results
        successful = sum(1 for r in results if r['traversable'])
        avg_tidal = np.mean([r['tidal_stress']['max_tidal_stress'] for r in results])
        avg_time = np.mean([r['coordinate_time'] for r in results])
        avg_proper_time = np.mean([r['proper_time'] for r in results])
        
        mission_profile = {
            'total_particles': num_particles,
            'successful_transit': successful,
            'success_rate': successful / num_particles,
            'avg_tidal_stress': avg_tidal,
            'avg_coordinate_time': avg_time,
            'avg_proper_time': avg_proper_time,
            'avg_time_dilation': avg_time / (avg_proper_time + 1e-6),
            'trajectories': trajectories,
            'results': results
        }
        
        print(f"✓ Mission profile:")
        print(f"  Success Rate: {mission_profile['success_rate']*100:.1f}%")
        print(f"  Avg Tidal Stress: {mission_profile['avg_tidal_stress']:.6f}")
        print(f"  Avg Transit Time (coordinate): {mission_profile['avg_coordinate_time']:.2f}")
        print(f"  Avg Transit Time (proper): {mission_profile['avg_proper_time']:.2f}")
        print(f"  Time Dilation Factor: {mission_profile['avg_time_dilation']:.3f}")
        
        return mission_profile

    def generate_mission_report(self):
        """
        Generate comprehensive mission planning report.
        """
        print("\n" + "=" * 70)
        print("WORMHOLE TRANSIT MISSION PLANNING REPORT")
        print("=" * 70)
        
        # Find optimal trajectory
        optimal, opt_result = self.find_optimal_trajectory(num_samples=15)
        
        if optimal is None:
            print("\n✗ MISSION FEASIBILITY: NOT RECOMMENDED")
            print("No traversable corridors identified in current wormhole configuration.")
            return None
        
        # Calculate safety corridor
        corridor = self.calculate_safety_corridor(optimal, tolerance=0.15)
        
        # Estimate mission profile
        mission = self.estimate_mission_profile(num_particles=10)
        
        # Generate recommendations
        print("\n" + "-" * 70)
        print("MISSION RECOMMENDATIONS")
        print("-" * 70)
        
        if mission['success_rate'] >= 0.9:
            feasibility = "✓ HIGHLY FEASIBLE"
        elif mission['success_rate'] >= 0.7:
            feasibility = "◐ MODERATELY FEASIBLE"
        else:
            feasibility = "✗ RISKY"
        
        print(f"\nMission Feasibility: {feasibility}")
        print(f"Recommended Convoy Size: {mission['total_particles']} vessels")
        print(f"Expected Success Rate: {mission['success_rate']*100:.1f}%")
        
        print(f"\nOptimal Transit Profile:")
        print(f"  Entry Position: x = {opt_result['x0']:.2f}")
        print(f"  Entry Velocity: v = {opt_result['v0']:.3f}")
        print(f"  Estimated Transit Time: {optimal.trajectory_t[-1]:.2f} coordinate seconds")
        print(f"  Experienced Time: {optimal.trajectory_tau[-1]:.2f} proper seconds")
        print(f"  Maximum Tidal Stress: {opt_result['tidal_stress']['max_tidal_stress']:.6f}")
        print(f"  Survivability Rating: {opt_result['tidal_stress']['survivability_factor']*100:.1f}%")
        
        print(f"\nSafety Margins:")
        print(f"  Position Tolerance: ±{0.15:.2f} units")
        print(f"  Velocity Tolerance: ±15%")
        print(f"  Safe Corridor Traversability: {corridor['traversable_fraction']*100:.1f}%")
        
        print(f"\nTime Dilation Effects:")
        print(f"  Coordinate Time: {mission['avg_coordinate_time']:.2f} seconds")
        print(f"  Proper Time (experienced): {mission['avg_proper_time']:.2f} seconds")
        print(f"  Time Dilation Factor: {mission['avg_time_dilation']:.3f}x")
        
        if mission['avg_time_dilation'] > 1.1:
            print(f"  ⚠ Significant time dilation detected")
            print(f"    Travelers will experience {(1 - 1/mission['avg_time_dilation'])*100:.1f}% less time than external observers")
        
        print("\n" + "=" * 70)
        
        return {
            'optimal_trajectory': optimal,
            'optimal_result': opt_result,
            'safety_corridor': corridor,
            'mission_profile': mission
        }


def main():
    """
    Run complete transit corridor analysis.
    """
    from stabilized_bridge import run_stabilized_bridge_simulation
    
    print("Initializing transit corridor analysis...")
    
    # Run stabilized bridge simulation
    snapshots = run_stabilized_bridge_simulation()
    final_t, final_T00 = snapshots[-1]
    
    phi_field = np.arctan(X / SIGMA)
    
    # Create analysis
    analysis = TransitCorridorAnalysis(final_T00, phi_field)
    
    # Generate mission report
    report = analysis.generate_mission_report()
    
    if report:
        print("\n✓ Transit corridor analysis complete.")
        print("Mission planning data available for decision-making.")


if __name__ == "__main__":
    main()
