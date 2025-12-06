#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
信用额度分析可视化工具
生成符合顶会要求的高质量图表
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams
import warnings
warnings.filterwarnings('ignore')

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from services.credit_limit_service import CreditLimitService
from services.pdf_service import PDFService

# 设置科研级别的绘图参数
def setup_plot_style():
    """设置高质量的绘图风格"""
    # 使用IEEE风格的字体设置
    rcParams['font.family'] = 'serif'
    rcParams['font.serif'] = ['Times New Roman']
    rcParams['font.size'] = 11
    rcParams['axes.labelsize'] = 12
    rcParams['axes.titlesize'] = 13
    rcParams['xtick.labelsize'] = 10
    rcParams['ytick.labelsize'] = 10
    rcParams['legend.fontsize'] = 10
    rcParams['figure.titlesize'] = 14
    
    # 设置线条和网格
    rcParams['axes.linewidth'] = 1.2
    rcParams['grid.linewidth'] = 0.5
    rcParams['lines.linewidth'] = 2
    rcParams['lines.markersize'] = 6
    
    # 设置图形质量
    rcParams['figure.dpi'] = 300
    rcParams['savefig.dpi'] = 300
    rcParams['savefig.bbox'] = 'tight'
    rcParams['savefig.pad_inches'] = 0.1
    
    # 使用科研配色方案
    sns.set_palette("Set2")

# 科研配色方案
COLORS = {
    'primary': '#2E86AB',      # 深蓝色
    'secondary': '#A23B72',    # 紫红色
    'accent': '#F18F01',       # 橙色
    'success': '#06A77D',      # 绿色
    'warning': '#D62246',      # 红色
    'neutral': '#6C757D',      # 灰色
    'light_blue': '#89CFF0',   # 浅蓝色
    'light_red': '#FFB3BA',    # 浅红色
}

