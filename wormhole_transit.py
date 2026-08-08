"""
Traversable Wormhole Transit Dynamics

This module extends the stabilized Einstein-Rosen bridge simulation to model
particle trajectories through the wormhole throat. It includes:

- Geodesic equation solver for particle motion
- Tidal force calculations (Riemann curvature effects)
- Proper time tracking for observers
- Stability analysis of transit corridors
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from stabilized_bridge import (
    ALPHA, LAMBDA, SIGMA, GRID_SIZE, DX, X,
    lagrangian_density, compute_stress_tensor_T00
)


class WormholeGeometry:
    """
    Represents the metric and curvature of the stabilized wormhole.
    Uses the Morris-Thorne form with shape function b(r) derived from T_00.
    """

    def __init__(self, T00_field, phi_field):
        """
        Initialize wormhole geometry from field configuration.
        
        Args:
            T00_field: Energy density array from stabilized bridge simulation
            phi_field: Scalar field configuration
        """
        self.T00 = T00_field
        self.phi = phi_field
        self.x_grid = X
        self.dx = DX
        
        # Compute shape function b(r) from Einstein equations
        # For simplicity: b(r) ~ -T_00 (negative energy creates throat)
        self.shape_function = -np.maximum(T00_field, 0)
        
        # Redshift function: e^(2*Phi) ~ 1 + small corrections
        self.redshift = np.ones_like(X)

    def metric_component_g00(self, x):
        """
        Metric component g_00 = -e^(2*Phi(r))
        For traversable wormhole, must remain negative (timelike).
        """
        idx = np.argmin(np.abs(self.x_grid - x))
        return -(1.0 + 0.1 * self.redshift[idx])

    def metric_component_grr(self, x):
        """
        Metric component g_rr = e^(2*Lambda(r)) / (1 - b(r)/r)
        Must be positive for spacelike.
        """
        idx = np.argmin(np.abs(self.x_grid - x))
        r = np.abs(x) + 1e-6  # Avoid division by zero
        b_r = self.shape_function[idx]
        
        if r <= b_r:  # Inside throat
            return 1.0 / (1.0 - b_r / r + 1e-6)
        return 1.0 / (1.0 - b_r / r)

    def riemann_component(self, x, direction='radial'):
        """
        Riemann curvature component for tidal force calculation.
        Approximated from second derivatives of metric.
        """
        idx = np.argmin(np.abs(self.x_grid - x))
        
        if idx < 1 or idx >= len(self.x_grid) - 1:
            return 0.0
        
        # Numerical second derivative of shape function
        d2b_dr2 = (self.shape_function[idx + 1] - 2 * self.shape_function[idx] + 
                   self.shape_function[idx - 1]) / (self.dx ** 2)
        
        return d2b_dr2


class ParticleTrajectory:
    """
    Represents a test particle transiting through the wormhole.
    Solves the geodesic equation: d²x^μ/dτ² + Γ^μ_νρ (dx^ν/dτ)(dx^ρ/dτ) = 0
    """

    def __init__(self, wormhole_geometry, initial_position, initial_velocity, mass=1.0):
        """
        Initialize particle trajectory.
        
        Args:
            wormhole_geometry: WormholeGeometry instance
            initial_position: Starting position (x coordinate)
            initial_velocity: Starting velocity (dx/dt)
            mass: Particle mass (for proper time calculation)
        """
        self.geometry = wormhole_geometry
        self.x0 = initial_position
        self.v0 = initial_velocity
        self.mass = mass
        
        self.trajectory_x = []
        self.trajectory_v = []
        self.trajectory_t = []
        self.trajectory_tau = []  # Proper time
        self.trajectory_tidal = []  # Tidal forces
        
    def geodesic_equations(self, state, t):
        """
        Geodesic equations in the wormhole spacetime.
        state = [x, v] where v = dx/dt
        
        d²x/dt² = -Γ^x_μν (dx^μ/dt)(dx^ν/dt) + tidal_force
        """
        x, v = state
        
        # Christoffel symbol approximation: Γ^x_tt ~ -g_tt,x / 2
        idx = np.argmin(np.abs(self.geometry.x_grid - x))
        
        if idx < 1 or idx >= len(self.geometry.x_grid) - 1:
            return [v, 0.0]
        
        # Metric derivative
        dg00_dx = (self.geometry.metric_component_g00(x + self.geometry.dx) - 
                   self.geometry.metric_component_g00(x - self.geometry.dx)) / (2 * self.geometry.dx)
        
        # Geodesic acceleration
        a_geodesic = 0.5 * dg00_dx * (v ** 2)
        
        # Tidal force (from Riemann curvature)
        tidal = self.geometry.riemann_component(x, 'radial')
        
        # Total acceleration
        a_total = a_geodesic + 0.1 * tidal
        
        return [v, a_total]

    def integrate_trajectory(self, t_max, num_steps=1000):
        """
        Integrate particle trajectory through wormhole.
        """
        t_eval = np.linspace(0, t_max, num_steps)
        initial_state = [self.x0, self.v0]
        
        # Solve geodesic equations
        solution = odeint(self.geodesic_equations, initial_state, t_eval)
        
        self.trajectory_x = solution[:, 0]
        self.trajectory_v = solution[:, 1]
        self.trajectory_t = t_eval
        
        # Calculate proper time: dτ = dt * sqrt(-g_μν (dx^μ/dt)(dx^ν/dt))
        proper_time = np.zeros_like(t_eval)
        tidal_forces = np.zeros_like(t_eval)
        
        for i, (x, v, t) in enumerate(zip(self.trajectory_x, self.trajectory_v, t_eval)):
            # Proper time increment
            g00 = self.geometry.metric_component_g00(x)
            grr = self.geometry.metric_component_grr(x)
            
            # ds² = -g_00 dt² + g_rr dr²
            ds2 = -g00 + grr * (v ** 2)
            dtau_dt = np.sqrt(np.maximum(ds2, 0.0))
            
            if i > 0:
                proper_time[i] = proper_time[i-1] + dtau_dt * (t_eval[i] - t_eval[i-1])
            
            # Tidal force
            tidal_forces[i] = self.geometry.riemann_component(x, 'radial')
        
        self.trajectory_tau = proper_time
        self.trajectory_tidal = tidal_forces
        
        return solution

    def check_traversability(self):
        """
        Verify that particle trajectory remains timelike and causally connected.
        Returns: (is_traversable, violation_count, max_violation)
        """
        violations = 0
        max_violation = 0.0
        
        for x, v in zip(self.trajectory_x, self.trajectory_v):
            g00 = self.geometry.metric_component_g00(x)
            grr = self.geometry.metric_component_grr(x)
            
            # Timelike condition: -g_00 > g_rr * v²
            timelike_check = -g00 - grr * (v ** 2)
            
            if timelike_check < 0:
                violations += 1
                max_violation = max(max_violation, abs(timelike_check))
        
        is_traversable = violations == 0
        return is_traversable, violations, max_violation

    def calculate_tidal_stress(self):
        """
        Calculate maximum tidal stress experienced during transit.
        Tidal stress ~ |Riemann| * (particle_size)
        """
        max_tidal = np.max(np.abs(self.trajectory_tidal))
        mean_tidal = np.mean(np.abs(self.trajectory_tidal))
        
        # Estimate survivability (rough heuristic)
        # Humans can tolerate ~10 g's; tidal stress scales with curvature
        survivability_factor = 1.0 / (1.0 + max_tidal)
        
        return {
            'max_tidal_stress': max_tidal,
            'mean_tidal_stress': mean_tidal,
            'survivability_factor': survivability_factor
        }


def simulate_transit_mission(T00_field, phi_field, num_particles=5):
    """
    Simulate multiple particles transiting through the wormhole.
    """
    geometry = WormholeGeometry(T00_field, phi_field)
    
    # Initial conditions for particles
    # Vary initial velocities to explore transit corridor
    initial_positions = np.linspace(-20, 20, num_particles)
    initial_velocities = np.linspace(0.1, 0.5, num_particles)
    
    trajectories = []
    transit_results = []
    
    for x0, v0 in zip(initial_positions, initial_velocities):
        particle = ParticleTrajectory(geometry, x0, v0)
        particle.integrate_trajectory(t_max=100, num_steps=500)
        
        is_traversable, violations, max_violation = particle.check_traversability()
        tidal_stress = particle.calculate_tidal_stress()
        
        trajectories.append(particle)
        transit_results.append({
            'initial_position': x0,
            'initial_velocity': v0,
            'traversable': is_traversable,
            'violations': violations,
            'max_violation': max_violation,
            'tidal_stress': tidal_stress,
            'proper_time': particle.trajectory_tau[-1] if len(particle.trajectory_tau) > 0 else 0.0,
            'coordinate_time': particle.trajectory_t[-1] if len(particle.trajectory_t) > 0 else 0.0
        })
    
    return trajectories, transit_results


def print_transit_diagnostics(transit_results):
    """
    Print summary of transit mission results.
    """
    print("\n" + "=" * 70)
    print("WORMHOLE TRANSIT MISSION DIAGNOSTICS")
    print("=" * 70)
    
    traversable_count = sum(1 for r in transit_results if r['traversable'])
    
    print(f"\nTraversable Trajectories: {traversable_count}/{len(transit_results)}")
    
    for i, result in enumerate(transit_results):
        print(f"\n--- Particle {i+1} ---")
        print(f"Initial Position: x = {result['initial_position']:.2f}")
        print(f"Initial Velocity: v = {result['initial_velocity']:.3f}")
        print(f"Traversable: {'✓ YES' if result['traversable'] else '✗ NO'}")
        
        if not result['traversable']:
            print(f"  Timelike Violations: {result['violations']}")
            print(f"  Max Violation: {result['max_violation']:.6f}")
        
        tidal = result['tidal_stress']
        print(f"Max Tidal Stress: {tidal['max_tidal_stress']:.6f}")
        print(f"Survivability Factor: {tidal['survivability_factor']:.3f}")
        print(f"Coordinate Time: {result['coordinate_time']:.2f}")
        print(f"Proper Time: {result['proper_time']:.2f}")
        print(f"Time Dilation Factor: {result['coordinate_time'] / (result['proper_time'] + 1e-6):.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Import stabilized bridge simulation
    from stabilized_bridge import run_stabilized_bridge_simulation
    
    print("Running stabilized bridge simulation...")
    snapshots = run_stabilized_bridge_simulation()
    final_t, final_T00 = snapshots[-1]
    
    # Create dummy phi field for demonstration
    phi_field = np.arctan(X / SIGMA)
    
    print("Simulating wormhole transit dynamics...")
    trajectories, transit_results = simulate_transit_mission(final_T00, phi_field, num_particles=5)
    
    print_transit_diagnostics(transit_results)
    
    print("\n✓ Transit simulation complete.")
