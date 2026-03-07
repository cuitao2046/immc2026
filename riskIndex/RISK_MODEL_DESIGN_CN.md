# 保护区网格风险指数模型 - 设计文档

## 1. 模型目标

在野生动物保护区中，巡逻人员、无人机、固定监控设备和救援队伍等资源是有限的。为了最大化保护效果，需要将保护区建模为网格，并为每个网格计算**风险系数**，以指导巡逻和监控资源的最优分配。

本模型综合考虑：
- 人为威胁风险
- 环境风险
- 动物分布密度
- 季节变化
- 昼夜变化

来为每个网格计算**综合风险值**。

最终输出：每个网格的风险值

```
R_i ∈ [0, 1]
```

数值越高表示该区域需要更密集的监控。

---

## 2. 风险计算公式

### 2.1 综合风险（未归一化）

```
R'_{i,t} = (ω₁·H_{i,t} + ω₂·E_i + ω₃·Σ_s w_s·D_{s,i,t}) × T_t × S_t
```

### 2.2 归一化

```
R_i = (R'_{i,t} - R_min) / (R_max - R_min)
```

结果范围：
```
R_i ∈ [0, 1]
```

其中：
- R_min = 所有网格的最小风险值
- R_max = 所有网格的最大风险值

### 2.3 符号索引

| 符号 | 含义 |
|------|------|
| i | 网格单元格标识符 |
| t | 时间 |
| s | 物种 |
| H_{i,t} | 人为风险 |
| E_i | 环境风险 |
| D_{s,i,t} | 物种密度 |
| T_t | 昼夜影响因子 |
| S_t | 季节影响因子 |
| P_t | 偷猎时间概率 |
| w_s | 物种权重 |
| ω₁, ω₂, ω₃ | 权重系数 |

---

## 3. 人为风险模型

人为风险反映偷猎等人类活动的威胁程度。

```
H_{i,t} = (α₁·d_boundary + α₂·d_road + α₃·d_water) × P_t
```

注：距离越近，人为风险越高（距离应为归一化后的倒数值）。

### 3.1 参数

| 参数 | 含义 |
|------|------|
| d_boundary | 到保护区边界的距离 |
| d_road | 到道路的距离 |
| d_water | 到水源的距离 |
| P_t | 偷猎时间概率 |

### 3.2 权重参数

| 参数 | 含义 | 示例值 |
|------|------|--------|
| α₁ | 边界影响权重 | 0.4 |
| α₂ | 道路影响权重 | 0.35 |
| α₃ | 水源影响权重 | 0.25 |

约束：
```
α₁ + α₂ + α₃ = 1
```

---

## 4. 环境风险模型

环境风险反映自然条件对动物安全的影响。

```
E_i = β₁·V_fire + β₂·C_terrain
```

### 4.1 参数

| 参数 | 含义 | 范围 |
|------|------|------|
| V_fire | 火灾风险指数 | [0, 1] |
| C_terrain | 地形复杂度 | [0, 1] |

### 4.2 参数说明

**火灾风险 (V_fire)**
- 范围：0 ≤ V_fire ≤ 1
- 来源：
  - 植被干燥度
  - 温度
  - 历史火灾记录

**地形复杂度 (C_terrain)**
- 表示地形对动物受伤概率的影响
- 示例：
  - 山地
  - 峡谷
  - 陡坡
- 范围：0 ≤ C_terrain ≤ 1

---

## 5. 物种密度模型

动物密度反映保护价值。

```
D_{s,i,t}
```

表示：物种 (s) 在网格 (i) 和时间 (t) 的密度。

### 5.1 加权物种密度

```
Σ_s w_s·D_{s,i,t}
```

### 5.2 物种权重（示例）

| 物种 | 权重 |
|------|------|
| 犀牛 | 0.5 |
| 大象 | 0.3 |
| 鸟类 | 0.2 |

濒危动物权重更高。

### 5.3 季节变化

```
D_{s,i,t} = D_{s,i} × M_season
```

**季节调整系数 (M_season)**

| 物种 | 雨季 | 旱季 |
|------|------|------|
| 大象 | 1.3 | 0.9 |
| 犀牛 | 1.2 | 1.0 |
| 鸟类 | 1.5 | 0.8 |

---

## 6. 季节影响模型

不同季节会影响：
- 动物分布
- 偷猎活动
- 巡逻难度

### 6.1 季节因子

```
S_t = {
    1.0   旱季
    1.2   雨季
}
```

### 6.2 季节影响

| 季节 | 影响 |
|------|------|
| 旱季 | 动物分散 |
| 雨季 | 动物集中到水源 |

雨季风险通常更高。

---

## 7. 昼夜影响模型

