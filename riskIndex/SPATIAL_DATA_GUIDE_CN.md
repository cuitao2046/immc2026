# 空间数据生成器指南

## 概述

空间数据生成器使用高斯平滑技术为野生动物保护区风险建模创建真实的连续空间地图。本指南描述了生成的数据结构、格式和使用模式。

## 数据生成过程

### 核心概念

生成器使用**高斯平滑**创建真实的连续空间模式，而不是离散网格单元。这会在不同地形类型、植被区和动物分布之间产生自然的过渡效果。

### 随机种子

为了可复现性，您可以指定随机种子：

```python
generator = SpatialDataGenerator(config=config, seed=42)
```

## 配置

### SpatialConfig 数据类

#### 基本设置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `size` | int | 120 | 方形地图的大小（像素） |
| `season` | str | "rainy" | 季节："rainy"（雨季）或 "dry"（旱季） |
| `hour` | int | 22 | 一天中的小时（0-23） |
| `output_dir` | str | "maps" | 保存地图的目录 |
| `save_maps` | bool | True | 是否保存图片地图 |
| `save_data` | bool | True | 是否保存原始数据（NumPy/CSV） |
| `map_format` | str | "jpg" | 图片格式："jpg"、"png" 或 "both" |

#### 平滑尺度

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `terrain_smooth_scale` | float | 10.0 | 地形的高斯sigma值 |
| `water_smooth_scale` | float | 8.0 | 水体的高斯sigma值 |
| `animal_smooth_scale` | float | 6.0 | 动物分布的高斯sigma值 |

#### 地形配置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `terrain_threshold_lowland` | float | 0.3 | 低地分类阈值 |
| `terrain_threshold_plain` | float | 0.55 | 平原分类阈值 |
| `terrain_threshold_hill` | float | 0.75 | 丘陵分类阈值 |

- 低于 `terrain_threshold_lowland` 的值 = 低地（0）
- 阈值之间的值 = 平原（1）、丘陵（2）
- 高于 `terrain_threshold_hill` 的值 = 山地（3）

#### 水域配置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `water_threshold` | float | 0.65 | 水体生成阈值 |

- 值越小，水域越大
- 水仅出现在低地区域

#### 道路配置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `num_roads` | int | 4 | 要生成的道路数量 |

#### 水坑配置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `waterhole_probability` | float | 0.02 | 水附近出现水坑的概率 |
| `waterhole_search_range` | int | 2 | 搜索附近水源的范围（像素） |

#### 物种配置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `rhino_weight` | float | 0.5 | 犀牛在密度计算中的权重 |
| `elephant_weight` | float | 0.3 | 大象在密度计算中的权重 |
| `bird_weight` | float | 0.2 | 鸟类在密度计算中的权重 |
| `rhino_season_multipliers` | tuple | (1.2, 1.0) | 季节乘数（雨季，旱季） |
| `elephant_season_multipliers` | tuple | (1.3, 0.9) | 季节乘数（雨季，旱季） |
| `bird_season_multipliers` | tuple | (1.5, 0.8) | 季节乘数（雨季，旱季） |

权重之和必须为1.0。

#### 火灾风险配置

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `fire_risk_by_vegetation` | tuple | (0.8, 0.6, 0.5, 0.2) | 按植被类型的火灾风险 |

元组顺序：（草地，灌木，森林，湿地）

#### 风险计算权重

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `risk_weight_human` | float | 0.4 | 人为风险组件的权重 |
| `risk_weight_environmental` | float | 0.3 | 环境风险组件的权重 |
| `risk_weight_density` | float | 0.3 | 动物密度组件的权重 |

权重之和必须为1.0。

#### 人为风险子权重

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `human_risk_weight_boundary` | float | 0.4 | 边界接近度的权重 |
| `human_risk_weight_road` | float | 0.35 | 道路接近度的权重 |
| `human_risk_weight_water` | float | 0.25 | 水源接近度的权重 |

权重之和必须为1.0。

