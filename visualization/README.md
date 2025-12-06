# 信用额度分析可视化

本目录包含信用额度预测系统的高质量可视化工具和输出图表。

## 📊 生成的图表

### 1. PD和周转率分析图 (`pd_velocity_analysis.png`)
**内容**：
- **(a) Default Probability vs. Credit Limit**: 违约概率随信用额度的变化
- **(b) Velocity Rate vs. Credit Limit**: 周转率随信用额度的变化

**关键发现**：
- 违约概率随额度增加而上升（杠杆效应）
- 周转率随额度增加而下降（用户用不完大额度）
- 两者共同决定了最优额度

---

### 2. EV分析图 (`ev_analysis.png`)
**内容**：
- **(a) Revenue and Cost vs. Credit Limit**: 收入和成本随额度的变化
- **(b) Expected Value vs. Credit Limit**: 预期价值曲线

**关键发现**：
- 收入随额度增加而增长（但增速放缓）
- 成本随额度增加而加速增长
- EV曲线呈现倒U型，存在最优额度点
- 标注了最优额度位置（星号标记）

---

### 3. 蒙特卡洛模拟图 (`monte_carlo_simulation.png`)
**内容**：
- **(a) Monte Carlo Simulation of Expected Value**: EV的蒙特卡洛散点图（按PD着色）
- **(b) Distribution of Expected Value**: EV的分布直方图

**关键发现**：
- 模拟了2000次随机场景
- 散点颜色表示违约概率（红色=高风险，绿色=低风险）
- 直方图显示EV的分布特征
- 统计信息：正EV比例、平均EV、标准差等

---

### 4. 综合仪表板 (`comprehensive_dashboard.png`)
**内容**：
- **(a) Risk Metrics vs. Credit Limit**: PD和周转率双轴图
- **(b) Expected Value Curve**: EV曲线（标注最优点）
- **(c) Transaction Volume vs. Credit Limit**: GMV随额度变化
- **(d) Normalized Metrics Heatmap**: 关键指标热力图

**关键发现**：
- 一页纸展示所有关键指标
- 热力图直观对比不同额度下的表现
- 适合用于报告和演示

---

## 🎨 设计特点

### 科研级别配色
- **主色调**: 深蓝色 (#2E86AB) - 专业、可信
- **强调色**: 橙色 (#F18F01) - 突出重点
- **成功色**: 绿色 (#06A77D) - 正向指标
- **警告色**: 红色 (#D62246) - 风险指标

### 符合顶会标准
- ✅ 使用Times New Roman字体
- ✅ 300 DPI高分辨率
- ✅ 清晰的轴标签和标题
- ✅ 适当的网格线和图例
- ✅ 专业的配色方案
- ✅ 标准化的子图标注 (a), (b), (c), (d)

---

## 🚀 使用方法

### 基本用法
```bash
python visualization/credit_analysis_plots.py <PDF文件路径>
```

### 示例
```bash
python visualization/credit_analysis_plots.py uploads/pdfs/bank_statement_20251204232322.pdf
```

### 输出
所有图表将保存在 `visualization/outputs/` 目录下。

---

## 📈 技术细节

### 候选额度生成
- 基于用户余额生成50个候选额度
- 倍数范围：0.5x - 15x
- 使用线性插值确保平滑曲线

### 蒙特卡洛模拟
- 模拟次数：2000次
- 随机扰动：
  - 额度：±10%
  - PD：±2%
  - EV：±15%
- 随机种子：42（可重复）

### 数据处理
- 所有百分比指标转换为0-100范围
- 使用NumPy数组确保数值稳定性
- 自动处理标量/数组类型转换

---

## 📊 统计信息示例

```
蒙特卡洛模拟统计:
  总模拟次数: 2000
  正EV比例: 100.0%
  负EV比例: 0.0%
  平均EV: ¥3,508.07
  EV标准差: ¥1,496.90
  EV范围: ¥259.76 - ¥6,955.70
```

---

## 🔧 依赖项

- `numpy`: 数值计算
- `matplotlib`: 绘图
- `seaborn`: 高级可视化
- `sklearn`: 数据归一化（热力图）

---

## 📝 注意事项

1. **图表质量**: 所有图表均为300 DPI，适合论文发表
2. **文件大小**: 每个图表约200-700 KB
3. **颜色盲友好**: 使用了对比度高的配色方案
4. **可定制**: 可以修改 `COLORS` 字典来调整配色

---

## 🎯 适用场景

- ✅ 学术论文插图
- ✅ 技术报告
- ✅ 业务演示
- ✅ 模型分析
- ✅ 风险评估报告

---

## 📧 联系方式

如有问题或建议，请联系开发团队。

