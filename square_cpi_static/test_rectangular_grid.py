import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from data_loader import DataLoader
from grid_model import HexGridModel


def test_rectangular_grid():
    print("=" * 70)
    print("测试矩形六边形网格生成")
    print("=" * 70)
    
    # 创建数据加载器
    data_loader = DataLoader()
    
    # 生成矩形六边形网格 (12列 x 10行 = 120个网格)
    width, height = 12, 10
    grids = data_loader.generate_rectangular_hex_grid(width=width, height=height)
    
    print(f"\n网格生成结果:")
    print(f"  矩形尺寸: {width} 列 x {height} 行")
    print(f"  总网格数: {len(grids)}")
    
    # 创建网格模型
    grid_model = HexGridModel(grids)
    
    print(f"\n网格坐标示例 (前20个):")
    print(f"{'Grid ID':<10} {'Q':<6} {'R':<6} {'Row':<6} {'Col':<6}")
    print("-" * 40)
    
    for i, grid in enumerate(grids[:20]):
        # 计算行列位置
        row = grid.r
        col = grid.q + (row // 2)
        print(f"{grid.grid_id:<10} {grid.q:<6} {grid.r:<6} {row:<6} {col:<6}")
    
    # 验证矩形边界
    print(f"\n矩形边界验证:")
    q_values = [grid.q for grid in grids]
    r_values = [grid.r for grid in grids]
    print(f"  Q坐标范围: {min(q_values)} ~ {max(q_values)}")
    print(f"  R坐标范围: {min(r_values)} ~ {max(r_values)}")
    
    # 计算邻居关系
    print(f"\n邻居关系验证 (前5个网格):")
    for grid in grids[:5]:
        neighbors = grid_model.get_neighbors(grid.grid_id)
        print(f"  Grid {grid.grid_id}: {len(neighbors)} 个邻居 -> {neighbors}")
    
    # 计算距离
    print(f"\n距离计算验证:")
    if len(grids) >= 3:
        dist_0_1 = grid_model.get_distance(0, 1)
        dist_0_2 = grid_model.get_distance(0, 2)
        dist_0_10 = grid_model.get_distance(0, 10)
        print(f"  Grid 0 -> Grid 1 距离: {dist_0_1}")
        print(f"  Grid 0 -> Grid 2 距离: {dist_0_2}")
        print(f"  Grid 0 -> Grid 10 距离: {dist_0_10}")
    
    # 可视化网格
    print(f"\n生成可视化...")
    visualize_rectangular_grid(grid_model, width, height)
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)


