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
- **地图生成**：正方形和六边形网格地图生成器，包含道路和水源
- **热力图可视化**：从wrapper输出生成风险热力图

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
├── demo_phase*.py              # 阶段演示脚本
├── risk_model_wrapper.py        # JSON文件输入输出的Wrapper脚本
├── generate_hex_map.py          # 六边形网格地图生成器
├── generate_square_map.py       # 正方形网格地图生成器
├── visualize_risk_from_json.py  # 风险热力图可视化工具
├── example_data.json            # 示例输入数据
├── example_config.json          # 示例配置
└── example_results.json         # 示例输出结果
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

## 六边形网格地图生成器

生成矩形边界的六边形网格地图，包含弯曲道路和水源特征。

### 基本用法

```bash
# 使用默认设置生成地图（15列 × 12行）
python3 generate_hex_map.py
```

### 命令行参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--cols` | `-c` | 15 | 六边形网格列数 |
| `--rows` | `-r` | 12 | 六边形网格行数 |
| `--data` | `-d` | rect_hex_map_data.json | 输出JSON数据文件路径 |
| `--map-image` | `-m` | rect_hex_map_features.jpg | 输出地图特征图路径 |
| `--help` | `-h` | - | 显示帮助信息 |

### 使用示例

```bash
# 显示帮助
python3 generate_hex_map.py --help

# 生成20列×15行的地图
python3 generate_hex_map.py --cols 20 --rows 15

# 自定义输出文件名
python3 generate_hex_map.py --cols 25 --rows 18 --data my_map.json --map-image my_map.jpg

# 使用简写参数
python3 generate_hex_map.py -c 20 -r 15 -d output.json
```

### 特性

- **矩形边界**：六边形网格具有矩形外边界
- **弯曲道路**：随机游走生成的道路，支持分支
- **水源特征**：池塘 + 蜿蜒河流
- **无网格边框**：隐藏六边形边框（linewidth=0）
- **Even-Q偏移坐标**：使用偏移坐标实现矩形网格布局

## 正方形网格地图生成器

生成正方形网格地图，包含弯曲道路和水源特征。

### 基本用法

```bash
# 使用默认设置生成地图（40列 × 30行）
python3 generate_square_map.py
```

### 命令行参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--cols` | `-c` | 40 | 正方形网格列数 |
| `--rows` | `-r` | 30 | 正方形网格行数 |
| `--data` | `-d` | square_map_data.json | 输出JSON数据文件路径 |
| `--map-image` | `-m` | square_map_features.jpg | 输出地图特征图路径 |
| `--risk-image` | `-k` | square_map_risk.jpg | 输出风险热力图路径 |
| `--help` | `-h` | - | 显示帮助信息 |

### 使用示例

```bash
# 显示帮助
python3 generate_square_map.py --help

# 生成50列×25行的地图
python3 generate_square_map.py --cols 50 --rows 25

# 自定义输出文件名
python3 generate_square_map.py --cols 100 --rows 50 --data my_map.json --map-image my_map.jpg
```

## 完整工作流程：地图生成→风险计算→热力图绘制

这是从零开始生成风险热力图的推荐工作流程。

### 第1步：生成地图数据

选择正方形或六边形网格：

```bash
# 正方形网格地图（100×50）
python3 generate_square_map.py --cols 100 --rows 50 --data map_data.json

# 或 六边形网格地图（100×50）
python3 generate_hex_map.py --cols 100 --rows 50 --data map_data.json
```

### 第2步：转换为Wrapper格式（如需要）

地图生成器输出使用`num_cols`/`num_rows`，而wrapper期望使用`map_width`/`map_height`。如需转换：

```python
import json

with open('map_data.json', 'r') as f:
    data = json.load(f)

map_config = data['map_config']
map_config['map_width'] = map_config.pop('num_cols')
map_config['map_height'] = map_config.pop('num_rows')

for grid in data['grids']:
    if 'x' not in grid:
        grid['x'] = grid.get('hex_col', 0)
    if 'y' not in grid:
        grid['y'] = grid.get('hex_row', 0)

with open('map_for_wrapper.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### 第3步：使用Wrapper计算风险

```bash
python3 risk_model_wrapper.py \
    --data map_for_wrapper.json \
    --output risk_results.json
```

### 第4步：生成风险热力图

```bash
# 正方形网格热力图（默认）
python3 visualize_risk_from_json.py \
    --results risk_results.json \
    --input map_for_wrapper.json \
    --output risk_heatmap.jpg \
    --grid-type square

# 或 六边形网格热力图
python3 visualize_risk_from_json.py \
    --results risk_results.json \
    --input map_for_wrapper.json \
    --output risk_heatmap.jpg \
    --grid-type hex
```

## 风险热力图可视化工具

从wrapper脚本输出生成风险热力图。支持正方形和六边形网格。

### 基本用法

```bash
# 使用默认设置生成热力图（正方形网格，无特征叠加）
python3 visualize_risk_from_json.py --results results.json
```

### 命令行参数

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--results` | `-r` | 必填 | 风险结果JSON文件路径 |
| `--input` | `-i` | None | 可选的输入数据JSON路径（用于道路/水源叠加） |
| `--output` | `-o` | risk_heatmap_from_json.jpg | 输出热力图路径 |
| `--grid-type` | `-g` | square | 网格类型：'square' 或 'hex' |
| `--show-labels` | - | True | 显示风险值标签 |
| `--no-labels` | - | - | 隐藏风险值标签 |
| `--show-features` | - | False | 显示道路/水源特征叠加 |
| `--no-features` | - | - | 隐藏道路/水源特征叠加（默认） |

### 使用示例

```bash
# 显示帮助
python3 visualize_risk_from_json.py --help

# 基本正方形网格热力图
python3 visualize_risk_from_json.py --results results.json --output heatmap.jpg

# 六边形网格热力图
python3 visualize_risk_from_json.py --results results.json --grid-type hex --output hex_heatmap.jpg

# 带道路/水源特征叠加
python3 visualize_risk_from_json.py --results results.json --input data.json --show-features

# 完整选项：六边形网格、带特征、无标签
python3 visualize_risk_from_json.py \
    --results results.json \
    --input data.json \
    --output full_heatmap.jpg \
    --grid-type hex \
    --show-features \
    --no-labels
```

### 功能特性

- **双网格支持**：正方形和六边形（even-q偏移）网格
- **对比度优化标签**：自动选择黑色/白色文本以获得最佳可读性
- **动态字体大小**：根据网格数量自动调整字体大小
- **大网格优化**：超过500个网格时自动禁用标签
- **无边框**：网格单元无边框，呈现无缝外观

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
