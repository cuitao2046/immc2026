import numpy as np
from data_loader import DataLoader
from grid_model import HexGridModel


def test_fence_constraint():
    """测试Fence只能在边缘网格部署的约束"""
    print("=" * 70)
    print("测试Fence约束规则: Fence只能在边缘网格部署")
    print("=" * 70)
    
    # 创建数据加载器
    data_loader = DataLoader()
    
    # 生成矩形六边形网格
    width, height = 12, 10
    grids = data_loader.generate_rectangular_hex_grid(width=width, height=height)
    print(f"\n生成网格: {width} x {height} = {len(grids)} 个网格")
    
    # 创建网格模型
    grid_model = HexGridModel(grids)
    
    # 获取边缘网格
    edge_grids = grid_model.get_edge_grids()
    print(f"边缘网格数量: {len(edge_grids)}")
    print(f"边缘网格ID: {edge_grids[:20]}...")  # 只显示前20个
    
    # 生成地形
    terrain_types = ['SaltMarsh', 'SparseGrass', 'DenseGrass', 'WaterHole', 'Road']
    terrain_weights = [0.15, 0.35, 0.25, 0.15, 0.10]
    
    np.random.seed(42)
    terrain_map = {}
    for grid in grids:
        terrain = np.random.choice(terrain_types, p=terrain_weights)
        terrain_map[grid.grid_id] = terrain
    data_loader.set_terrain_types(terrain_map)
    
    # 初始化部署矩阵（带边缘约束）
    data_loader.initialize_deployment_matrix(edge_grids=edge_grids)
    
    # 检查Fence部署约束
    print("\n" + "-" * 70)
    print("Fence部署约束验证:")
    print("-" * 70)
    
    fence_matrix = data_loader.deployment_matrix['fence']
    
    # 统计
    total_grids = len(grids)
    fence_allowed = sum(1 for v in fence_matrix.values() if v == 1)
    fence_not_allowed = sum(1 for v in fence_matrix.values() if v == 0)
    
    print(f"总网格数: {total_grids}")
    print(f"允许部署Fence的网格: {fence_allowed}")
    print(f"禁止部署Fence的网格: {fence_not_allowed}")
    
    # 验证所有允许部署Fence的网格都是边缘网格
    allowed_fence_grids = [grid_id for grid_id, v in fence_matrix.items() if v == 1]
    
    print(f"\n允许部署Fence的网格ID: {sorted(allowed_fence_grids)[:20]}...")
    
    # 检查是否有非边缘网格被允许部署Fence
    non_edge_with_fence = [grid_id for grid_id in allowed_fence_grids if grid_id not in edge_grids]
    
    if non_edge_with_fence:
        print(f"\n❌ 错误: 以下非边缘网格被允许部署Fence: {non_edge_with_fence}")
    else:
        print(f"\n✅ 验证通过: 所有允许部署Fence的网格都是边缘网格")
    
    # 检查是否有边缘网格被禁止部署Fence（由于地形限制）
    edge_without_fence = [grid_id for grid_id in edge_grids if fence_matrix.get(grid_id, 0) == 0]
    
    if edge_without_fence:
        print(f"\n⚠️  注意: 以下边缘网格因地形限制禁止部署Fence:")
        for grid_id in edge_without_fence[:10]:  # 只显示前10个
            terrain = terrain_map.get(grid_id, 'Unknown')
            print(f"    Grid {grid_id}: {terrain}")
        if len(edge_without_fence) > 10:
            print(f"    ... 还有 {len(edge_without_fence) - 10} 个")
    
    # 详细验证
    print("\n" + "-" * 70)
    print("详细验证 (前20个网格):")
    print("-" * 70)
    print(f"{'Grid ID':<10} {'Row':<6} {'Col':<6} {'Is Edge':<10} {'Terrain':<15} {'Fence Allowed'}")
    print("-" * 70)
    
    for grid in grids[:20]:
        row = grid.r
        col = grid.q + (row // 2)
        is_edge = "✓" if grid.grid_id in edge_grids else "✗"
        terrain = terrain_map.get(grid.grid_id, 'Unknown')
        fence_allowed = "✓" if fence_matrix.get(grid.grid_id, 0) == 1 else "✗"
        print(f"{grid.grid_id:<10} {row:<6} {col:<6} {is_edge:<10} {terrain:<15} {fence_allowed}")
    
    # 可视化
    print("\n生成可视化...")
    visualize_fence_constraint(grid_model, edge_grids, fence_matrix, terrain_map)
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)