#### 环境风险子权重

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `env_risk_weight_fire` | float | 0.6 | 火灾风险的权重 |
| `env_risk_weight_terrain` | float | 0.4 | 地形复杂度的权重 |

权重之和必须为1.0。

#### 时间因子

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `temporal_factor_night` | float | 1.3 | 夜间的风险乘数 |
| `temporal_factor_day` | float | 1.0 | 白天的风险乘数 |
| `temporal_factor_rainy` | float | 1.2 | 雨季的风险乘数 |
| `temporal_factor_dry` | float | 1.0 | 旱季的风险乘数 |

### 配置文件使用

配置可以保存和从JSON文件加载：

```python
from risk_model.data import SpatialConfig

# 创建并保存配置
config = SpatialConfig(
    size=120,
    season="rainy",
    hour=22,
    num_roads=6,
    waterhole_probability=0.05
)
config.save("my_config.json")

# 从文件加载
loaded_config = SpatialConfig.load("my_config.json")
```

完整模板请参见 `config_example.json`。

## 生成的地图

所有地图都是形状为 `(size, size)` 的NumPy数组。

### 1. 地形图 (`terrain`)

具有自然边界的离散地形分类。

| 值 | 类型 | 描述 |
|-------|------|-------------|
| 0 | 低地 | 平坦区域，适合形成水体 |
| 1 | 平原 | 草原区域 |
| 2 | 丘陵 | 斜坡地形 |
| 3 | 山地 | 高海拔，森林覆盖 |

**生成方法：**
- 使用高斯滤波器平滑随机噪声（默认σ=10.0）
- 使用 `terrain_threshold_*` 配置值进行阈值分类

### 2. 水体图 (`water`)

指示永久水体的二值地图。

| 值 | 描述 |
|-------|-------------|
| 0 | 陆地 |
| 1 | 水体 |

**生成约束：**
- 仅出现在低地区域（terrain == 0）
- 使用σ=8.0的平滑噪声（默认）
- 使用 `water_threshold` 配置进行阈值处理

### 3. 植被图 (`vegetation`)

从地形和水体派生的植被类型。

| 值 | 类型 | 关联地形 |
|-------|------|-------------------|
| 0 | 无 | （未使用） |
| 1 | 草原 | 平原（terrain == 1） |
| 2 | 灌木 | 丘陵（terrain == 2） |
| 3 | 森林 | 山地（terrain == 3） |
| 4 | 湿地 | 水体（water == 1） |

### 4. 道路图 (`roads`)

具有自然路径外观的道路网络。

| 值 | 描述 |
|-------|-------------|
| 0 | 无道路 |
| 1 | 道路 |

**生成算法：**
- 从上到下创建 `num_roads` 条道路
- 随机游走，横向移动±1或0
- 避开水体
- 自然蜿蜒的路径外观

### 5. 水坑图 (`waterholes`)

大型水体附近的小型水源。

| 值 | 描述 |
|-------|-------------|
| 0 | 无水坑 |
| 1 | 水坑 |

**放置规则：**
- 必须在 `waterhole_search_range` 像素范围内有水源
- 每个符合条件的位置有 `waterhole_probability` 的概率
- 不在水中

### 6. 动物密度图

范围在[0, 1]内的连续密度值。

#### 犀牛密度 (`rhino`)
- 偏好草原（vegetation == 1）
- 使用σ=6.0的平滑噪声（默认）
- 非草原区域为零

#### 大象密度 (`elephant`)
- 偏好草原和森林（vegetation == 1或3）
- 使用σ=6.0的平滑噪声（默认）
- 其他区域为零

#### 鸟类密度 (`bird`)
- 偏好湿地（vegetation == 4）
- 使用σ=6.0的平滑噪声（默认）
- 非湿地区域为零

#### 总动物密度 (`animal_density`)
- 使用 `rhino_weight`、`elephant_weight`、`bird_weight` 进行加权求和
- 应用季节乘数
- 不归一化以保持相对丰度

### 7. 火灾风险图 (`fire_risk`)

基于植被类型的火灾风险。

