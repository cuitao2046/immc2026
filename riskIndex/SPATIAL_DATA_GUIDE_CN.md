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

| 参数 | 类型 | 默认值 | 描述 |
|-----------|------|---------|-------------|
| `size` | int | 120 | 方形地图的大小（像素） |
| `season` | str | "rainy" | 季节："rainy"（雨季）或 "dry"（旱季） |
| `hour` | int | 22 | 一天中的小时（0-23） |
| `terrain_smooth_scale` | float | 10.0 | 地形的高斯sigma值 |
| `water_smooth_scale` | float | 8.0 | 水体的高斯sigma值 |
| `animal_smooth_scale` | float | 6.0 | 动物分布的高斯sigma值 |
| `output_dir` | str | "maps" | 保存地图的目录 |
| `save_maps` | bool | True | 是否保存PNG地图 |

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
- 使用高斯滤波器（σ=10.0）平滑随机噪声
- 在0.3、0.55、0.75处进行阈值分类

### 2. 水体图 (`water`)

指示永久水体的二值地图。

| 值 | 描述 |
|-------|-------------|
| 0 | 陆地 |
| 1 | 水体 |

**生成约束：**
- 仅出现在低地区域（terrain == 0）
- 使用σ=8.0的平滑噪声
- 阈值设为0.65

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
- 从上到下创建4条道路
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
- 必须在水体2像素范围内
- 每个符合条件的位置有2%的概率
- 不在水中

### 6. 动物密度图

范围在[0, 1]内的连续密度值。

#### 犀牛密度 (`rhino`)
- 偏好草原（vegetation == 1）
- 使用σ=6.0的平滑噪声
- 非草原区域为零

#### 大象密度 (`elephant`)
- 偏好草原和森林（vegetation == 1或3）
- 使用σ=6.0的平滑噪声
- 其他区域为零

#### 鸟类密度 (`bird`)
- 偏好湿地（vegetation == 4）
- 使用σ=6.0的平滑噪声
- 非湿地区域为零

#### 总动物密度 (`animal_density`)
- 总和：`rhino + elephant + bird`
- 不归一化以保持相对丰度

### 7. 火灾风险图 (`fire_risk`)

基于植被类型的火灾风险。

| 植被 | 火灾风险 |
|------------|-----------|
| 草原 (1) | 0.8 |
| 灌木 (2) | 0.6 |
| 森林 (3) | 0.5 |
| 湿地 (4) | 0.2 |

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

**计算公式：**

```
人为风险 (H) = 0.4 * (1/(d_boundary+1))
               + 0.35 * (1/(d_road+1))
               + 0.25 * (1/(d_water+1))

环境风险 (E) = 0.6 * fire_risk + 0.4 * (terrain/3)

密度值 (D) = 0.5 * rhino + 0.3 * elephant + 0.2 * bird

时间因子 (T) = 1.3（如果 hour < 6 或 hour > 18）否则为 1.0
季节因子 (S) = 1.2（如果 season == "rainy"）否则为 1.0

原始风险 = (0.4*H + 0.3*E + 0.3*D) * T * S

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

当 `save_maps=True` 时，会生成以下PNG文件：

| 文件名 | 颜色映射 | 描述 |
|----------|----------|-------------|
| `terrain_map.png` | terrain | 4级地形分类 |
| `water_map.png` | Blues | 水体 |
| `vegetation_map.png` | Greens | 植被类型 |
| `roads_map.png` | gray | 道路网络 |
| `waterholes_map.png` | Blues | 水坑位置 |
| `animal_density_map.png` | YlGn | 组合动物密度 |
| `risk_map.png` | hot | 带有色标的最终风险热力图 |

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

## 扩展点

要自定义生成器：

1. 继承 `SpatialDataGenerator`
2. 重写特定的 `generate_*` 方法
3. 向 `SpatialMaps` 数据类添加新的地图类型
4. 调整 `calculate_risk()` 中的权重

示例：
```python
class CustomSpatialGenerator(SpatialDataGenerator):
    def generate_fire_risk(self, vegetation: np.ndarray) -> np.ndarray:
        # 自定义火灾风险逻辑
        fire_risk = np.zeros_like(vegetation, dtype=float)
        # ... 您的自定义逻辑 ...
        return fire_risk
```