def visualize_fence_constraint(grid_model, edge_grids, fence_matrix, terrain_map):
    """可视化Fence约束"""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    hex_size = 1.0
    grid_ids = grid_model.get_all_grid_ids()
    
    # 绘制六边形网格
    for grid_id in grid_ids:
        corners = grid_model.get_grid_corners(grid_id, hex_size)
        
        # 根据Fence部署权限着色
        is_edge = grid_id in edge_grids
        can_fence = fence_matrix.get(grid_id, 0) == 1
        
        if can_fence:
            # 允许部署Fence的边缘网格 - 绿色
            color = '#90EE90'
            edge_color = '#228B22'
            linewidth = 2.5
        elif is_edge:
            # 边缘但不能部署Fence（地形限制）- 黄色
            color = '#FFE4B5'
            edge_color = '#FF8C00'
            linewidth = 2.0
        else:
            # 非边缘网格 - 浅灰色
            color = '#F0F0F0'
            edge_color = '#AAAAAA'
            linewidth = 0.8
        
        # 绘制六边形
        polygon = Polygon(corners, facecolor=color, edgecolor=edge_color, 
                         linewidth=linewidth, alpha=0.9)
        ax.add_patch(polygon)
        
        # 显示网格ID（只在边缘网格显示）
        if is_edge:
            center = grid_model.get_grid_center_coords(grid_id, hex_size)
            terrain = terrain_map.get(grid_id, '')
            label = f"{grid_id}\n{terrain[:4]}"
            ax.text(center[0], center[1], label, 
                   ha='center', va='center', fontsize=6, alpha=0.9)
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#90EE90', edgecolor='#228B22', linewidth=2, label='可部署Fence（边缘+地形允许）'),
        Patch(facecolor='#FFE4B5', edgecolor='#FF8C00', linewidth=2, label='边缘但地形限制'),
        Patch(facecolor='#F0F0F0', edgecolor='#AAAAAA', label='非边缘网格')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    # 设置图形属性
    ax.set_aspect('equal')
    ax.set_title('Fence Deployment Constraint\n(Fence can only be deployed on edge grids)', 
                fontsize=14, fontweight='bold')
    ax.set_xlabel('X Coordinate', fontsize=12)
    ax.set_ylabel('Y Coordinate', fontsize=12)
    
    # 设置边界
    bounds = grid_model.get_grid_bounds(hex_size)
    margin = 1.0
    ax.set_xlim(bounds[0] - margin, bounds[1] + margin)
    ax.set_ylim(bounds[2] - margin, bounds[3] + margin)
    
    plt.tight_layout()
    plt.savefig('./output/fence_constraint.png', dpi=200, bbox_inches='tight')
    print(f"  Fence约束可视化已保存到: ./output/fence_constraint.png")
    plt.close()


def test_full_optimization_with_fence_constraint():
    """使用Fence约束运行完整优化测试"""
    print("\n" + "=" * 70)
    print("使用Fence约束运行完整优化测试")
    print("=" * 70)
    
    from coverage_model import CoverageModel
    from dssa_optimizer import DSSAOptimizer, DSSAConfig
    
    # 设置随机种子
    np.random.seed(42)
    
    # 创建数据加载器
    data_loader = DataLoader()
    
    # 生成矩形六边形网格
    width, height = 12, 10
    grids = data_loader.generate_rectangular_hex_grid(width=width, height=height)
    print(f"\n生成网格: {width} x {height} = {len(grids)} 个网格")
    
    # 创建网格模型
    grid_model = HexGridModel(grids)
    edge_grids = grid_model.get_edge_grids()
    print(f"边缘网格数量: {len(edge_grids)}")
    
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
    
    # 初始化矩阵（带Fence边缘约束）
    data_loader.initialize_deployment_matrix(edge_grids=edge_grids)
    data_loader.initialize_visibility_params()
    
    # 创建覆盖模型
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
    
    # 验证Fence位置
    if stats['fence_edges']:
        print(f"\n围栏段数: {len(stats['fence_edges'])}")
        print(f"围栏部署验证:")
        
        invalid_fence = []
        for edge in stats['fence_edges']:
            grid1_id = edge[0]
            if grid1_id not in edge_grids:
                invalid_fence.append(grid1_id)
        
        if invalid_fence:
            print(f"  ❌ 错误: 以下Fence部署在非边缘网格: {invalid_fence}")
        else:
            print(f"  ✅ 验证通过: 所有Fence都部署在边缘网格")
    
    print("\n" + "=" * 70)
    print("Fence约束优化测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    # 测试Fence约束
    test_fence_constraint()
    
    # 运行完整优化测试
    test_full_optimization_with_fence_constraint()