| 植被 | 默认火灾风险 |
|------------|-----------|
| 草原 (1) | 0.8 |
| 灌木 (2) | 0.6 |
| 森林 (3) | 0.5 |
| 湿地 (4) | 0.2 |

可通过 `fire_risk_by_vegetation` 配置。

### 8. 距离图

以像素为单位的连续距离测量。

#### 到道路的距离 (`distance_to_road`)
- 到最近道路像素的欧几里得距离
- 无道路时的最大值 = 地图大小

#### 到水源的距离 (`distance_to_water`)
- 到最近水坑的欧几里得距离
- 注意：这是到水坑的距离，不是到永久水体的距离

#### 到边界的距离 (`distance_to_boundary`)
- 到最近边缘的曼哈顿距离
- `min(i, j, size-i, size-j)`

### 9. 风险图 (`risk_map`)

归一化后的最终风险指数，范围[0, 1]。

**计算公式（可配置权重）：**

```
人为风险 (H) = human_risk_weight_boundary * (1 - 归一化边界距离)
              + human_risk_weight_road * (1 - 归一化道路距离)
              + human_risk_weight_water * (1 - 归一化水源距离)

环境风险 (E) = env_risk_weight_fire * 火灾风险
              + env_risk_weight_terrain * (地形/3)

密度值 (D) = rhino_weight * 犀牛 * 犀牛季节乘数
            + elephant_weight * 大象 * 大象季节乘数
            + bird_weight * 鸟类 * 鸟类季节乘数

时间因子 (T) = 如果 hour < 6 或 hour > 18 则为 temporal_factor_night
              否则为 temporal_factor_day

季节因子 (S) = 如果 season == "rainy" 则为 temporal_factor_rainy
              否则为 temporal_factor_dry

原始风险 = (risk_weight_human * H
          + risk_weight_environmental * E
          + risk_weight_density * D) * T * S

风险图 = 将原始风险归一化到 [0, 1]
```

## 使用示例

### 基本使用

```python
from risk_model.data import SpatialDataGenerator, SpatialConfig

# 创建配置
config = SpatialConfig(
    size=120,
    season="rainy",
    hour=22,
    output_dir="my_maps",
    save_maps=True
)

# 创建生成器并生成地图
generator = SpatialDataGenerator(config=config, seed=42)
maps = generator.generate()

# 访问单独的地图
print(f"风险图形状: {maps.risk_map.shape}")
print(f"最大风险: {maps.risk_map.max()}")
print(f"最小风险: {maps.risk_map.min()}")
```

### 自定义配置示例

```python
# 侧重鸟类保护并带有大量水坑的配置
config = SpatialConfig(
    size=100,
    season="rainy",
    hour=6,
    num_roads=3,
    waterhole_probability=0.08,
    waterhole_search_range=3,
    rhino_weight=0.2,
    elephant_weight=0.2,
    bird_weight=0.6,
    bird_season_multipliers=(2.0, 1.0),
    temporal_factor_night=1.5
)

generator = SpatialDataGenerator(config=config, seed=42)
maps = generator.generate()
```

### 访问特定数据

```python
# 获取高风险区域
high_risk_mask = maps.risk_map > 0.7
high_risk_count = np.sum(high_risk_mask)
print(f"高风险像素: {high_risk_count}")

# 获取特定区域的动物密度
region = maps.animal_density[20:40, 20:40]
print(f"区域动物密度平均值: {region.mean()}")

# 查找所有水体位置
water_coords = np.argwhere(maps.water == 1)
print(f"水体像素: {len(water_coords)}")
```

### 不同时间的批量生成

```python
# 为一天中的不同时间生成地图
for hour in [0, 6, 12, 18]:
    config = SpatialConfig(
        season="rainy",
        hour=hour,
        output_dir=f"maps_{hour:02d}",
        save_maps=True
    )
    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()
    print(f"小时 {hour}: 平均风险 = {maps.risk_map.mean():.4f}")
```

## 输出文件

### 图片地图

当 `save_maps=True` 时，会生成以下图片文件：