偷猎行为通常在夜间更频繁。

### 7.1 昼夜因子（离散）

```
T_t = {
    1.0   白天
    1.3   夜间
}
```

### 7.2 昼夜因子（连续）

```
T_t = 1 + γ·sin(2πt/24)
```

### 7.3 按时间的风险级别

| 时间 | 风险 |
|------|------|
| 白天 | 较低 |
| 夜间 | 较高 |

### 7.4 示例时间因子

| 时间 | 因子 |
|------|------|
| 08:00 | 1.0 |
| 12:00 | 0.9 |
| 20:00 | 1.2 |
| 24:00 | 1.3 |

---

## 8. 模型权重设置

最终风险权重：

```
ω₁ + ω₂ + ω₃ = 1
```

### 8.1 示例权重

| 参数 | 含义 | 值 |
|------|------|-----|
| ω₁ | 人为风险权重 | 0.4 |
| ω₂ | 环境风险权重 | 0.3 |
| ω₃ | 动物密度权重 | 0.3 |

---

## 9. 输入数据结构

模型输入数据包括：

### 9.1 枚举类型

#### VegetationType 枚举
```
VegetationType {
    GRASSLAND = "grassland"    // 草原
    FOREST = "forest"          // 森林
    SHRUB = "shrub"            // 灌木
}
```

#### Season 枚举
```
Season {
    DRY = "dry"         // 旱季
    RAINY = "rainy"     // 雨季
}
```

### 9.2 网格数据类

#### Grid（输入
```
@dataclass
Grid {
    grid_id: str                    // 唯一标识符（如 "A12"）
    x: float                        // 网格中心X坐标
    y: float                        // 网格中心Y坐标
    distance_to_boundary: float          // 到边界的归一化距离 [0,1]
    distance_to_road: float            // 到道路的归一化距离 [0,1]
    distance_to_water: float           // 到水源的归一化距离 [0,1]
}
```

### 9.3 物种数据类

#### Species
```
@dataclass
Species {
    name: str                         // 物种名称（如 "rhino", "elephant", "bird"）
    weight: float                     // 保护权重（越高越重要）
    rainy_season_multiplier: float      // 雨季密度乘数
    dry_season_multiplier: float        // 旱季密度乘数
}
```

#### SpeciesDensity
```
@dataclass
SpeciesDensity {
    densities: Dict[str, float]          // {物种名称 -> 归一化密度 [0,1]}
}
```

### 9.4 环境数据类

#### Environment
```
@dataclass
Environment {
    fire_risk: float                 // 火灾风险指数 [0,1]
    terrain_complexity: float          // 地形复杂度 [0,1]
    vegetation_type: VegetationType     // 植被类型
}
```

### 9.5 时间上下文类

#### TimeContext
```
@dataclass
TimeContext {
    hour_of_day: int                 // 一天中的小时 [0, 23]
    season: Season                  // 当前季节（DRY 或 RAINY）

    // 派生属性：
    is_daytime: bool                 // 如果是 6:00-18:00 则为 true
    is_nighttime: bool               // 如果是 18:00-6:00 则为 true
}
```

### 9.6 输入字段摘要

#### 网格空间数据

| 字段 | 类型 | 范围 | 描述 |
|------|------|------|------|
| grid_id | string | - | 唯一标识符（如 "A12"） |
| x | float | ≥ 0 | 网格中心X坐标 |
| y | float | ≥ 0 | 网格中心Y坐标 |
| distance_to_boundary | float | [0,1] | 到保护区边界的归一化距离（0=在边界，1=最远） |
| distance_to_road | float | [0,1] | 到最近道路的归一化距离（0=在路边，1=最远） |
| distance_to_water | float | [0,1] | 到最近水源的归一化距离 |

#### 环境数据

| 字段 | 类型 | 范围 | 描述 |
|------|------|------|------|
| fire_risk | float | [0,1] | 火灾风险指数（0=安全，1=危险） |
| terrain_complexity | float | [0,1] | 地形复杂度（0=平坦，1=复杂） |
| vegetation_type | enum | - | 植被类型（GRASSLAND, FOREST, SHRUB） |

#### 动物数据

| 字段 | 类型 | 范围 | 描述 |
|------|------|------|------|
| species_name | string | - | 物种名称 |
| density | float | [0,1] | 网格中物种的归一化密度 |
| weight | float | >0 | 物种的保护权重 |
| rainy_season_multiplier | float | ≥0 | 雨季密度乘数 |
| dry_season_multiplier | float | ≥0 | 旱季密度乘数 |

#### 时间数据

| 字段 | 类型 | 范围 | 描述 |
|------|------|------|------|
| hour_of_day | integer | [0,23] | 一天中的小时 |
| season | enum | - | 季节（DRY, RAINY） |

