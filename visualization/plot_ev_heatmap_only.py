#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EV双Y轴图表绘制脚本
X轴=额度倍数，左Y轴=PD违约概率，右Y轴=EV期望值
设计参考: Nature / Science 期刊配色
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置绘图风格
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['Times New Roman']
rcParams['font.size'] = 11
rcParams['figure.dpi'] = 300
rcParams['savefig.dpi'] = 300

# 使用用户提供的数据
data = [
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

# 提取数据
mult_vals = np.array([d['mult'] for d in data])
pd_vals = np.array([d['pd'] for d in data])
ev_vals = np.array([d['ev'] for d in data])

# 找到最优点
optimal_idx = np.argmax(ev_vals)

# 使用索引位置而不是实际倍数值，确保间距均匀
x_positions = np.arange(len(data))

# ========== 创建图表 ==========
fig, ax1 = plt.subplots(figsize=(14, 7))

# ========== 左Y轴：PD (折线图) ==========
color_pd = '#3498db'  # 蓝色
ax1.set_xlabel('Credit Limit Multiplier', fontweight='bold', fontsize=14)
ax1.set_ylabel('Default Probability (PD, %)', fontweight='bold', fontsize=14, color=color_pd)
line_pd = ax1.plot(x_positions, pd_vals, color=color_pd, linewidth=2.5,
                   marker='o', markersize=8, label='PD', alpha=0.8)
ax1.tick_params(axis='y', labelcolor=color_pd, labelsize=11)
ax1.tick_params(axis='x', labelsize=11)
ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)

# ========== 右Y轴：EV (柱状图) ==========
ax2 = ax1.twinx()
color_ev_pos = '#27ae60'  # 绿色（正值）
color_ev_neg = '#e74c3c'  # 红色（负值）

ax2.set_ylabel('Expected Value (EV, ¥)', fontweight='bold', fontsize=14, color='#2c3e50')

# 根据EV正负使用不同颜色
colors = [color_ev_pos if ev >= 0 else color_ev_neg for ev in ev_vals]
bars = ax2.bar(x_positions, ev_vals, width=0.6, color=colors, alpha=0.85,
               edgecolor='white', linewidth=1.5, label='EV')

# 在柱子上方标注数值（调整位置避免超出范围）
for i, ev in enumerate(ev_vals):
    if ev >= 0:
        y_offset = 1.5
        va = 'bottom'
    else:
        y_offset = -1.5
        va = 'top'
    ax2.text(x_positions[i], ev + y_offset, f'¥{ev}', ha='center', va=va,
            fontsize=9, fontweight='bold', color='#2c3e50')

ax2.tick_params(axis='y', labelcolor='#2c3e50', labelsize=11)
ax2.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.3)

# 设置Y轴范围，确保标注不超出
ev_min_val, ev_max_val = ev_vals.min(), ev_vals.max()
y_margin = max(abs(ev_min_val), abs(ev_max_val)) * 0.15
ax2.set_ylim(ev_min_val - y_margin, ev_max_val + y_margin)

# ========== 标注最优点 ==========
# 在PD线上标注最优点
ax1.plot(x_positions[optimal_idx], pd_vals[optimal_idx], marker='*',
        markersize=20, color='#e63946', markeredgecolor='white',
        markeredgewidth=2, zorder=10)

# 在EV柱上标注最优点（红色边框）
bars[optimal_idx].set_edgecolor('#e63946')
bars[optimal_idx].set_linewidth(3.5)

# ========== X轴设置 ==========
ax1.set_xticks(x_positions)
ax1.set_xticklabels([f'{m:.1f}×' for m in mult_vals], fontsize=11)
ax1.set_xlim(-0.5, len(data) - 0.5)

# ========== 标题 ==========
fig.suptitle('Credit Limit Analysis: Multiplier vs PD & EV',
            fontweight='bold', fontsize=15, y=0.97)

# ========== 图例 ==========
# 添加自定义图例项
from matplotlib.patches import Patch
legend_elements = [
    plt.Line2D([0], [0], color=color_pd, linewidth=2.5, marker='o',
               markersize=8, label='Default Probability (PD)'),
    Patch(facecolor=color_ev_pos, edgecolor='white', label='Positive EV'),
    Patch(facecolor=color_ev_neg, edgecolor='white', label='Negative EV'),
    plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#e63946',
               markersize=15, markeredgecolor='white', markeredgewidth=2,
               label=f'Optimal Point ({mult_vals[optimal_idx]:.1f}×)')
]

# 将图例放在右上角偏左，增加透明度避免遮挡
ax1.legend(handles=legend_elements, loc='upper right', fontsize=10,
          framealpha=0.85, edgecolor='#bdc3c7', ncol=2,
          bbox_to_anchor=(0.98, 0.98))

plt.tight_layout()

# 保存
os.makedirs('visualization/outputs', exist_ok=True)
output_path = 'visualization/outputs/ev_heatmap.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
print(f'✓ 已保存双Y轴图表: {output_path}')
print(f'  - X轴: 倍数 (1.0× - 10.0×)')
print(f'  - 左Y轴: PD违约概率 (蓝色折线)')
print(f'  - 右Y轴: EV期望值 (绿/红柱状图)')
print(f'  - 最优点: {mult_vals[optimal_idx]:.1f}× @ PD {pd_vals[optimal_idx]:.2f}%, EV=¥{ev_vals[optimal_idx]}')
plt.close()