| 文件名 | 颜色映射 | 描述 |
|----------|----------|-------------|
| `01_terrain.*` | terrain | 4级地形分类 |
| `01a_lowland.*` | Blues | 低地分布蒙版 |
| `01b_plain.*` | YlGn | 平原分布蒙版 |
| `01c_hill.*` | BrBG | 丘陵分布蒙版 |
| `01d_mountain.*` | terrain | 山地分布蒙版 |
| `02_water_bodies.*` | Blues | 永久水体 |
| `02a_water_only.*` | Blues | 水体分布蒙版 |
| `03_waterholes.*` | Blues | 水坑位置 |
| `04_vegetation.*` | Greens | 植被类型 |
| `04a_grassland.*` | YlGn | 草原分布蒙版 |
| `04b_shrubland.*` | Greens | 灌木分布蒙版 |
| `04c_forest.*` | viridis | 森林分布蒙版 |
| `04d_wetland.*` | Blues | 湿地分布蒙版 |
| `05_roads.*` | gray | 道路网络 |
| `06_fire_risk.*` | YlOrRd | 火灾风险指数 |
| `07a_rhino_density.*` | YlGn | 犀牛密度分布 |
| `07b_elephant_density.*` | YlGn | 大象密度分布 |
| `07c_bird_density.*` | YlGnBu | 鸟类密度分布 |
| `07_total_animal_density.*` | YlGn | 组合动物密度 |
| `08_risk_index.*` | hot | 带有色标的最终风险热力图 |

### 原始数据文件

当 `save_data=True` 时，以下文件保存在 `data/` 目录中：

| 文件 | 描述 |
|------|-------------|
| `terrain.npy` | 地形分类图 |
| `water.npy` | 水体图 |
| `vegetation.npy` | 植被图 |
| `roads.npy` | 道路图 |
| `waterholes.npy` | 水坑图 |
| `rhino.npy` | 犀牛密度图 |
| `elephant.npy` | 大象密度图 |
| `bird.npy` | 鸟类密度图 |
| `animal_density.npy` | 总动物密度 |
| `fire_risk.npy` | 火灾风险图 |
| `distance_to_road.npy` | 到道路的距离图 |
| `distance_to_water.npy` | 到水坑的距离图 |
| `distance_to_boundary.npy` | 到边界的距离图 |
| `risk_map.npy` | 风险指数图 |
| `config.json` | 完整的生成配置 |

### CSV文件

CSV版本也保存在 `csv/` 目录中以便查看。

## 依赖项

### 必需
- `numpy` - 数组运算

### 可选（带有回退）
- `scipy` - 高斯滤波（回退到卷积实现）
- `matplotlib` - 地图可视化（如果不可用则跳过保存）

## 数据验证

所有地图都通过其生成方式进行隐式验证：
- 地形值：{0, 1, 2, 3}
- 二值地图（水体、道路、水坑）：{0, 1}
- 植被值：{0, 1, 2, 3, 4}
- 连续地图：归一化到[0, 1]
- 距离地图：≥ 0

## 关于真实性的说明

1. **高斯平滑尺度**：较大的sigma值会创建更宽泛、更真实的模式
2. **生态约束**：动物被限制在合适的植被类型中
3. **水文逻辑**：水只出现在低地，水坑靠近水体
4. **时间变化**：风险随一天中的时间和季节变化
5. **可配置权重**：模型的所有方面都可以通过配置进行自定义

## 扩展点

要自定义生成器：

1. 继承 `SpatialDataGenerator`
2. 重写特定的 `generate_*` 方法
3. 向 `SpatialMaps` 数据类添加新的地图类型
4. 使用配置选项调整行为而无需更改代码

示例：
```python
class CustomSpatialGenerator(SpatialDataGenerator):
    def generate_fire_risk(self, vegetation: np.ndarray) -> np.ndarray:
        # 自定义火灾风险逻辑
        fire_risk = np.zeros_like(vegetation, dtype=float)
        # ... 您的自定义逻辑 ...
        return fire_risk
```
