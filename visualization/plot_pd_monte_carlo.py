"""
PD-EV Monte Carlo Simulation - Right-skewed Long-tail Distribution
Features:
- X-axis: PD (Probability of Default) - varying
- Y-axis: EV (Expected Value)
- Left plot: PD vs EV scatter plot
- Right plot: EV frequency histogram (right-skewed long-tail distribution)
  * Small frequency for negative values on the left
  * Frequency increases from left to right
  * Single peak distribution
  * Long tail decreases after peak on the right
  * Sharp peak
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os
from scipy import stats

# Use default English fonts
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


def generate_pd_ev_monte_carlo(user_data, n_simulations=10000, seed=42):
    """
    Generate PD-EV Monte Carlo simulation data based on user's actual data characteristics

    Strategy:
    1. Extract PD and EV characteristics from user_data
    2. Generate PD distribution matching user's PD range and pattern
    3. Generate EV distribution with right-skewed pattern matching user's risk profile
    4. User 2 (lower risk) should have: lower PD, higher EV, fewer negatives, stronger right-skew

    Args:
        user_data: List of dicts with 'pd' and 'ev' values from user's actual data
        n_simulations: Number of simulations
        seed: Random seed

    Returns:
        pd_values: PD probability values (percentage)
        ev_values: EV expected values (currency)
    """
    np.random.seed(seed)

    # ========== 1. Extract user characteristics from actual data ==========
    pd_list = [d['pd'] for d in user_data]
    ev_list = [d['ev'] for d in user_data]

    pd_min = min(pd_list)
    pd_max = max(pd_list)
    pd_mean = np.mean(pd_list)

    ev_min = min(ev_list)
    ev_max = max(ev_list)
    ev_mean = np.mean(ev_list)

    # Count negative EV ratio in actual data
    negative_count = sum(1 for ev in ev_list if ev < 0)
    negative_ratio = negative_count / len(ev_list)

    # ========== 2. Generate PD distribution based on user's range ==========
    # Use Beta distribution, adjust parameters based on user's PD characteristics
    if pd_mean < 20:  # User 2: lower risk, more concentrated at lower PD
        pd_raw = np.random.beta(2, 4, n_simulations)  # More concentrated at lower values
    else:  # User 1: higher risk, more spread out
        pd_raw = np.random.beta(2, 3, n_simulations)

    pd_values = pd_min + pd_raw * (pd_max - pd_min)

    # ========== 3. Calculate base EV (negative correlation with PD) ==========
    # Higher PD leads to lower EV
    # Adjust base_ev and k based on user's EV characteristics
    if ev_mean > 25:  # User 2: higher average EV, more profitable
        base_ev = 75
        k = 2.0
    else:  # User 1: lower average EV
        base_ev = 65
        k = 2.2

    ev_base = base_ev - k * pd_values

    # ========== 4. Add right-skewed noise ==========
    # Adjust Gamma parameters based on user's risk profile
    if ev_mean > 25:  # User 2: sharper peak, stronger right-skew
        gamma_shape = 3.0  # Sharper peak
        gamma_scale = 12.0  # Longer tail
    else:  # User 1: less sharp
        gamma_shape = 2.5
        gamma_scale = 10.0

    noise_raw = np.random.gamma(gamma_shape, gamma_scale, n_simulations)
    noise = noise_raw - (gamma_shape * gamma_scale)
    ev_values = ev_base + noise

    # ========== 5. Set negative values based on user's actual negative ratio ==========
    # User 2 should have fewer negatives than User 1
    target_negative_ratio = max(negative_ratio, 0.02)  # At least 2%
    n_negative = int(n_simulations * target_negative_ratio)
    negative_indices = np.random.choice(n_simulations, n_negative, replace=False)

    # Set negative values based on user's actual negative range
    if ev_min < 0:
        neg_range_min = max(ev_min * 1.2, -20)  # Slightly extend the range
        neg_range_max = -1
    else:
        neg_range_min = -8
        neg_range_max = -1

    ev_values[negative_indices] = np.random.uniform(neg_range_min, neg_range_max, n_negative)

    # Convert any other unintentional negative values to small positive values
    for i in range(len(ev_values)):
        if i not in negative_indices and ev_values[i] < 0:
            ev_values[i] = abs(ev_values[i]) * 0.5

    return pd_values, ev_values


def plot_pd_ev_monte_carlo_simulation(user_data, n_simulations=10000, output_path=None, seed=42):
    """
    Plot PD-EV Monte Carlo simulation
    Left plot: PD vs EV scatter plot
    Right plot: EV frequency histogram (right-skewed long-tail distribution)

    Args:
        user_data: List of dicts with 'pd' and 'ev' values from user's actual data
        n_simulations: Number of simulations
        output_path: Output path (auto-generated if None)
        seed: Random seed for reproducibility
    """
    print(f"\n🎲 Generating PD-EV Monte Carlo Simulation (n={n_simulations:,})...")

    # Generate PD-EV data based on user characteristics
    pd_values, ev_values = generate_pd_ev_monte_carlo(user_data, n_simulations, seed)

    # Calculate EV statistics
    mean_ev = np.mean(ev_values)
    median_ev = np.median(ev_values)
    std_ev = np.std(ev_values)
    skewness = stats.skew(ev_values)
    kurtosis = stats.kurtosis(ev_values)

    # Calculate percentiles
    p5_ev = np.percentile(ev_values, 5)
    p25_ev = np.percentile(ev_values, 25)
    p75_ev = np.percentile(ev_values, 75)
    p95_ev = np.percentile(ev_values, 95)

    # Negative/positive ratios
    negative_ratio = (ev_values < 0).sum() / len(ev_values) * 100
    positive_ratio = (ev_values > 0).sum() / len(ev_values) * 100

    # PD statistics
    mean_pd = np.mean(pd_values)
    median_pd = np.median(pd_values)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # ========== Plot 1: PD vs EV Scatter Plot ==========
    # Use color mapping to represent EV values
    scatter = ax1.scatter(pd_values, ev_values,
                         c=ev_values, cmap='RdYlGn',
                         alpha=0.5, s=20, edgecolors='none')

    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('EV Expected Value (¥)', fontsize=10, fontweight='bold')

    # Add trend line (polynomial fit)
    z = np.polyfit(pd_values, ev_values, 2)
    p = np.poly1d(z)
    pd_sorted = np.sort(pd_values)
    ax1.plot(pd_sorted, p(pd_sorted), "r--", linewidth=2.5,
             label='Trend Line', alpha=0.8)

    # Mark mean point
    ax1.scatter([mean_pd], [mean_ev], color='#e74c3c', s=300, marker='*',
               edgecolors='white', linewidths=2, zorder=10,
               label=f'Mean (PD={mean_pd:.1f}%, EV=¥{mean_ev:.1f})')

    # Add reference lines
    ax1.axhline(0, color='black', linestyle='-', linewidth=1, alpha=0.3)
    ax1.axhline(mean_ev, color='#e74c3c', linestyle='--', linewidth=1.5,
                alpha=0.5, label=f'EV Mean: ¥{mean_ev:.1f}')
    ax1.axvline(mean_pd, color='#3498db', linestyle='--', linewidth=1.5,
                alpha=0.5, label=f'PD Mean: {mean_pd:.1f}%')

    ax1.set_xlabel('PD Probability of Default (%)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('EV Expected Value (¥)', fontsize=12, fontweight='bold')
    ax1.set_title('PD vs EV Scatter Plot', fontsize=14, fontweight='bold', pad=15)
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3, linestyle='--')

    # ========== Plot 2: EV Frequency Histogram (Right-skewed Long-tail) ==========
    # Use more bins to show sharp peak
    n_bins = 60

    # Plot histogram
    counts, bins, patches = ax2.hist(ev_values, bins=n_bins, density=False,
                                      alpha=0.7, color='#3498db',
                                      edgecolor='white', linewidth=0.5,
                                      orientation='vertical')

    # Color by frequency (gradient)
    cm = plt.cm.RdYlGn  # Green for high frequency (positive EV), red for low frequency (negative EV)
    norm = plt.Normalize(vmin=bins.min(), vmax=bins.max())
    for bin_val, patch in zip(bins[:-1], patches):
        patch.set_facecolor(cm(norm(bin_val)))

    # Plot kernel density estimation curve (smooth curve)
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(ev_values, bw_method=0.2)
    ev_range = np.linspace(ev_values.min(), ev_values.max(), 500)
    kde_values = kde(ev_range)
    # Scale KDE to frequency scale
    kde_scaled = kde_values * len(ev_values) * (bins[1] - bins[0])

    ax2_twin = ax2.twinx()
    ax2_twin.plot(ev_range, kde_values, 'r-', linewidth=3,
                  label='KDE', alpha=0.8)
    ax2_twin.set_ylabel('Probability Density', fontsize=11, fontweight='bold', color='red')
    ax2_twin.tick_params(axis='y', labelcolor='red')

    # Mark peak position
    peak_idx = np.argmax(kde_values)
    peak_ev = ev_range[peak_idx]
    peak_density = kde_values[peak_idx]
    ax2_twin.plot(peak_ev, peak_density, 'r*', markersize=20,
                  label=f'Peak: ¥{peak_ev:.1f}', zorder=10)

    # Mark mean and median
    ax2.axvline(mean_ev, color='#e74c3c', linestyle='--', linewidth=2.5,
                label=f'Mean: ¥{mean_ev:.1f}', alpha=0.8)
    ax2.axvline(median_ev, color='#2ecc71', linestyle='--', linewidth=2.5,
                label=f'Median: ¥{median_ev:.1f}', alpha=0.8)
    ax2.axvline(0, color='black', linestyle='-', linewidth=1.5, alpha=0.5)

    ax2.set_xlabel('EV Expected Value (¥)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax2.set_title('EV Frequency Distribution',
                  fontsize=14, fontweight='bold', pad=15)

    # Combine legends
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=9)

    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')

    plt.tight_layout()

    # Save figure
    if output_path is None:
        os.makedirs('visualization/outputs', exist_ok=True)
        output_path = 'visualization/outputs/pd_ev_monte_carlo_simulation.png'

    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved PD-EV Monte Carlo simulation plot: {output_path}")

    # Print statistics
    print(f"\n📊 Statistics:")
    print(f"  • Simulations: {n_simulations:,}")
    print(f"\n  PD Statistics:")
    print(f"    - Mean: {mean_pd:.2f}%")
    print(f"    - Median: {median_pd:.2f}%")
    print(f"    - Range: {pd_values.min():.2f}% - {pd_values.max():.2f}%")
    print(f"\n  EV Statistics:")
    print(f"    - Mean: ¥{mean_ev:.2f}")
    print(f"    - Median: ¥{median_ev:.2f}")
    print(f"    - Std Dev: ¥{std_ev:.2f}")
    print(f"    - Skewness: {skewness:.2f} {'(right-skewed)' if skewness > 0 else '(left-skewed)'}")
    print(f"    - Kurtosis: {kurtosis:.2f}")
    print(f"    - Peak Position: ¥{peak_ev:.2f}")
    print(f"    - Negative Ratio: {negative_ratio:.2f}%")
    print(f"    - Positive Ratio: {positive_ratio:.2f}%")
    print(f"    - P5: ¥{p5_ev:.2f}")
    print(f"    - P25: ¥{p25_ev:.2f}")
    print(f"    - P75: ¥{p75_ev:.2f}")
    print(f"    - P95: ¥{p95_ev:.2f}")
    print(f"\n  Correlation:")
    print(f"    - PD-EV Correlation: {np.corrcoef(pd_values, ev_values)[0,1]:.3f}")

    plt.show()

    return pd_values, ev_values


if __name__ == '__main__':
    print("="*80)
    print("PD-EV Monte Carlo Simulation - Right-skewed EV Distribution")
    print("="*80)

    # User 1 data
    user1_data = [
        {'mult': 1.0, 'pd': 15.21, 'ev': 21},
        {'mult': 1.5, 'pd': 15.87, 'ev': 32},
        {'mult': 2.0, 'pd': 16.55, 'ev': 42},
        {'mult': 2.5, 'pd': 17.26, 'ev': 45},
        {'mult': 3.0, 'pd': 18.01, 'ev': 43},
        {'mult': 4.0, 'pd': 19.60, 'ev': 39},
        {'mult': 5.0, 'pd': 21.32, 'ev': 34},
        {'mult': 6.0, 'pd': 23.20, 'ev': 26},
        {'mult': 7.0, 'pd': 25.24, 'ev': 17},
        {'mult': 8.0, 'pd': 27.47, 'ev': 5},
        {'mult': 9.0, 'pd': 29.11, 'ev': -4},
        {'mult': 10.0, 'pd': 31.67, 'ev': -18},
    ]

    # User 2 data
    user2_data = [
        {'mult': 1.0, 'pd': 9.67, 'ev': 19},
        {'mult': 1.5, 'pd': 10.39, 'ev': 28},
        {'mult': 2.0, 'pd': 11.16, 'ev': 37},
        {'mult': 2.5, 'pd': 11.98, 'ev': 39},
        {'mult': 3.0, 'pd': 12.87, 'ev': 40},
        {'mult': 4.0, 'pd': 14.84, 'ev': 41},
        {'mult': 5.0, 'pd': 16.24, 'ev': 42},
        {'mult': 6.0, 'pd': 18.73, 'ev': 38},
        {'mult': 7.0, 'pd': 23.98, 'ev': 25},
        {'mult': 8.0, 'pd': 27.04, 'ev': 18},
        {'mult': 9.0, 'pd': 28.70, 'ev': 17},
        {'mult': 10.0, 'pd': 34.19, 'ev': 3},
    ]

    # Generate plots for both users
    print("\n" + "="*80)
    print("Generating User 1 Monte Carlo Simulation...")
    print("  User 1 Profile: Higher risk, lower average EV, has negative values")
    print("="*80)
    pd_values1, ev_values1 = plot_pd_ev_monte_carlo_simulation(
        user_data=user1_data,
        n_simulations=10000,
        output_path='visualization/outputs/pd_ev_mc_user1.png',
        seed=42
    )

    print("\n" + "="*80)
    print("Generating User 2 Monte Carlo Simulation...")
    print("  User 2 Profile: Lower risk, higher average EV, more profitable")
    print("="*80)
    pd_values2, ev_values2 = plot_pd_ev_monte_carlo_simulation(
        user_data=user2_data,
        n_simulations=10000,
        output_path='visualization/outputs/pd_ev_mc_user2.png',
        seed=43  # Different seed for different distribution
    )

    print("\n" + "="*80)
    print("✅ All PD-EV Monte Carlo Simulations Complete!")
    print("="*80)