def visualize_rectangular_grid(grid_model, width, height):
    """可视化矩形六边形网格"""
    fig, ax = plt.subplots(figsize=(14, 10))
    
    hex_size = 1.0
    grid_ids = grid_model.get_all_grid_ids()
    
    # 绘制六边形网格
    for grid_id in grid_ids:
        corners = grid_model.get_grid_corners(grid_id, hex_size)
        
        # 根据行列位置着色
        grid = grid_model.get_grid_by_id(grid_id)
        row = grid.r
        col = grid.q + (row // 2)
        
        # 交替颜色显示网格结构
        if (row + col) % 2 == 0:
            color = '#E8F4F8'
        else:
            color = '#F0F8E8'
        
        polygon = Polygon(corners, facecolor=color, edgecolor='black', 
                         linewidth=0.5, alpha=0.8)
        ax.add_patch(polygon)
        
        # 显示网格ID
        center = grid_model.get_grid_center_coords(grid_id, hex_size)
        ax.text(center[0], center[1], str(grid_id), 
               ha='center', va='center', fontsize=6, alpha=0.7)
    
    # 设置图形属性
    ax.set_aspect('equal')
    ax.set_title(f'Rectangular Hexagonal Grid ({width} x {height})', 
                fontsize=16, fontweight='bold')
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Y Coordinate', fontsize=12)
    ax.grid(True, alpha=0.2)
    
    # 设置边界
    bounds = grid_model.get_grid_bounds(hex_size)
    margin = 1.0
    ax.set_xlim(bounds[0] - margin, bounds[1] + margin)
    ax.set_ylim(bounds[2] - margin, bounds[3] + margin)
    
    plt.tight_layout()
    plt.savefig('./output/rectangular_grid_test.png', dpi=200, bbox_inches='tight')
    print(f"  网格可视化已保存到: ./output/rectangular_grid_test.png")
    plt.close()


def test_full_optimization_with_rectangular_grid():
    """使用矩形网格运行完整优化测试"""
    print("\n" + "=" * 70)
    print("使用矩形网格运行完整优化测试")
    print("=" * 70)
    
    from data_loader import DataLoader
    from grid_model import HexGridModel
    from coverage_model import CoverageModel
    from dssa_optimizer import DSSAOptimizer, DSSAConfig
    
    # 设置随机种子
    np.random.seed(42)
    
    # 创建数据加载器
    data_loader = DataLoader()
    
    # 生成矩形六边形网格
    width, height = 12, 10
    grids = data_loader.generate_rectangular_hex_grid(width=width, height=height)
    print(f"\n生成矩形网格: {width} x {height} = {len(grids)} 个网格")
    
    # 生成地形
    terrain_types = ['SaltMarsh', 'SparseGrass', 'DenseGrass', 'WaterHole', 'Road']
    terrain_weights = [0.15, 0.35, 0.25, 0.15, 0.10]
    
    terrain_map = {}
    for grid in grids:
        terrain = np.random.choice(terrain_types, p=terrain_weights)
        terrain_map[grid.grid_id] = terrain
    data_loader.set_terrain_types(terrain_map)
    
    # 生成风险
    risk_map = {}
    for grid in grids:
        base_risk = np.random.uniform(0.0, 0.9)
        terrain = terrain_map[grid.grid_id]
        if terrain == 'Road':
            base_risk *= 1.5
        elif terrain == 'WaterHole':
            base_risk *= 1.3
        elif terrain == 'SaltMarsh':
            base_risk *= 0.6
        risk_map[grid.grid_id] = min(1.0, base_risk)
    data_loader.set_risk_values(risk_map)
    
    # 设置约束
    constraints = {
        'total_patrol': 20,
        'total_camps': 5,
        'max_rangers_per_camp': 5,
        'total_cameras': 10,
        'total_drones': 3,
        'total_fence_length': 50.0
    }
    data_loader.set_constraints(**constraints)
    
    # 设置覆盖参数
    coverage_params = {
        'patrol_radius': 5.0,
        'drone_radius': 8.0,
        'camera_radius': 3.0,
        'fence_protection': 0.5,
        'wp': 0.3,
        'wd': 0.3,
        'wc': 0.2,
        'wf': 0.2
    }
    data_loader.set_coverage_parameters(**coverage_params)
    
    # 初始化矩阵
    data_loader.initialize_deployment_matrix()
    data_loader.initialize_visibility_params()
    
    # 创建模型
    grid_model = HexGridModel(data_loader.grids)
    coverage_model = CoverageModel(
        grid_model,
        data_loader.coverage_params,
        data_loader.deployment_matrix,
        data_loader.visibility_params
    )
    
    # 配置DSSA
    dssa_config = DSSAConfig(
        population_size=30,
        max_iterations=30,
        producer_ratio=0.2,
        scout_ratio=0.2,
        ST=0.8,
        R2=0.5
    )
    
    print(f"\nDSSA配置:")
    print(f"  种群大小: {dssa_config.population_size}")
    print(f"  迭代次数: {dssa_config.max_iterations}")
    
    # 运行优化
    optimizer = DSSAOptimizer(coverage_model, constraints, dssa_config)
    
    print(f"\n开始优化...")
    best_solution, best_fitness, fitness_history = optimizer.optimize()
    
    # 输出结果
    stats = optimizer.get_solution_statistics(best_solution)
    
    print("\n" + "=" * 70)
    print("优化结果")
    print("=" * 70)
    print(f"最优适应度: {best_fitness:.4f}")
    print(f"摄像头: {stats['total_cameras']} / {constraints['total_cameras']}")
    print(f"无人机: {stats['total_drones']} / {constraints['total_drones']}")
    print(f"营地: {stats['total_camps']} / {constraints['total_camps']}")
    print(f"巡逻人员: {stats['total_rangers']} / {constraints['total_patrol']}")
    print(f"围栏: {stats['total_fence_length']} / {constraints['total_fence_length']}")
    
    print(f"\n摄像头位置: {stats['camera_locations']}")
    print(f"无人机位置: {stats['drone_locations']}")
    print(f"营地位置: {stats['camp_locations']}")
    
    print("\n" + "=" * 70)
    print("矩形网格优化测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    # 测试矩形网格生成
    test_rectangular_grid()
    
    # 运行完整优化测试
    test_full_optimization_with_rectangular_grid()
