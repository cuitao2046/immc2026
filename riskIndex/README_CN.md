# 保护区网格风险指数模型

一个用于计算野生动物保护区风险系数的综合数学模型，用于指导巡逻和监控资源的最优分配。

## 功能特性

- **核心风险模型**：人为风险、环境风险、物种密度计算
- **时间因素**：昼夜和季节风险变化
- **自动距离计算**：从网格坐标自动计算距离
- **时空风险场**：跨空间和时间的连续插值
- **DSSA算法**：用于巡逻优化的无人机群调度算法
- **可视化**：风险热力图、组件分析和时间对比
- **数据生成**：用于测试和验证的合成数据
- **Wrapper脚本**：基于JSON的配置和数据文件输入输出

## 项目结构

```
riskIndex/
├── src/risk_model/
│   ├── core/              # 核心数据结构
│   ├── risk/              # 风险计算器
│   ├── data/              # 数据生成和输入输出
│   ├── config/            # 配置管理
│   ├── visualization/     # 绘图和可视化
│   └── advanced/          # IMMC增强功能
├── tests/                 # 单元测试
├── examples/              # 示例脚本
├── plots/                 # 生成的图表
├── demo_phase*.py         # 阶段演示脚本
├── risk_model_wrapper.py   # JSON文件输入输出的Wrapper脚本
├── example_data.json     # 示例输入数据
├── example_config.json   # 示例配置
└── example_results.json  # 示例输出结果
```

## 快速开始

### 使用Wrapper脚本

```bash
# 使用示例数据运行
python3 risk_model_wrapper.py --data example_data.json --config example_config.json --output results.json
```

### 运行所有演示

```bash
# 阶段1：核心模型实现
python3 demo_phase1.py

# 阶段2：风险整合与归一化
python3 demo_phase2.py

# 阶段3：数据生成与输入输出
python3 demo_phase3.py

# 阶段4：可视化
python3 demo_phase4.py

# 阶段5：测试与验证
python3 demo_phase5.py

# 阶段6：高级特性（IMMC增强）
python3 demo_phase6.py
```

## 坐标系

模型使用基于网格的坐标系：
- **原点**：左下角网格单元中心
- **X轴**：向右增大（列索引）
- **Y轴**：向上增大（行索引）
- **距离计算**：使用欧氏距离进行自动距离计算

## Wrapper脚本使用

### 输入数据格式（`data.json`）

```json
{
  "map_config": {
    "map_width": 10,
    "map_height": 6,
    "boundary_type": "RECTANGLE",
    "road_locations": [[2, 3], [5, 7]],
    "water_locations": [[1, 1], [8, 5]]
  },
  "grids": [
    {
      "grid_id": "A01",
      "x": 0,
      "y": 0,
      "fire_risk": 0.8,
      "terrain_complexity": 0.7,
      "vegetation_type": "FOREST",
      "species_densities": {
        "rhino": 0.9,
        "elephant": 0.7,
        "bird": 0.5
      }
    }
  ],
  "time": {
    "hour_of_day": 22,
    "season": "RAINY"
  }
}
```

### 配置格式（`config.json`）

```json
{
  "risk_weights": {
    "human_weight": 0.4,
    "environmental_weight": 0.3,
    "density_weight": 0.3
  },
  "human_risk_weights": {
    "boundary_weight": 0.4,
    "road_weight": 0.35,
    "water_weight": 0.25
  },
  "environmental_risk_weights": {
    "fire_weight": 0.6,
    "terrain_weight": 0.4
  }
}
```

## 模型概述

### 风险公式

```
R'_{i,t} = (ω₁·H_{i,t} + ω₂·E_i + ω₃·Σ_s w_s·D_{s,i,t}) × T_t × S_t

R_i = (R'_{i,t} - R_min) / (R_max - R_min)
```

### 组件

| 组件 | 描述 |
|------|------|
| H_{i,t} | 人为风险（边界/道路/水源邻近度） |
| E_i | 环境风险（火灾 + 地形复杂度） |
| D_{s,i,t} | 加权物种密度 |
| T_t | 昼夜因子（白天/黑夜） |
| S_t | 季节因子（旱季/雨季） |

## IMMC竞赛增强功能

### 1. 时空风险场

使用高斯或IDW核进行连续风险插值：

```python
from risk_model.advanced import SpatioTemporalRiskField

risk_field = SpatioTemporalRiskField(grids, risk_results)
risk = risk_field.get_risk_at(x=50, y=50, t=2, season=Season.RAINY)
```

### 2. DSSA算法（无人机群调度）

用于最优巡逻调度的伪代码和实现。完整的IMMC格式算法请参见`risk_model/advanced/dssa.py`。

### 3. 完整工作流程

```
生成数据 → 计算风险 → 构建风险场 → 优化巡逻 → 可视化
```

## 依赖要求

- Python 3.8+
- numpy
- matplotlib

## 开发阶段

| 阶段 | 状态 | 演示 |
|------|------|------|
| 1. 核心模型实现 | ✅ | `demo_phase1.py` |
| 2. 风险整合与归一化 | ✅ | `demo_phase2.py` |
| 3. 数据生成与输入输出 | ✅ | `demo_phase3.py` |
| 4. 可视化 | ✅ | `demo_phase4.py` |
| 5. 测试与验证 | ✅ | `demo_phase5.py` |
| 6. IMMC高级特性 | ✅ | `demo_phase6.py` |

## 许可证

供IMMC竞赛使用。
