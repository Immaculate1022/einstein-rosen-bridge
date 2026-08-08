"""
Visualization tools for wormhole transit dynamics.

Generates plots showing:
- Particle trajectories through the wormhole
- Tidal force profiles
- Proper time vs coordinate time
- Energy density and metric components
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from wormhole_transit import (
    simulate_transit_mission, WormholeGeometry,
    ALPHA, LAMBDA, SIGMA, GRID_SIZE, DX, X
)


def plot_transit_trajectories(trajectories, T00_field, save_path=None):
    """
    Plot particle trajectories overlaid on energy density field.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Trajectories in spacetime
    ax1.set_title('Particle Trajectories Through Wormhole', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Position x')
    ax1.set_ylabel('Coordinate Time t')
    
    # Color code by initial velocity
    colors = plt.cm.viridis(np.linspace(0, 1, len(trajectories)))
    
    for i, (trajectory, color) in enumerate(zip(trajectories, colors)):
        ax1.plot(trajectory.trajectory_x, trajectory.trajectory_t, 
                color=color, linewidth=2, label=f'Particle {i+1}', alpha=0.8)
        
        # Mark start and end points
        ax1.plot(trajectory.trajectory_x[0], trajectory.trajectory_t[0], 
                'o', color=color, markersize=8)
        ax1.plot(trajectory.trajectory_x[-1], trajectory.trajectory_t[-1], 
                's', color=color, markersize=8)
    
    # Highlight throat region
    ax1.axvspan(-2, 2, alpha=0.1, color='red', label='Throat Region')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Energy density profile
    ax2.set_title('Energy Density T₀₀ Profile', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Position x')
    ax2.set_ylabel('T₀₀ (Energy Density)')
    
    ax2.fill_between(X, 0, T00_field, where=(T00_field < 0), 
                     alpha=0.3, color='red', label='Negative Energy (Exotic Matter)')
    ax2.fill_between(X, 0, T00_field, where=(T00_field >= 0), 
                     alpha=0.3, color='blue', label='Positive Energy')
    ax2.plot(X, T00_field, 'k-', linewidth=2)
    ax2.axhline(y=0, color='k', linestyle='--', linewidth=1)
    ax2.axvline(x=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_tidal_forces(trajectories, save_path=None):
    """
    Plot tidal force experienced along each trajectory.
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 1: Tidal forces vs position
    ax = axes[0]
    ax.set_title('Tidal Force Profile Along Trajectories', fontsize=12, fontweight='bold')
    ax.set_xlabel('Position x')
    ax.set_ylabel('Tidal Force (Riemann Component)')
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(trajectories)))
    
    for trajectory, color in zip(trajectories, colors):
        ax.plot(trajectory.trajectory_x, trajectory.trajectory_tidal, 
               color=color, linewidth=2, alpha=0.7)
    
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Throat')
    ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Tidal stress vs time
    ax = axes[1]
    ax.set_title('Tidal Stress Over Time', fontsize=12, fontweight='bold')
    ax.set_xlabel('Coordinate Time t')
    ax.set_ylabel('|Tidal Force|')
    
    for trajectory, color in zip(trajectories, colors):
        ax.semilogy(trajectory.trajectory_t, np.abs(trajectory.trajectory_tidal) + 1e-6, 
                   color=color, linewidth=2, alpha=0.7, label=f'Particle {trajectory.x0:.1f}')
    
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3, which='both')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_proper_time_dilation(trajectories, save_path=None):
    """
    Plot proper time vs coordinate time (time dilation effect).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Proper time vs coordinate time
    ax1.set_title('Proper Time vs Coordinate Time', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Coordinate Time t')
    ax1.set_ylabel('Proper Time τ')
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(trajectories)))
    
    for trajectory, color in zip(trajectories, colors):
        ax1.plot(trajectory.trajectory_t, trajectory.trajectory_tau, 
                color=color, linewidth=2, label=f'x₀={trajectory.x0:.1f}', alpha=0.8)
    
    # Reference: no time dilation
    t_max = max(traj.trajectory_t[-1] for traj in trajectories)
    ax1.plot([0, t_max], [0, t_max], 'k--', linewidth=1, alpha=0.5, label='No Dilation')
    
    ax1.legend(loc='upper left', fontsize=9)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Time dilation factor
    ax2.set_title('Time Dilation Factor (dτ/dt)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Position x')
    ax2.set_ylabel('Time Dilation Factor')
    
    for trajectory, color in zip(trajectories, colors):
        dilation = np.gradient(trajectory.trajectory_tau, trajectory.trajectory_t)
        dilation = np.clip(dilation, 0.5, 1.5)  # Clip for visualization
        ax2.plot(trajectory.trajectory_x, dilation, 
                color=color, linewidth=2, alpha=0.7)
    
    ax2.axhline(y=1.0, color='k', linestyle='--', linewidth=1, alpha=0.5)
    ax2.axvline(x=0, color='red', linestyle='--', linewidth=2, alpha=0.3, label='Throat')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def plot_metric_components(T00_field, phi_field, save_path=None):
    """
    Plot metric components g_00 and g_rr across the wormhole.
    """
    geometry = WormholeGeometry(T00_field, phi_field)
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Calculate metric components
    g00_vals = np.array([geometry.metric_component_g00(x) for x in X])
    grr_vals = np.array([geometry.metric_component_grr(x) for x in X])
    
    # Plot 1: g_00 (timelike component)
    ax = axes[0]
    ax.set_title('Metric Component g₀₀ (Timelike)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Position x')
    ax.set_ylabel('g₀₀')
    ax.fill_between(X, 0, g00_vals, alpha=0.3, color='blue')
    ax.plot(X, g00_vals, 'b-', linewidth=2)
    ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Throat')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Plot 2: g_rr (spacelike component)
    ax = axes[1]
    ax.set_title('Metric Component g_rr (Spacelike)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Position x')
    ax.set_ylabel('g_rr')
    ax.fill_between(X, 0, grr_vals, alpha=0.3, color='green')
    ax.plot(X, grr_vals, 'g-', linewidth=2)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=2, alpha=0.5, label='Throat')
    ax.set_ylim([0, max(grr_vals) * 1.1])
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    
    return fig


def create_summary_report(trajectories, transit_results, T00_field, phi_field, output_dir='./'):
    """
    Create a comprehensive summary report with all visualizations.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print("\nGenerating visualization report...")
    
    # Plot 1: Trajectories
    plot_transit_trajectories(trajectories, T00_field, 
                             save_path=f"{output_dir}/01_trajectories.png")
    
    # Plot 2: Tidal forces
    plot_tidal_forces(trajectories, 
                     save_path=f"{output_dir}/02_tidal_forces.png")
    
    # Plot 3: Time dilation
    plot_proper_time_dilation(trajectories, 
                             save_path=f"{output_dir}/03_time_dilation.png")
    
    # Plot 4: Metric components
    plot_metric_components(T00_field, phi_field, 
                          save_path=f"{output_dir}/04_metric_components.png")
    
    print(f"✓ Report saved to {output_dir}")
    
    plt.show()


if __name__ == "__main__":
    from stabilized_bridge import run_stabilized_bridge_simulation, SIGMA
    
    print("Running stabilized bridge simulation...")
    snapshots = run_stabilized_bridge_simulation()
    final_t, final_T00 = snapshots[-1]
    
    phi_field = np.arctan(X / SIGMA)
    
    print("Simulating transit dynamics...")
    trajectories, transit_results = simulate_transit_mission(final_T00, phi_field, num_particles=5)
    
    print("Creating visualization report...")
    create_summary_report(trajectories, transit_results, final_T00, phi_field, output_dir='./wormhole_transit_report')
