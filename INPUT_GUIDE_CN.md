# 输入数据指南

## 目录
1. [坐标格式](#坐标格式)
2. [公园边界](#公园边界)
3. [火险四边形](#火险四边形)
4. [单元格网格数据](#单元格网格数据)
5. [图结构](#图结构)
6. [地形成本](#地形成本)
7. [预计算映射](#预计算映射)
8. [参数](#参数)
9. [完整输入示例](#完整输入示例)

---

## 坐标格式

### DMS 格式（度-分-秒）
用于公园边界输入。

**类型**：`str`

**格式**：`{度}°{分}'{秒}"{方向}`

**示例**：
```python
"19°26'55.93\"S"   # 南纬
"14°24'43.35\"E"   # 东经
```

**方向**：
- 纬度：`N`（正），`S`（负）
- 经度：`E`（正），`W`（负）

### 十进制度数
内部使用，也用于火险四边形。

**类型**：`Tuple[float, float]`

**格式**：`(经度, 纬度)`

**示例**：
```python
(16.595, -18.834)   # (经度, 纬度)
(14.41204167, -19.44886944)  # 从 DMS 转换而来
```

---

## 公园边界

**函数参数**：`park_boundary`

**类型**：`List[Tuple[float, float]]`

**描述**：定义保护区边界的多边形。

**要求**：
- 必须是简单（非自相交）多边形
- 顶点按顺时针或逆时针排列
- 十进制度数坐标（经度，纬度）
- 起点和终点可以相同也可以不同（自动闭合）

**示例**：
```python
park_boundary = [
    (14.412042, -19.448869),   # 角点 1: 14°24'43.35"E, 19°26'55.93"S
    (14.262811, -18.616883),   # 角点 2: 14°15'46.12"E, 18°37'00.78"S
    (17.149883, -18.485992),   # 角点 3: 17°08'59.58"E, 18°29'09.57"S
    (17.109472, -19.325883),   # 角点 4: 17°06'34.10"E, 19°19'33.18"S
]
```

**从 DMS 转换**：
```python
from cpi import dms_to_decimal

park_boundary = [
    (dms_to_decimal("14°24'43.35\"E"), dms_to_decimal("19°26'55.93\"S")),
    (dms_to_decimal("14°15'46.12\"E"), dms_to_decimal("18°37'00.78\"S")),
    (dms_to_decimal("17°08'59.58\"E"), dms_to_decimal("18°29'09.57\"S")),
    (dms_to_decimal("17°06'34.10\"E"), dms_to_decimal("19°19'33.18\"S")),
]
```

---

## 火险四边形

**函数参数**：`fire_quads`

**类型**：`List[List[Tuple[float, float]]]`

**描述**：定义火灾风险区域的四边形列表。每个四边形被转换为其最小外接圆。

**要求**：
- 每个四边形恰好有 4 个顶点
- 十进制度数坐标（经度，纬度）
- 可以是凸的或凹的

**示例**：
```python
fire_quads = [
    # 火险区 1
    [
        (16.595, -18.834),
        (17.116, -18.832),
        (16.552, -19.084),
        (17.093, -19.145)
    ],
    # 火险区 2
    [
        (15.482, -19.289),
        (15.875, -19.310),
        (15.879, -19.114),
        (15.515, -19.140)
    ]
]
```

**注意**：如果只有一个火险区，仍然要用列表包裹：`[quad1]`

---

## 单元格网格数据

### 单元格字典

**类型**：`Dict[int, Dict[str, Any]]`

**描述**：将单元格 ID 映射到其属性。

**结构**：
```python
cells = {
    cell_id: {
        "lon": float,           # 十进制度数经度
        "lat": float,           # 十进制度数纬度
        "terrain": str,         # 地形类型键（见地形成本）
        # 可选附加字段：
        "habitat": Dict[str, bool],  # 物种栖息地存在
        "eco_sensitive": bool,       # 生态敏感区标志
    },
    ...
}
```

**982 个六边形单元格示例**：
```python
cells = {
    1: {"lon": 16.7, "lat": -18.95, "terrain": "road"},
    2: {"lon": 15.7, "lat": -19.2, "terrain": "grass"},
    3: {"lon": 16.2, "lat": -18.6, "terrain": "grass"},
    # ... 直到 cell_id 982
}
```

---

## 图结构

### 邻接表

**类型**：`Dict[int, List[int]]`

**描述**：定义哪些单元格相邻（可以在它们之间移动）。

**示例（六边形网格）**：
```python
neighbors = {
    1: [2, 3, 7, 8, 9, 10],      # 单元格 1 有 6 个邻居
    2: [1, 3, 4, 11, 12, 13],    # 单元格 2 有 6 个邻居
    3: [1, 2, 4, 5, 6, 7],        # 等等
    # ...
}
```

**对于结构统一的网格**：
```python
# 如果单元格形成网格，可以通过编程方式生成邻居
# neighbors = generate_hex_neighbors(num_cells=982)
```

---

## 地形成本

### 地形权值字典

**类型**：`Dict[str, float]`

**描述**：将地形类型名称映射到通行成本（时间单位）。

**特殊值**：
- `float("inf")` - 不可通行地形（无法进入）
- `1.0` - 最快（如道路）
- 值越高 = 越慢

**示例**：
```python
terrain_weight = {
    "road": 1.0,           # 道路上移动快
    "grass": 3.0,          # 草地较慢
    "forest": 5.0,         # 密林
    "swamp": float("inf"), # 不可通行
    "river": float("inf"),
}
```

### 每单元格地形成本

**类型**：`Dict[int, float]`

**描述**：直接将单元格 ID 映射到地形成本（从上面推导而来）。

**示例**：
```python
terrain_cost = {
    1: 1.0,     # 道路
    2: 3.0,     # 草地
    3: 5.0,     # 森林
    4: float("inf"),  # 沼泽
    # ...
}
```

**如何构建**：
```python
terrain_cost = {
    cell_id: terrain_weight[cells[cell_id]["terrain"]]
    for cell_id in cells
}
```

---

## 预计算映射

**类型**：`Dict[str, Any]`

**描述**：用于在 CPI 计算中重复使用的预计算值容器。

### 结构

```python
precomp = {
    # 必需字段：
    "T_c": Dict[int, float],              # 从最近营地的通行时间
    "eco_sensitive": Dict[int, bool],     # 单元格是否是生态敏感区？
    "fire_penalty": Dict[int, float],     # 每单元格火灾惩罚值
    "species_active": Dict[str, Dict[int, bool]],  # 每单元格物种栖息地

    # 可选附加：
    "fire_risk": Dict[int, float],        # 原始火灾风险 [0,1]
    "cell_lon": Dict[int, float],         # 每单元格经度
    "cell_lat": Dict[int, float],         # 每单元格纬度
}
```

### 字段详情

#### 1. `T_c` - 通行时间
**类型**：`Dict[int, float]`

**含义**：从最近营地（源节点）到每个单元格的最短通行时间。

**如何计算**：
```python
from cpi import dijkstra_multi_source

T_c = dijkstra_multi_source(
    nodes=list(cells.keys()),
    neighbors=neighbors,
    terrain_cost=terrain_cost,
    sources=camp_cell_ids,        # 营地单元格 ID 列表
    blocked=blocked_function       # 可选：被火灾阻挡的单元格
)
```

**值**：
- `0.0` - 在营地
- 正浮点数 - 通行时间
- `float("inf")` - 不可达

#### 2. `eco_sensitive` - 生态敏感区
**类型**：`Dict[int, bool]`

**含义**：如果在此处布置设备会产生生态惩罚，则为 `True`。

**示例**：
```python
eco_sensitive = {
    1: False,
    2: True,     # 湿地、筑巢区等
    3: False,
    # ...
}
```

#### 3. `fire_penalty` - 火灾惩罚
**类型**：`Dict[int, float]`

**含义**：由于火灾风险从 CPI 中减去的惩罚。

**计算**：
```python
gamma_max = 20.0  # 最大可能惩罚

fire_penalty = {
    cell_id: gamma_max * fire_risk_fn(cells[cell_id]["lon"], cells[cell_id]["lat"])
    for cell_id in cells
}
```

**范围**：`0.0` 到 `gamma_max`

#### 4. `species_active` - 物种栖息地映射
**类型**：`Dict[str, Dict[int, bool]]`

**含义**：对于每个物种，哪些单元格在其栖息地内。

**示例**：
```python
species_active = {
    "rhino": {
        1: True,    # 犀牛栖息地
        2: False,   # 不是犀牛栖息地
        3: True,
        # ...
    },
    "elephant": {
        1: True,
        2: True,
        3: False,
        # ...
    },
    # 添加更多物种...
}
```

---

## 参数

**类型**：`Dict[str, Any]`

**描述**：CPI 模型的可调常量。

### 完整参数字典

```python
params = {
    # 存活/通行时间
    "lambda": 0.4,            # 存活衰减率（典型 0-1）

    # 设备效果
    "D_device": 0.8,          # 威慑效果 (0-1)
    "eta_camera": 0.5,        # 相机核实有效性 (0-1)
    "eta_uav": 1.0,           # 无人机核实有效性 (0-1)

    # 惩罚
    "eco_penalty": 50.0,      # 生态惩罚（可以很大）
    "gamma_max": 20.0,        # 最大火灾惩罚

    # 物种权重
    "W": {
        "rhino": 10.0,
        "elephant": 2.0,
        # 添加更多物种...
    },
    "W_base": 0.5,            # 非栖息地单元格的基准权重
}
```

### 参数详情

#### `lambda` - 存活衰减率
**类型**：`float`

**典型范围**：`0.1` 到 `1.0`

**含义**：控制存活概率随通行时间衰减的速度。
- 值越小 = 存活衰减越慢（远处区域仍然可行）
- 值越大 = 存活衰减越快（只有近处区域重要）

**公式**：`S = exp(-λ * T_c)`

#### `D_device` - 威慑效果
**类型**：`float`

**典型范围**：`0.0` 到 `1.0`

**含义**：由于设备存在而导致的偷猎概率降低。
- `0.0` = 无威慑（设备不会吓到偷猎者）
- `1.0` = 完美威慑（偷猎被消除）

#### `eta_camera`、`eta_uav` - 核实有效性
**类型**：`float`

**典型范围**：`0.0` 到 `1.0`

**含义**：事件被成功核实/拦截的概率。
- `0.0` = 从不抓偷猎者
- `1.0` = 总是抓到偷猎者（当威慑失败时）

#### `eco_penalty` - 生态惩罚
**类型**：`float`

**典型范围**：`10.0` 到 `100.0`

**含义**：在敏感区布置设备时从 CPI 减去的惩罚。
- 设置大值以有效禁止在敏感区布置设备
- 设置为 0 以禁用生态约束

#### `gamma_max` - 最大火灾惩罚
**类型**：`float`

**典型范围**：`10.0` 到 `50.0`

**含义**：最大火灾风险时的惩罚（火险区中心）。

#### `W` - 物种权重
**类型**：`Dict[str, float]`

**含义**：每个物种的重要性权重。
- 越高 = 保护该物种的优先级越高
- 应反映保护状态、经济价值、文化重要性等

#### `W_base` - 基准权重
**类型**：`float`

**含义**：当单元格不在物种栖息地时使用的权重。
- 设置为 0 以忽略非栖息地单元格
- 设置为小正值用于一般保护

---

## 完整输入示例

```python
from cpi import (
    dms_to_decimal,
    build_fire_risk_function,
    dijkstra_multi_source,
    compute_cpi_for_cell
)

# ==========================================================================
# 1. 空间数据
# ==========================================================================

# 公园边界（4 个点）
park_boundary = [
    (dms_to_decimal("14°24'43.35\"E"), dms_to_decimal("19°26'55.93\"S")),
    (dms_to_decimal("14°15'46.12\"E"), dms_to_decimal("18°37'00.78\"S")),
    (dms_to_decimal("17°08'59.58\"E"), dms_to_decimal("18°29'09.57\"S")),
    (dms_to_decimal("17°06'34.10\"E"), dms_to_decimal("19°19'33.18\"S")),
]

# 火险四边形（2 个区域）
fire_quads = [
    [(16.595, -18.834), (17.116, -18.832), (16.552, -19.084), (17.093, -19.145)],
    [(15.482, -19.289), (15.875, -19.310), (15.879, -19.114), (15.515, -19.140)],
]

# ==========================================================================
# 2. 单元格网格（替换为你的 982 个单元格）
# ==========================================================================

cells = {
    1: {"lon": 16.7, "lat": -18.95, "terrain": "road"},
    2: {"lon": 15.7, "lat": -19.2, "terrain": "grass"},
    3: {"lon": 16.2, "lat": -18.6, "terrain": "forest"},
    # ... 还有 979 个单元格 ...
}

# 单元格邻接
neighbors = {
    1: [2, 3],
    2: [1, 3],
    3: [1, 2],
    # ...
}

# ==========================================================================
# 3. 地形和通行
# ==========================================================================

terrain_weight = {"road": 1.0, "grass": 3.0, "forest": 5.0, "swamp": float("inf")}
terrain_cost = {cid: terrain_weight[cells[cid]["terrain"]] for cid in cells}

# 营地（源节点）
camp_cell_ids = [1]

# ==========================================================================
# 4. 火灾风险
# ==========================================================================

fire_risk_fn = build_fire_risk_function(
    park_boundary,
    fire_quads,
    combine="max",
    radial_mode="linear"
)

gamma_max = 20.0
fire_penalty = {}
fire_risk = {}
for cid, info in cells.items():
    r = fire_risk_fn(info["lon"], info["lat"])
    fire_risk[cid] = r
    fire_penalty[cid] = gamma_max * r

# 可选：火灾阻挡通行
fire_blocks_travel = True
def blocked(cid):
    return fire_blocks_travel and fire_risk[cid] > 0.0

# ==========================================================================
# 5. 预计算通行时间
# ==========================================================================

T_c = dijkstra_multi_source(
    nodes=list(cells.keys()),
    neighbors=neighbors,
    terrain_cost=terrain_cost,
    sources=camp_cell_ids,
    blocked=blocked
)

# ==========================================================================
# 6. 预计算映射
# ==========================================================================

precomp = {
    "T_c": T_c,
    "eco_sensitive": {1: False, 2: True, 3: False},  # ... 所有单元格
    "fire_penalty": fire_penalty,
    "species_active": {
        "rhino": {1: True, 2: False, 3: True},
        "elephant": {1: True, 2: True, 3: False},
    }
}

# ==========================================================================
# 7. 参数
# ==========================================================================

params = {
    "lambda": 0.4,
    "D_device": 0.8,
    "eta_camera": 0.5,
    "eta_uav": 1.0,
    "eco_penalty": 50.0,
    "W": {"rhino": 10.0, "elephant": 2.0},
    "W_base": 0.5
}

# ==========================================================================
# 8. 计算 CPI
# ==========================================================================

# 单个单元格
cpi = compute_cpi_for_cell(
    cell_id=3,
    species_id="rhino",
    device_type="uav",
    params=params,
    precomp=precomp
)

# 所有组合
results = {}
for cid in cells:
    for sp in ["rhino", "elephant"]:
        for device in ["none", "camera", "uav"]:
            key = (cid, sp, device)
            results[key] = compute_cpi_for_cell(cid, sp, device, params, precomp)
```

---

## 数据准备检查清单

运行 CPI 计算前：

- [ ] 公园边界已转换为十进制度数
- [ ] 火险四边形已定义
- [ ] 所有单元格有经度、纬度、地形
- [ ] 邻居邻接表完整
- [ ] 地形成本已映射
- [ ] 营地位置已确定
- [ ] 生态敏感区已标记
- [ ] 物种栖息地映射已创建
- [ ] 参数已设置为合理值
