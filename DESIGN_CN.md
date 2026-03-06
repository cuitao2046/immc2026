# CPI (保护优先指数) 模块设计文档

## 概述

本模块计算保护区内野生动物监测设备布置的保护优先指数（CPI, Conservation Priority Index）。它综合了生态因素、火灾风险、通行时间和物种重要性来确定监测位置的优先级。

## 架构

```
cpi.py
├── 几何工具
├── 最小外接圆
├── 火灾风险模型
├── 最短路径 (Dijkstra)
├── CPI 计算
└── 示例流程
```

## 模块详解

### 1. 基础几何工具 (`dms_to_decimal`、`point_in_polygon`、`dist2`)

**用途**：处理坐标转换和空间查询。

| 函数 | 描述 |
|------|------|
| `dms_to_decimal()` | 将 DMS（度-分-秒）格式（如 `19°26'55.93"S`）转换为十进制度数 |
| `point_in_polygon()` | 射线投射算法测试点是否在多边形内 |
| `dist2()` | 两点间欧氏距离的平方（为了效率） |

### 2. 最小外接圆 (`minimum_enclosing_circle`)

**用途**：计算包围一组点的最小圆（用于火险四边形）。

| 函数 | 描述 |
|------|------|
| `_circle_from_2_points()` | 由直径端点确定的圆 |
| `_circle_from_3_points()` | 三角形的外接圆（共线时返回 None） |
| `_is_in_circle()` | 测试点是否在圆内 |
| `minimum_enclosing_circle()` | Welzl 随机算法（期望 O(n) 时间复杂度） |

### 3. 火灾风险模型 (`build_fire_risk_function`)

**用途**：从火险四边形创建空间火灾风险函数。

**配置项**：
- `combine`：`"max"`（取最大风险）或 `"sum"`（风险求和）
- `radial_mode`：`"linear"`（中心为 1，边缘为 0）或 `"gaussian"`（指数衰减）
- `gaussian_alpha`：控制高斯分布的扩散（越小越陡）

**返回**：函数 `fire_risk(lon, lat) → [0,1]`

### 4. 最短路径通行时间 (`dijkstra_multi_source`)

**用途**：计算从多个源节点（营地）穿越地形的最短通行时间。

| 参数 | 类型 | 描述 |
|------|------|------|
| `nodes` | `List[int]` | 所有单元格 ID |
| `neighbors` | `Dict[int, List[int]]` | 邻接表 |
| `terrain_cost` | `Dict[int, float]` | 进入每个节点的成本 |
| `sources` | `List[int]` | 源节点 ID（营地） |
| `blocked` | `Callable[[int], bool]` | 可选的不可通行节点测试 |

**返回**：`Dict[int, float]` - 从最近源点到每个节点的通行时间

### 5. CPI 计算 (`compute_cpi_for_cell`)

**用途**：单个单元格、物种和设备类型的核心 CPI 公式。

**公式**：
```
CPI = (D + (1 - D) * η * S) * W_i - Φ - γ_fire
```

| 符号 | 含义 | 来源 |
|------|------|------|
| D | 威慑效果 | `params["D_device"]`（无设备时为 0） |
| η | 核实有效性 | `eta_camera` 或 `eta_uav` |
| S | 存活概率 | `exp(-λ * T_c)` |
| λ | 存活衰减率 | `params["lambda"]` |
| T_c | 到单元格的通行时间 | `precomp["T_c"][cell_id]` |
| W_i | 物种权重 | `params["W"][species_id]` |
| Φ | 生态惩罚 | 敏感区且有设备时为 `eco_penalty` |
| γ_fire | 火灾惩罚 | `gamma_max * fire_risk` |

### 6. 端到端流程 (`build_and_compute_example`)

**用途**：完整工作流程的演示。

步骤：
1. 定义公园边界（DMS → 十进制度数）
2. 定义火险四边形
3. 构建火灾风险函数
4. 定义单元格网格、邻接关系、地形成本
5. 计算从营地出发的通行时间
6. 组装预计算映射
7. 设置参数
8. 计算所有单元格-物种-设备组合的 CPI

## 数据流

```
公园边界 ──┐
           ├──> 火灾风险函数 ──> 火灾惩罚
火险四边形 ──┘

单元格 ──┐
         ├──> Dijkstra ──> 通行时间 (T_c) ──> 存活率 (S)
地形 ────┘
营地 ────┘

物种权重 ──┐
生态敏感区 ──├──> CPI 计算
火灾惩罚 ────┘
通行时间 ─────┘
设备类型 ─────┘
```

## 参数

| 参数 | 类型 | 典型值 | 描述 |
|------|------|--------|------|
| `lambda` | float | 0.4 | 存活衰减率 |
| `D_device` | float | 0.8 | 设备存在时的威慑效果 |
| `eta_camera` | float | 0.5 | 核实有效性（相机） |
| `eta_uav` | float | 1.0 | 核实有效性（无人机） |
| `eco_penalty` | float | 50.0 | 在敏感区布置设备的惩罚 |
| `W` | dict | `{"rhino": 10.0, "elephant": 2.0}` | 物种重要性权重 |
| `W_base` | float | 0.5 | 非栖息地单元格的基准权重 |
| `gamma_max` | float | 20.0 | 最大火灾惩罚 |

## 扩展点

1. **替代风险模型**：替换 `build_fire_risk_function()` 为自定义实现
2. **不同路径规划**：替换 `dijkstra_multi_source()` 为 A* 或其他算法
3. **额外惩罚**：在 `compute_cpi_for_cell()` 中扩展 CPI 公式添加更多项
4. **优化**：在 `precomp` 字典中预计算更多值用于重复 CPI 计算

## 依赖

- 仅 Python 标准库：`math`、`random`、`heapq`、`typing`