---

## 10. 模型输出

### 10.1 输出数据类

#### RiskComponents（中间输出）
```
@dataclass
RiskComponents {
    human_risk: float             // 人为风险组件 [0, ~1]
    environmental_risk: float        // 环境风险组件 [0, ~1]
    density_value: float          // 加权物种密度值 [0, ~1]
    diurnal_factor: float         // 昼夜乘数（通常 1.0-1.3）
    seasonal_factor: float        // 季节乘数（通常 1.0-1.2）

    // 派生属性：
    temporal_factor: float        // diurnal_factor × seasonal_factor
}
```

#### GridRiskResult（单个网格的最终输出）
```
@dataclass
GridRiskResult {
    grid_id: str                  // 网格标识符（如 "A12"）
    raw_risk: float               // 未归一化的风险值
    normalized_risk: Optional[float]   // 归一化风险 [0,1]
    components: Optional[RiskComponents]  // 单独的风险组件
}
```

### 10.2 归一化输出

#### NormalizationEngine 状态
```
NormalizationEngine {
    min_risk: Optional[float]     // 批次中最小原始风险
    max_risk: Optional[float]     // 批次中最大原始风险
    is_fitted: bool               // 调用 fit() 后为 true
}
```

#### 归一化公式
```
R_i = (R'_i - R_min) / (R_max - R_min)
```

其中：
- R'_i = 网格 i 的原始风险值
- R_min = 批次中所有网格的最小原始风险
- R_max = 批次中所有网格的最大原始风险
- R_i = 归一化风险值 [0, 1]

### 10.3 批次输出结构

#### 批次计算结果
```
List[GridRiskResult] [
    GridRiskResult {
        grid_id: "A00",
        raw_risk: 1.423,
        normalized_risk: 1.000,
        components: RiskComponents {
            human_risk: 0.937,
            environmental_risk: 0.760,
            density_value: 1.032,
            diurnal_factor: 1.3,
            seasonal_factor: 1.2
        }
    },
    GridRiskResult {
        grid_id: "A01",
        ...
    },
    ...
]
```

### 10.4 输出字段摘要

#### GridRiskResult 字段

| 字段 | 类型 | 范围 | 描述 |
|------|------|------|------|
| grid_id | string | - | 唯一网格标识符 |
| raw_risk | float | ≥0 | 未归一化的综合风险值 |
| normalized_risk | float | [0,1] | 用于比较的归一化风险（未归一化时为 null） |

#### RiskComponents 字段

| 字段 | 类型 | 范围 | 描述 |
|------|------|------|------|
| human_risk | float | [0, ~1] | 人为威胁风险 |
| environmental_risk | float | [0, ~1] | 环境风险 |
| density_value | float | [0, ~1] | 加权物种密度（保护价值） |
| diurnal_factor | float | ≥0 | 一天中的时间乘数 |
| seasonal_factor | float | ≥0 | 季节乘数 |
| temporal_factor | float | ≥0 | 组合时间乘数（派生） |

### 10.5 示例输出

#### 单个网格示例
```
GridRiskResult {
    grid_id: "A12",
    raw_risk: 1.380,
    normalized_risk: 0.82,
    components: RiskComponents {
        human_risk: 0.92,
        environmental_risk: 0.76,
        density_value: 0.96,
        diurnal_factor: 1.3,
        seasonal_factor: 1.2
    }
}
```

#### 表格输出示例

| 网格 | 原始风险 | 归一化风险 | 人为风险 | 环境风险 | 密度值 | 时间因子 |
|------|----------|------------|----------|----------|--------|----------|
| A12 | 1.380 | 0.82 | 0.92 | 0.76 | 0.96 | 1.56 |
| B07 | 1.051 | 0.65 | 0.77 | 0.46 | 0.76 | 1.56 |
| C14 | 0.534 | 0.33 | 0.38 | 0.28 | 0.41 | 1.56 |

---

## 11. 模型应用

计算得到的风险地图可以用于：

### 11.1 巡逻路径优化
高风险区域优先巡逻。

### 11.2 无人机监控
无人机优先覆盖：
- 夜间
- 高风险区域

### 11.3 驻扎点选址
选择具有以下特点的位置：
- 高风险中心
- 覆盖范围最大位置

### 11.4 紧急救援
在动物受伤概率高的区域部署救援人员。

---

## 12. 模型优势

与传统静态模型相比，本模型提供：

### 12.1 动态风险评估
同时考虑：
- 空间因素
- 时间因素

### 12.2 生态一致性
动物行为随季节变化。

### 12.3 调度算法就绪
可以直接作为**DSSA调度算法的输入变量**。