def analyze_credit_limits(pdf_path, output_dir='visualization/outputs'):
    """
    分析信用额度并生成可视化图表
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*80)
    print("信用额度分析可视化")
    print("="*80)
    
    # 1. 提取PDF数据
    print("\n📄 提取PDF数据...")
    pdf_service = PDFService()
    result = pdf_service.extract_bank_statement(pdf_path)
    
    if not result.get('success'):
        print(f"❌ PDF提取失败: {result.get('message')}")
        return
    
    total_income = result.get('total_income', 74707.66)
    balance = result.get('current_balance', result.get('balance', 4204.74))
    
    print(f"✓ 总收入: ¥{total_income:,.2f}")
    print(f"✓ 当前余额: ¥{balance:,.2f}")
    
    # 2. 初始化信用额度服务
    print("\n🔧 初始化信用额度服务...")
    credit_service = CreditLimitService()
    
    # 3. 生成更多候选额度（用于详细分析）
    print("\n📊 生成候选额度...")
    base_amount = balance
    # 使用更密集的倍数范围（与优化器保持一致：1.0x - 10.0x）
    multipliers = np.linspace(1.0, 10.0, 100)  # 100个候选额度，更平滑的曲线
    candidate_limits = base_amount * multipliers

    print(f"✓ 生成{len(candidate_limits)}个候选额度")
    print(f"✓ 范围: ¥{candidate_limits.min():,.2f} - ¥{candidate_limits.max():,.2f}")
    print(f"✓ 倍数范围: {multipliers.min():.1f}x - {multipliers.max():.1f}x")
    
    # 4. 评估所有候选额度
    print("\n⚙️  评估所有候选额度...")
    results = []
    
    for i, limit in enumerate(candidate_limits):
        if (i + 1) % 10 == 0:
            print(f"  进度: {i+1}/{len(candidate_limits)}")

        # 提取特征
        features = credit_service.feature_service.extract_features_from_pdf_data(
            pdf_data=result,
            credit_amount=limit
        )

        # 评估该额度（传入initial_balance）
        eval_result = credit_service.optimizer.evaluate_single_limit(
            credit_limit=limit,
            features=features,
            initial_balance=balance  # 传入用户余额作为本金
        )
        
        results.append({
            'multiplier': limit / base_amount,
            'credit_limit': limit,
            'pd': eval_result['pd'],
            'velocity': eval_result['velocity'],
            'gmv': eval_result['gmv'],
            'ev': eval_result['ev'],
            'total_revenue': eval_result['total_revenue'],
            'total_cost': eval_result['total_cost'],
        })
    
    print(f"✓ 评估完成")
    
    return results, base_amount, total_income, balance, output_dir

def plot_pd_velocity_analysis(results, output_dir):
    """绘制PD和周转率随额度变化的图表"""
    print("\n📈 绘制PD和周转率分析图...")

    multipliers = np.array([r['multiplier'] for r in results])
    # 确保PD和velocity是标量
    pds = np.array([float(np.array(r['pd']).item()) * 100 for r in results])  # 转换为百分比
    velocities = np.array([float(np.array(r['velocity']).item()) * 100 for r in results])  # 转换为百分比

    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 图1: PD随额度变化
    ax1.plot(multipliers, pds, color=COLORS['warning'], linewidth=2.5,
             marker='o', markersize=4, markevery=5, label='Default Probability')
    ax1.fill_between(multipliers, pds, alpha=0.2, color=COLORS['warning'])
    ax1.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold')
    ax1.set_ylabel('Default Probability (%)', fontweight='bold')
    ax1.set_title('(a) Default Probability vs. Credit Limit', fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim(multipliers[0], multipliers[-1])

    # 添加参考线
    ax1.axhline(y=15, color=COLORS['neutral'], linestyle='--',
                linewidth=1, alpha=0.5, label='Risk Threshold (15%)')
    ax1.legend(loc='upper left', framealpha=0.9)

    # 图2: 周转率随额度变化
    ax2.plot(multipliers, velocities, color=COLORS['primary'], linewidth=2.5,
             marker='s', markersize=4, markevery=5, label='Velocity Rate')
    ax2.fill_between(multipliers, velocities, alpha=0.2, color=COLORS['primary'])
    ax2.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold')
    ax2.set_ylabel('Velocity Rate (%)', fontweight='bold')
    ax2.set_title('(b) Velocity Rate vs. Credit Limit', fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xlim(multipliers[0], multipliers[-1])
    ax2.legend(loc='upper right', framealpha=0.9)

    plt.tight_layout()

    # 保存图表
    output_path = os.path.join(output_dir, 'pd_velocity_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 保存图表: {output_path}")
    plt.close()


def plot_ev_analysis(results, output_dir):
    """绘制EV分析图（包括收入和成本）"""
    print("\n📊 绘制EV分析图...")

    multipliers = np.array([r['multiplier'] for r in results])
    evs = np.array([float(r['ev']) for r in results])
    revenues = np.array([float(r['total_revenue']) for r in results])
    costs = np.array([float(r['total_cost']) for r in results])

    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 图1: 收入和成本对比
    ax1.plot(multipliers, revenues, color=COLORS['success'], linewidth=2.5,
             marker='o', markersize=4, markevery=5, label='Total Revenue')
    ax1.plot(multipliers, costs, color=COLORS['warning'], linewidth=2.5,
             marker='s', markersize=4, markevery=5, label='Total Cost')
    ax1.fill_between(multipliers, revenues, alpha=0.15, color=COLORS['success'])
    ax1.fill_between(multipliers, costs, alpha=0.15, color=COLORS['warning'])
    ax1.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold')
    ax1.set_ylabel('Amount (¥)', fontweight='bold')
    ax1.set_title('(a) Revenue and Cost vs. Credit Limit', fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='upper left', framealpha=0.9)
    ax1.set_xlim(multipliers[0], multipliers[-1])

    # 图2: EV曲线
    # 区分正负EV
    positive_mask = np.array(evs) >= 0
    negative_mask = np.array(evs) < 0

    ax2.plot(multipliers, evs, color=COLORS['primary'], linewidth=2.5,
             marker='D', markersize=4, markevery=5, label='Expected Value')
    ax2.fill_between(multipliers, evs, 0, where=positive_mask,
                     alpha=0.3, color=COLORS['success'], label='Positive EV')
    ax2.fill_between(multipliers, evs, 0, where=negative_mask,
                     alpha=0.3, color=COLORS['warning'], label='Negative EV')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    ax2.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold')
    ax2.set_ylabel('Expected Value (¥)', fontweight='bold')
    ax2.set_title('(b) Expected Value vs. Credit Limit', fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(loc='upper left', framealpha=0.9)
    ax2.set_xlim(multipliers[0], multipliers[-1])

    # 标注最优点
    max_ev_idx = np.argmax(evs)
    max_ev = evs[max_ev_idx]
    max_multiplier = multipliers[max_ev_idx]
    ax2.scatter([max_multiplier], [max_ev], color=COLORS['accent'],
                s=150, zorder=5, marker='*', edgecolors='black', linewidths=1.5,
                label=f'Optimal (×{max_multiplier:.1f})')
    ax2.legend(loc='upper left', framealpha=0.9)

    plt.tight_layout()

    # 保存图表
    output_path = os.path.join(output_dir, 'ev_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 保存图表: {output_path}")
    plt.close()


def plot_monte_carlo_simulation(results, base_amount, output_dir, n_simulations=1000):
    """绘制EV的蒙特卡洛模拟散点图"""
    print(f"\n🎲 进行蒙特卡洛模拟 (n={n_simulations})...")

    # 从结果中提取数据用于模拟
    multipliers = np.array([r['multiplier'] for r in results])
    pds = np.array([float(np.array(r['pd']).item()) for r in results])
    velocities = np.array([float(np.array(r['velocity']).item()) for r in results])
    evs = np.array([float(r['ev']) for r in results])

    # 蒙特卡洛模拟：在每个额度附近添加随机扰动
    np.random.seed(42)  # 保证可重复性

    sim_multipliers = []
    sim_evs = []
    sim_pds = []

    for _ in range(n_simulations):
        # 随机选择一个基准点
        idx = np.random.randint(0, len(results))
        base_multiplier = multipliers[idx]
        base_ev = evs[idx]
        base_pd = pds[idx]

        # 添加随机扰动
        # 额度扰动: ±10%
        multiplier_noise = np.random.normal(0, 0.1)
        sim_multiplier = base_multiplier * (1 + multiplier_noise)

        # EV扰动: 基于PD的不确定性
        # PD的不确定性会影响EV
        pd_noise = np.random.normal(0, 0.02)  # PD ±2%
        ev_noise = np.random.normal(0, abs(base_ev) * 0.15)  # EV ±15%
        sim_ev = base_ev + ev_noise
        sim_pd = base_pd + pd_noise

        sim_multipliers.append(sim_multiplier)
        sim_evs.append(sim_ev)
        sim_pds.append(sim_pd * 100)  # 转换为百分比

    sim_multipliers = np.array(sim_multipliers)
    sim_evs = np.array(sim_evs)
    sim_pds = np.array(sim_pds)

    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # 图1: EV蒙特卡洛散点图（按PD着色）
    scatter1 = ax1.scatter(sim_multipliers, sim_evs, c=sim_pds,
                          cmap='RdYlGn_r', alpha=0.6, s=30, edgecolors='none')

    # 添加原始曲线
    ax1.plot(multipliers, evs, color='black', linewidth=2.5,
             linestyle='--', label='Deterministic EV', zorder=5)

    # 添加零线
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)

    ax1.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold')
    ax1.set_ylabel('Expected Value (¥)', fontweight='bold')
    ax1.set_title('(a) Monte Carlo Simulation of Expected Value', fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='upper left', framealpha=0.9)

    # 添加颜色条
    cbar1 = plt.colorbar(scatter1, ax=ax1)
    cbar1.set_label('Default Probability (%)', fontweight='bold')

    # 图2: EV分布直方图
    # 区分正负EV
    positive_evs = sim_evs[sim_evs >= 0]
    negative_evs = sim_evs[sim_evs < 0]

    ax2.hist(positive_evs, bins=40, color=COLORS['success'], alpha=0.7,
             label=f'Positive EV ({len(positive_evs)/len(sim_evs)*100:.1f}%)', edgecolor='black')
    ax2.hist(negative_evs, bins=40, color=COLORS['warning'], alpha=0.7,
             label=f'Negative EV ({len(negative_evs)/len(sim_evs)*100:.1f}%)', edgecolor='black')

    ax2.axvline(x=0, color='black', linestyle='-', linewidth=2, alpha=0.7)
    ax2.axvline(x=np.mean(sim_evs), color=COLORS['primary'], linestyle='--',
                linewidth=2, label=f'Mean EV (¥{np.mean(sim_evs):.0f})')

    ax2.set_xlabel('Expected Value (¥)', fontweight='bold')
    ax2.set_ylabel('Frequency', fontweight='bold')
    ax2.set_title('(b) Distribution of Expected Value', fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.legend(loc='upper right', framealpha=0.9)

    plt.tight_layout()

    # 保存图表
    output_path = os.path.join(output_dir, 'monte_carlo_simulation.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 保存图表: {output_path}")

    # 打印统计信息
    print(f"\n📊 蒙特卡洛模拟统计:")
    print(f"  总模拟次数: {n_simulations}")
    print(f"  正EV比例: {len(positive_evs)/len(sim_evs)*100:.1f}%")
    print(f"  负EV比例: {len(negative_evs)/len(sim_evs)*100:.1f}%")
    print(f"  平均EV: ¥{np.mean(sim_evs):,.2f}")
    print(f"  EV标准差: ¥{np.std(sim_evs):,.2f}")
    print(f"  EV范围: ¥{np.min(sim_evs):,.2f} - ¥{np.max(sim_evs):,.2f}")

    plt.close()


def plot_comprehensive_dashboard(results, base_amount, total_income, balance, output_dir):
    """绘制综合仪表板"""
    print("\n📊 绘制综合仪表板...")

    multipliers = np.array([r['multiplier'] for r in results])
    pds = np.array([float(np.array(r['pd']).item()) * 100 for r in results])
    velocities = np.array([float(np.array(r['velocity']).item()) * 100 for r in results])
    evs = np.array([float(r['ev']) for r in results])
    gmvs = np.array([float(r['gmv']) for r in results])

    # 创建2x2子图
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # 子图1: PD和周转率双轴图
    ax1 = fig.add_subplot(gs[0, :])
    ax1_twin = ax1.twinx()

    line1 = ax1.plot(multipliers, pds, color=COLORS['warning'], linewidth=2.5,
                     marker='o', markersize=5, markevery=5, label='Default Probability')
    line2 = ax1_twin.plot(multipliers, velocities, color=COLORS['primary'], linewidth=2.5,
                          marker='s', markersize=5, markevery=5, label='Velocity Rate')

    ax1.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold')
    ax1.set_ylabel('Default Probability (%)', fontweight='bold', color=COLORS['warning'])
    ax1_twin.set_ylabel('Velocity Rate (%)', fontweight='bold', color=COLORS['primary'])
    ax1.set_title('(a) Risk Metrics vs. Credit Limit', fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.tick_params(axis='y', labelcolor=COLORS['warning'])
    ax1_twin.tick_params(axis='y', labelcolor=COLORS['primary'])

    # 合并图例
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', framealpha=0.9)

    # 子图2: EV曲线
    ax2 = fig.add_subplot(gs[1, 0])

    positive_mask = evs >= 0
    negative_mask = evs < 0

    ax2.plot(multipliers, evs, color=COLORS['primary'], linewidth=2.5,
             marker='D', markersize=5, markevery=5)
    ax2.fill_between(multipliers, evs, 0, where=positive_mask,
                     alpha=0.3, color=COLORS['success'])
    ax2.fill_between(multipliers, evs, 0, where=negative_mask,
                     alpha=0.3, color=COLORS['warning'])
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)

    # 标注最优点
    max_ev_idx = np.argmax(evs)
    ax2.scatter([multipliers[max_ev_idx]], [evs[max_ev_idx]],
                color=COLORS['accent'], s=200, zorder=5, marker='*',
                edgecolors='black', linewidths=1.5)
    ax2.annotate(f'Optimal\n×{multipliers[max_ev_idx]:.1f}\n¥{evs[max_ev_idx]:.0f}',
                xy=(multipliers[max_ev_idx], evs[max_ev_idx]),
                xytext=(10, 20), textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['accent'], alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', lw=1.5))

    ax2.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold')
    ax2.set_ylabel('Expected Value (¥)', fontweight='bold')
    ax2.set_title('(b) Expected Value Curve', fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, linestyle='--')

    # 子图3: GMV分析
    ax3 = fig.add_subplot(gs[1, 1])

    ax3.plot(multipliers, gmvs, color=COLORS['success'], linewidth=2.5,
             marker='o', markersize=5, markevery=5)
    ax3.fill_between(multipliers, gmvs, alpha=0.2, color=COLORS['success'])
    ax3.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold')
    ax3.set_ylabel('Monthly GMV (¥)', fontweight='bold')
    ax3.set_title('(c) Transaction Volume vs. Credit Limit', fontweight='bold', pad=15)
    ax3.grid(True, alpha=0.3, linestyle='--')

    # 子图4: 关键指标热力图
    ax4 = fig.add_subplot(gs[2, :])

    # 选择关键倍数点
    key_indices = [int(i) for i in np.linspace(0, len(multipliers)-1, 10)]
    key_multipliers = multipliers[key_indices]
    key_pds = pds[key_indices]
    key_velocities = velocities[key_indices]
    key_evs = evs[key_indices]

    # 归一化数据用于热力图
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler()

    heatmap_data = np.array([
        scaler.fit_transform(key_pds.reshape(-1, 1)).flatten(),
        scaler.fit_transform(key_velocities.reshape(-1, 1)).flatten(),
        scaler.fit_transform(key_evs.reshape(-1, 1)).flatten(),
    ])

    im = ax4.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', alpha=0.8)

    ax4.set_xticks(range(len(key_multipliers)))
    ax4.set_xticklabels([f'{m:.1f}×' for m in key_multipliers])
    ax4.set_yticks(range(3))
    ax4.set_yticklabels(['PD', 'Velocity', 'EV'])
    ax4.set_xlabel('Credit Limit Multiplier', fontweight='bold')
    ax4.set_title('(d) Normalized Metrics Heatmap', fontweight='bold', pad=15)

    # 添加数值标注
    for i in range(3):
        for j in range(len(key_multipliers)):
            if i == 0:
                text = f'{key_pds[j]:.1f}%'
            elif i == 1:
                text = f'{key_velocities[j]:.1f}%'
            else:
                text = f'¥{key_evs[j]:.0f}'
            ax4.text(j, i, text, ha='center', va='center',
                    color='black', fontsize=8, fontweight='bold')

    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax4, orientation='horizontal', pad=0.1)
    cbar.set_label('Normalized Value', fontweight='bold')

    # 添加总标题
    fig.suptitle(f'Credit Limit Analysis Dashboard\nIncome: ¥{total_income:,.0f} | Balance: ¥{balance:,.0f}',
                fontsize=16, fontweight='bold', y=0.995)

    # 保存图表
    output_path = os.path.join(output_dir, 'comprehensive_dashboard.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 保存图表: {output_path}")
    plt.close()


def plot_ev_heatmap(results, base_amount, output_dir):
    """
    绘制EV热力图：X轴=额度倍数，Y轴=PD，格子颜色=EV值

    设计参考: Nature / Science 期刊配色, IEEE VIS 顶会标准
    """
    print("\n📊 绘制EV热力图...")

    # 提取原始数据
    multipliers = np.array([r['multiplier'] for r in results])
    pds = np.array([float(np.array(r['pd']).item()) * 100 for r in results])
    evs = np.array([float(r['ev']) for r in results])

    # 对数据进行分箱，得到12个关键点（1x到10x）
    target_mults = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

    # 找到最接近目标倍数的数据点
    data_points = []
    for tm in target_mults:
        idx = np.argmin(np.abs(multipliers - tm))
        data_points.append({
            'mult': multipliers[idx],
            'pd': pds[idx],
            'ev': evs[idx]
        })

    n_points = len(data_points)
    mult_labels = [f'{d["mult"]:.1f}×' for d in data_points]
    pd_vals = [d['pd'] for d in data_points]
    ev_vals = [d['ev'] for d in data_points]

    # ========== 构建热力图矩阵 ==========
    # 创建一个 n_points x 1 的矩阵，每行代表一个倍数
    ev_matrix = np.array(ev_vals).reshape(1, -1)

    # ========== 创建图表 ==========
    fig, ax = plt.subplots(figsize=(14, 6))

    # ========== 顶会级配色 ==========
    from matplotlib.colors import TwoSlopeNorm

    # 使用RdYlGn diverging colormap：红(负)->黄(0)->绿(正)
    cmap = plt.cm.RdYlGn

    # 设置颜色范围，以0为中心
    ev_min, ev_max = min(ev_vals), max(ev_vals)
    if ev_min < 0 and ev_max > 0:
        norm = TwoSlopeNorm(vmin=ev_min, vcenter=0, vmax=ev_max)
    else:
        norm = plt.Normalize(vmin=ev_min, vmax=ev_max)

    # 绘制热力图
    im = ax.imshow(ev_matrix, cmap=cmap, norm=norm, aspect='auto')

    # ========== 添加EV数值和PD标注 ==========
    for j in range(n_points):
        ev_val = ev_vals[j]
        pd_val = pd_vals[j]

        # EV数值（格子中央）
        text_color = 'white' if abs(ev_val) > 20 else 'black'
        ax.text(j, 0, f'¥{ev_val:.0f}', ha='center', va='center',
               fontsize=12, fontweight='bold', color=text_color)

    # ========== 坐标轴设置 ==========
    # X轴：倍数
    ax.set_xticks(range(n_points))
    ax.set_xticklabels(mult_labels, fontsize=11, fontweight='bold')
    ax.set_xlabel('Credit Limit Multiplier', fontweight='bold', fontsize=13)

    # Y轴：隐藏（只有一行）
    ax.set_yticks([])
    ax.set_ylabel('')

    # 在X轴下方添加PD值
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(range(n_points))
    ax2.set_xticklabels([f'{pd:.1f}%' for pd in pd_vals], fontsize=10, color='#666666')
    ax2.xaxis.set_ticks_position('bottom')
    ax2.xaxis.set_label_position('bottom')
    ax2.spines['bottom'].set_position(('outward', 25))
    ax2.set_xlabel('Default Probability (PD)', fontsize=11, color='#666666')

    # ========== 颜色条 ==========
    cbar = plt.colorbar(im, ax=ax, orientation='vertical', shrink=0.8, pad=0.02)
    cbar.set_label('Expected Value (EV, ¥)', fontweight='bold', fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    # ========== 标题 ==========
    ax.set_title('Expected Value Heatmap: Multiplier vs EV\n(Color indicates profitability: Green=Positive, Red=Negative)',
                 fontweight='bold', fontsize=14, pad=15)

    # ========== 标注最优点 ==========
    optimal_idx = np.argmax(ev_vals)
    # 添加红色边框
    rect = plt.Rectangle((optimal_idx - 0.5, -0.5), 1, 1,
                         fill=False, edgecolor='#e63946', linewidth=4, zorder=10)
    ax.add_patch(rect)

    plt.tight_layout()

    # 保存
    output_path = os.path.join(output_dir, 'ev_heatmap.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ 保存图表: {output_path}")
    plt.close()


def plot_pd_revenue_area(results, base_amount, output_dir):
    """
    绘制PD曲线 + Revenue面积填充图

    这是一个双轴图：
    - 左轴：PD曲线（折线）
    - 面积填充：表示Revenue区域
    - 颜色渐变：表示Revenue强度

    设计参考: IEEE TVCG, CHI 顶会图表风格
    """
    print("\n📊 绘制PD-Revenue面积填充图...")

    # 提取数据
    multipliers = np.array([r['multiplier'] for r in results])
    pds = np.array([float(np.array(r['pd']).item()) * 100 for r in results])
    revenues = np.array([float(r['total_revenue']) for r in results])
    evs = np.array([float(r['ev']) for r in results])
    credit_limits = np.array([float(r['credit_limit']) for r in results])

    # 找到最优点
    optimal_idx = np.argmax(evs)

    # 创建双轴图
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    # ========== 顶会级配色 ==========
    pd_color = '#c0392b'       # 深红色 - PD
    revenue_color = '#27ae60'  # 绿色 - Revenue
    fill_color = '#2ecc71'     # 浅绿色填充
    optimal_color = '#f39c12'  # 金色 - 最优点

    # ========== 绘制Revenue面积填充 ==========
    # 使用渐变填充效果
    ax2.fill_between(multipliers, 0, revenues, alpha=0.3, color=fill_color,
                     label='Expected Revenue Area')
    ax2.plot(multipliers, revenues, color=revenue_color, linewidth=2.5,
             linestyle='--', marker='s', markersize=5, markevery=3,
             label='Expected Revenue', zorder=3)

    # ========== 绘制PD曲线 ==========
    ax1.plot(multipliers, pds, color=pd_color, linewidth=3,
             marker='o', markersize=6, markevery=3,
             label='Default Probability', zorder=4)

    # ========== 标注最优点 ==========
    # 在PD曲线上标注
    ax1.scatter(multipliers[optimal_idx], pds[optimal_idx],
                s=200, c=optimal_color, edgecolors='white',
                linewidths=2, zorder=5, marker='*')

    # 添加垂直虚线
    ax1.axvline(x=multipliers[optimal_idx], color=optimal_color,
                linestyle=':', linewidth=2, alpha=0.7, zorder=2)

    # 添加注释
    ax1.annotate(f'Optimal Point\n({multipliers[optimal_idx]:.1f}×)',
                xy=(multipliers[optimal_idx], pds[optimal_idx]),
                xytext=(multipliers[optimal_idx] + 2, pds[optimal_idx] * 0.85),
                fontsize=10, fontweight='bold', color=optimal_color,
                arrowprops=dict(arrowstyle='->', color=optimal_color, lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                         edgecolor=optimal_color, alpha=0.9),
                zorder=6)

    # ========== 坐标轴设置 ==========
    ax1.set_xlabel('Credit Limit Multiplier (×)', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Default Probability (%)', fontweight='bold', fontsize=12, color=pd_color)
    ax2.set_ylabel('Expected Revenue (¥)', fontweight='bold', fontsize=12, color=revenue_color)

    # 刻度颜色
    ax1.tick_params(axis='y', labelcolor=pd_color)
    ax2.tick_params(axis='y', labelcolor=revenue_color)

    # 格式化Revenue轴刻度
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'¥{x:,.0f}'))

    # 网格
    ax1.grid(True, alpha=0.3, linestyle='--', zorder=1)
    ax1.set_axisbelow(True)

    # 坐标轴范围
    ax1.set_xlim(multipliers[0] - 0.3, multipliers[-1] + 0.3)
    ax1.set_ylim(0, max(pds) * 1.1)
    ax2.set_ylim(0, max(revenues) * 1.15)

    # ========== 合并图例 ==========
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc='upper left', framealpha=0.95, fontsize=10)

    # ========== 标题 ==========
    ax1.set_title('Default Probability and Expected Revenue vs. Credit Limit Multiplier',
                 fontweight='bold', fontsize=14, pad=15)

    # ========== 添加统计信息 ==========
    stats_text = (f"Optimal: {multipliers[optimal_idx]:.1f}× (¥{credit_limits[optimal_idx]:,.0f})\n"
                  f"PD at Optimal: {pds[optimal_idx]:.2f}%\n"
                  f"Revenue at Optimal: ¥{revenues[optimal_idx]:,.0f}\n"
                  f"Max EV: ¥{evs.max():,.0f}")

    props = dict(boxstyle='round,pad=0.4', facecolor='white',
                 edgecolor='#bdc3c7', alpha=0.95)
    ax1.text(0.98, 0.98, stats_text, transform=ax1.transAxes, fontsize=9,
             verticalalignment='top', horizontalalignment='right',
             bbox=props, family='monospace')

    plt.tight_layout()

    # 保存图表
    output_path = os.path.join(output_dir, 'pd_revenue_area.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ 保存图表: {output_path}")
    plt.close()


def main():
    """主函数"""
    setup_plot_style()

    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python credit_analysis_plots.py <PDF文件路径>")
        print("示例: python credit_analysis_plots.py uploads/pdfs/bank_statement.pdf")
        return

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return

    # 分析信用额度
    results, base_amount, total_income, balance, output_dir = analyze_credit_limits(pdf_path)

    # 生成所有图表
    print("\n" + "="*80)
    print("生成可视化图表")
    print("="*80)

    plot_pd_velocity_analysis(results, output_dir)
    plot_ev_analysis(results, output_dir)
    plot_monte_carlo_simulation(results, base_amount, output_dir, n_simulations=2000)
    plot_comprehensive_dashboard(results, base_amount, total_income, balance, output_dir)

    # 新增：EV热力图和PD-Revenue可视化图表
    plot_ev_heatmap(results, base_amount, output_dir)
    plot_pd_revenue_area(results, base_amount, output_dir)

    print("\n" + "="*80)
    print("✅ 所有图表生成完成！")
    print(f"📁 输出目录: {output_dir}")
    print("="*80)

    # 列出生成的文件
    print("\n生成的图表:")
    for filename in sorted(os.listdir(output_dir)):
        if filename.endswith('.png'):
            filepath = os.path.join(output_dir, filename)
            filesize = os.path.getsize(filepath) / 1024  # KB
            print(f"  ✓ {filename} ({filesize:.1f} KB)")


if __name__ == "__main__":
    main()

