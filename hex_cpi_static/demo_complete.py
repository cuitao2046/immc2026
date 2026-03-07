import numpy as np
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig
from dynamic_coverage_model import DynamicCoverageModel
import json
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


def run_complete_demo():
    """运行完整的20x20网格优化演示，包含时间动态保护分析"""
    print("=" * 80)
    print("20x20网格完整优化演示 - 包含时间动态保护分析")
    print("Complete 20x20 Grid Optimization Demo with Time-Dynamic Protection Analysis")
    print("=" * 80)
    
    # 创建优化器实例
    optimizer = WildlifeProtectionOptimizer()
    
    # 设置20x20网格
    grid_width = 20
    grid_height = 20
    print(f"[1/5] 生成网格: {grid_width} x {grid_height} ...")
    optimizer.data_loader.generate_rectangular_hex_grid(width=grid_width, height=grid_height)
    
    # 初始化模型（需要先创建grid_model来获取边缘网格）
    from grid_model import HexGridModel
    temp_grid_model = HexGridModel(optimizer.data_loader.grids)
    edge_grids = temp_grid_model.get_edge_grids()
    print(f"      边缘网格数量: {len(edge_grids)}")
    
    # 初始化矩阵
    optimizer.data_loader.initialize_deployment_matrix(edge_grids=edge_grids)
    optimizer.data_loader.initialize_visibility_params()
    
    # 生成地形和风险
    print("[2/5] 构建网格模型...")
    optimizer._initialize_models()
    
    print("[3/5] 生成模拟数据...")
    # 设置20个高风险网格，随机分布
    import random
    random.seed(42)  # 设置随机种子以保证可重复性
    total_grids = grid_width * grid_height
    high_risk_grids = random.sample(range(total_grids), 20)  # 随机选择20个网格作为高风险网格
    terrain_map = {}
    risk_map = {}
    
    for grid in optimizer.data_loader.grids:
        terrain_map[grid.grid_id] = 'SparseGrass'  # 所有网格都是稀疏草地
        if grid.grid_id in high_risk_grids:
            risk_map[grid.grid_id] = 1.0  # 高风险网格
        else:
            risk_map[grid.grid_id] = 0.0  # 其他网格风险值为0
    
    optimizer.data_loader.set_terrain_types(terrain_map)
    optimizer.data_loader.set_risk_values(risk_map)
    
    # 设置约束
    print("[4/5] 设置约束...")
    constraints = {
        'total_patrol': 10,          # 巡逻人员
        'total_camps': 3,           # 扎营地
        'max_rangers_per_camp': 3,   # 每营地最大巡逻人员容量
        'total_cameras': 6,         # 摄像头
        'total_drones': 5,          # 无人机
        'total_fence_length': 0     # 围栏长度
    }
    optimizer.data_loader.set_constraints(**constraints)
    
    # 打印约束信息
    for key, value in constraints.items():
        print(f"      {key}: {value}")
    
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
    optimizer.data_loader.set_coverage_parameters(**coverage_params)
    
    # 重新初始化模型
    print("[5/5] 配置DSSA优化器...")
    optimizer._initialize_models()
    
    # 配置DSSA参数
    dssa_config = DSSAConfig(
        population_size=150,
        max_iterations=100,
        producer_ratio=0.2,
        scout_ratio=0.2,
        ST=0.8,
        R2=0.5
    )
    
    # 运行优化
    print("=" * 80)
    print("开始优化...")
    print("=" * 80)
    
    best_solution, best_fitness, fitness_history = optimizer.run_optimization(dssa_config, verbose=True)
    
    # 打印优化结果
    print("=" * 80)
    print("优化结果")
    print("=" * 80)
    print(f"最优适应度: {best_fitness:.4f}")
    
    # 打印资源部署统计
    print("=" * 80)
    print("资源部署统计")
    print("=" * 80)
    stats = optimizer.optimizer.get_solution_statistics(best_solution)
    print(f"摄像头: {stats['total_cameras']} / {constraints['total_cameras']} ✅")
    print(f"无人机: {stats['total_drones']} / {constraints['total_drones']} ✅")
    print(f"营地: {stats['total_camps']} / {constraints['total_camps']} ✅")
    print(f"巡逻人员: {stats['total_rangers']} / {constraints['total_patrol']} ✅")
    print(f"围栏长度: {stats['total_fence_length']} / {constraints['total_fence_length']} ✅")
    
    if stats['camera_locations']:
        print(f"\n摄像头位置: {stats['camera_locations']}")
    if stats['drone_locations']:
        print(f"无人机位置: {stats['drone_locations']}")
    if stats['ranger_locations']:
        print(f"巡逻人员位置: {stats['ranger_locations']}")
    if stats['camp_locations']:
        print(f"营地位置: {stats['camp_locations']}")
    
    # 计算保护效益
    print("=" * 80)
    print("保护效益分析")
    print("=" * 80)
    protection_benefit = optimizer.coverage_model.calculate_protection_benefit(best_solution)
    
    # 计算总风险 W = Σ R_i
    total_risk = 0.0
    for grid_id in optimizer.grid_model.get_all_grid_ids():
        total_risk += optimizer.grid_model.get_grid_risk(grid_id)
    
    # 计算风险权重归一化的总保护效益
    total_benefit_raw = sum(protection_benefit.values())
    total_benefit = total_benefit_raw / total_risk if total_risk > 0 else 0.0
    
    avg_benefit = np.mean(list(protection_benefit.values()))
    covered_grids = sum(1 for v in protection_benefit.values() if v > 0)
    
    print(f"总保护效益: {total_benefit:.4f}")
    print(f"平均保护效益: {avg_benefit:.4f}")
    print(f"覆盖网格数: {covered_grids} / {total_grids} ({covered_grids/total_grids*100:.2f}%)")
    
    # 时间动态保护分析
    print("=" * 80)
    print("时间动态保护分析")
    print("=" * 80)
    
    # 创建动态覆盖模型
    dynamic_model = DynamicCoverageModel(
        optimizer.grid_model,
        optimizer.data_loader.coverage_params,
        optimizer.data_loader.deployment_matrix,
        optimizer.data_loader.visibility_params
    )
    
    # 生成时间动态解决方案
    from dynamic_coverage_model import TimeDynamicSolution
    
    # 生成巡逻路线
    time_steps = 24  # 24小时
    patrol_routes = dynamic_model.generate_patrol_routes(
        stats['total_rangers'], time_steps
    )
    
    # 生成无人机飞行计划
    drone_schedules = dynamic_model.generate_drone_schedules(
        stats['total_drones'], time_steps
    )
    
    # 创建时间动态解决方案
    dynamic_solution = TimeDynamicSolution(
        cameras=best_solution.cameras,
        camps=best_solution.camps,
        drones=drone_schedules,
        rangers=patrol_routes,
        fences=best_solution.fences
    )
    
    # 模拟保护效益随时间变化
    protection_over_time = dynamic_model.simulate_protection_over_time(
        dynamic_solution, time_steps
    )
    
    # 计算时间动态统计
    avg_protection = np.mean(protection_over_time)
    min_protection = np.min(protection_over_time)
    max_protection = np.max(protection_over_time)
    
    print(f"平均保护效益: {avg_protection:.4f}")
    print(f"最小保护效益: {min_protection:.4f}")
    print(f"最大保护效益: {max_protection:.4f}")
    
    # 估计最小人员需求
    target_protection = 0.4
    min_staffing = dynamic_model.estimate_minimum_staffing(
        best_solution, time_steps, target_protection, max_patrol=20
    )
    print(f"目标保护水平: {target_protection:.4f}")
    print(f"最小人员需求: {min_staffing}")
    
    # 保存结果
    print("=" * 80)
    print("保存结果...")
    print("=" * 80)
    output_dir = './output'
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        'best_fitness': float(best_fitness),
        'fitness_history': [float(f) for f in fitness_history],
        'solution_stats': stats,
        'grid_count': optimizer.grid_model.get_grid_count(),
        'terrain_distribution': optimizer.data_loader.get_terrain_distribution(),
        'high_risk_grids': high_risk_grids,
        'protection_benefit': {str(k): float(v) for k, v in protection_benefit.items()},
        'total_benefit': float(total_benefit),
        'avg_benefit': float(avg_benefit),
        'covered_grids': covered_grids,
        'dynamic_protection': {
            'avg_protection': float(avg_protection),
            'min_protection': float(min_protection),
            'max_protection': float(max_protection),
            'protection_over_time': [float(p) for p in protection_over_time],
            'target_protection': target_protection,
            'min_staffing': min_staffing
        }
    }
    
    with open(f'{output_dir}/complete_demo_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"结果已保存到: ./output/complete_demo_results.json")
    
    # 生成所有可视化
    print("=" * 80)
    print("生成可视化...")
    print("=" * 80)
    
    hex_size = 1.0
    
    # 1. 资源分布图
    print("生成资源分布图...")
    fig, ax = plt.subplots(figsize=(16, 14))
    
    # 绘制地形背景
    grid_ids = optimizer.grid_model.get_all_grid_ids()
    terrain_colors = {
        'SparseGrass': '#8DC63F',
        'DenseGrass': '#39B54A',
        'SaltMarsh': '#FFDE59',
        'WaterHole': '#4A90E2',
        'Road': '#808080'
    }
    
    for grid_id in grid_ids:
        corners = optimizer.grid_model.get_grid_corners(grid_id, hex_size)
        terrain = terrain_map.get(grid_id, 'SparseGrass')
        color = terrain_colors.get(terrain, '#CCCCCC')
        polygon = plt.Polygon(corners, facecolor=color, edgecolor='gray', 
                             linewidth=0.3, alpha=0.8)
        ax.add_patch(polygon)
    
    # 绘制资源
    # 摄像头 - 红色圆圈
    for grid_id in best_solution.cameras.keys():
        if best_solution.cameras[grid_id] > 0:
            center = optimizer.grid_model.get_grid_center_coords(grid_id, hex_size)
            circle = plt.Circle(center, hex_size * 0.3, facecolor='red', 
                             edgecolor='darkred', linewidth=1.5, alpha=0.8, zorder=5)
            ax.add_patch(circle)
            ax.text(center[0], center[1], 'C', ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='white', zorder=6)
    
    # 无人机 - 蓝色三角形
    for grid_id in best_solution.drones.keys():
        if best_solution.drones[grid_id] > 0:
            center = optimizer.grid_model.get_grid_center_coords(grid_id, hex_size)
            triangle = plt.Polygon([
                (center[0], center[1] + hex_size * 0.3),
                (center[0] - hex_size * 0.25, center[1] - hex_size * 0.2),
                (center[0] + hex_size * 0.25, center[1] - hex_size * 0.2)
            ], facecolor='blue', edgecolor='darkblue', linewidth=1.5, alpha=0.8, zorder=5)
            ax.add_patch(triangle)
            ax.text(center[0], center[1], 'D', ha='center', va='center', 
                   fontsize=8, fontweight='bold', color='white', zorder=6)
    
    # 巡逻人员 - 黄色五角星
    from matplotlib.patches import RegularPolygon
    for grid_id in best_solution.rangers.keys():
        if best_solution.rangers[grid_id] > 0:
            center = optimizer.grid_model.get_grid_center_coords(grid_id, hex_size)
            star = RegularPolygon(
                (center[0], center[1]),
                numVertices=5,
                radius=hex_size * 0.25,
                facecolor='yellow',
                edgecolor='orange',
                linewidth=1.5,
                alpha=0.8,
                zorder=5
            )
            ax.add_patch(star)
            ax.text(center[0], center[1], 'P', ha='center', va='center', 
                   fontsize=7, fontweight='bold', color='black', zorder=6)
    
    # 营地 - 绿色方块
    for grid_id in best_solution.camps.keys():
        if best_solution.camps[grid_id] > 0:
            center = optimizer.grid_model.get_grid_center_coords(grid_id, hex_size)
            rangers = best_solution.rangers.get(grid_id, 0)
            square = plt.Rectangle(
                (center[0] - hex_size * 0.2, center[1] - hex_size * 0.2),
                hex_size * 0.4, hex_size * 0.4,
                facecolor='green', edgecolor='darkgreen', linewidth=1.5, alpha=0.8, zorder=5
            )
            ax.add_patch(square)
            ax.text(center[0], center[1], f'S\n{rangers}', ha='center', va='center', 
                   fontsize=7, fontweight='bold', color='white', zorder=6)
    
    # 设置边界
    bounds = optimizer.grid_model.get_grid_bounds(hex_size)
    margin = 2.0
    ax.set_xlim(bounds[0] - margin, bounds[1] + margin)
    ax.set_ylim(bounds[2] - margin, bounds[3] + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 添加图例
    import matplotlib.patches as mpatches
    legend_elements = [
        mpatches.Patch(facecolor='red', edgecolor='darkred', label=f"Camera ({stats['total_cameras']})"),
        mpatches.Patch(facecolor='blue', edgecolor='darkblue', label=f"Drone ({stats['total_drones']})"),
        mpatches.Patch(facecolor='yellow', edgecolor='orange', label=f"Ranger ({stats['total_rangers']})"),
        mpatches.Patch(facecolor='green', edgecolor='darkgreen', label=f"Camp ({stats['total_camps']})"),
        mpatches.Patch(facecolor='#8DC63F', label='Sparse Grass')
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=12)
    ax.set_title('Resource Deployment Map', fontsize=18, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/resource_deployment_map.png', dpi=300, bbox_inches='tight')
    print(f"  资源分布图已保存到: {output_dir}/resource_deployment_map.png")
    plt.close()
    
    # 2. 保护程度热力图
    print("生成保护程度热力图...")
    fig, ax = plt.subplots(figsize=(16, 14))
    
    # 计算保护程度
    protection_level = {}
    wp = coverage_params['wp']
    wd = coverage_params['wd']
    wc = coverage_params['wc']
    wf = coverage_params['wf']
    patrol_radius = coverage_params['patrol_radius']
    drone_radius = coverage_params['drone_radius']
    camera_radius = coverage_params['camera_radius']
    fence_protection = coverage_params['fence_protection']
    
    for grid_id in grid_ids:
        # 巡逻覆盖
        patrol_intensity = 0.0
        for camp_id in best_solution.camps.keys():
            rangers = best_solution.rangers.get(camp_id, 0)
            distance = optimizer.grid_model.get_distance(grid_id, camp_id)
            patrol_intensity += rangers * np.exp(-distance / patrol_radius)
        for ranger_id, ranger_count in best_solution.rangers.items():
            if ranger_count > 0 and ranger_id not in best_solution.camps:
                distance = optimizer.grid_model.get_distance(grid_id, ranger_id)
                patrol_intensity += ranger_count * np.exp(-distance / patrol_radius)
        patrol_cov = 1 - np.exp(-patrol_intensity)
        
        # 无人机覆盖
        drone_cov = 0.0
        for drone_id in best_solution.drones.keys():
            distance = optimizer.grid_model.get_distance(grid_id, drone_id)
            if distance <= drone_radius * 2:
                drone_cov += np.exp(-distance / drone_radius)
        drone_cov = min(1.0, drone_cov)
        
        # 摄像头覆盖
        camera_cov = 0.0
        for cam_id in best_solution.cameras.keys():
            distance = optimizer.grid_model.get_distance(grid_id, cam_id)
            if distance <= camera_radius * 2:
                camera_cov += np.exp(-distance / camera_radius)
        camera_cov = min(1.0, camera_cov)
        
        # 围栏保护
        fence_prot = 0.0
        neighbors = optimizer.grid_model.get_neighbors(grid_id)
        for neighbor_id in neighbors:
            edge_key = tuple(sorted((grid_id, neighbor_id)))
            if edge_key in best_solution.fences and best_solution.fences[edge_key] > 0:
                fence_prot += fence_protection
        fence_prot = min(1.0, fence_prot)
        
        # 综合保护程度
        protection = wp * patrol_cov + wd * drone_cov + wc * camera_cov + wf * fence_prot
        protection_level[grid_id] = min(1.0, protection)
    
    # 绘制保护程度热力图
    for grid_id in grid_ids:
        corners = optimizer.grid_model.get_grid_corners(grid_id, hex_size)
        protection = protection_level.get(grid_id, 0.0)
        color = plt.cm.Greens(protection)
        polygon = plt.Polygon(corners, facecolor=color, edgecolor='gray', 
                             linewidth=0.3, alpha=0.8)
        ax.add_patch(polygon)
    
    # 设置边界
    ax.set_xlim(bounds[0] - margin, bounds[1] + margin)
    ax.set_ylim(bounds[2] - margin, bounds[3] + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 添加颜色条
    sm = plt.cm.ScalarMappable(cmap=plt.cm.Greens, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Protection Level', rotation=270, labelpad=20, fontsize=12)
    
    # 添加统计信息
    stats_text = f"""
    Protection Statistics:
    - Average: {np.mean(list(protection_level.values())):.4f}
    - Maximum: {max(protection_level.values()):.4f}
    - Minimum: {min(protection_level.values()):.4f}
    - Covered Grids: {sum(1 for v in protection_level.values() if v > 0)} / {len(grid_ids)}
    """
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    ax.set_title('Protection Level Heatmap', fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/protection_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"  保护程度热力图已保存到: {output_dir}/protection_heatmap.png")
    plt.close()
    
    # 3. 网格风险值热力图
    print("生成网格风险值热力图...")
    fig, ax = plt.subplots(figsize=(16, 14))
    
    for grid_id in grid_ids:
        corners = optimizer.grid_model.get_grid_corners(grid_id, hex_size)
        risk = risk_map.get(grid_id, 0.0)
        color = plt.cm.Reds(risk)
        polygon = plt.Polygon(corners, facecolor=color, edgecolor='gray', 
                             linewidth=0.3, alpha=0.8)
        ax.add_patch(polygon)
    
    ax.set_xlim(bounds[0] - margin, bounds[1] + margin)
    ax.set_ylim(bounds[2] - margin, bounds[3] + margin)
    ax.set_aspect('equal')
    ax.axis('off')
    
    sm = plt.cm.ScalarMappable(cmap=plt.cm.Reds, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Risk Level', rotation=270, labelpad=20, fontsize=12)
    
    ax.set_title('Risk Value Heatmap', fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/risk_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"  网格风险值热力图已保存到: {output_dir}/risk_heatmap.png")
    plt.close()
    
    # 4. DSSA收敛曲线
    print("生成DSSA收敛曲线...")
    fig, ax = plt.subplots(figsize=(12, 6))
    
    iterations = range(len(fitness_history))
    ax.plot(iterations, fitness_history, 'b-', linewidth=2, label='Best Fitness')
    ax.set_xlabel('Iteration', fontsize=14)
    ax.set_ylabel('Fitness Value', fontsize=14)
    ax.set_title('DSSA Convergence Curve', fontsize=16, fontweight='bold')
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # 添加最终值标注
    ax.text(0.98, 0.95, f'Final Fitness: {best_fitness:.4f}', 
           transform=ax.transAxes, fontsize=12, verticalalignment='top',
           horizontalalignment='right', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/dssa_convergence_curve.png', dpi=300, bbox_inches='tight')
    print(f"  DSSA收敛曲线已保存到: {output_dir}/dssa_convergence_curve.png")
    plt.close()
    
    # 5. Time-Dynamic Protection Analysis
    print("生成时间动态保护分析图...")
    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1])
    
    # 5.1 保护效益随时间变化
    ax1 = fig.add_subplot(gs[0, :])
    time_points = range(1, time_steps + 1)
    ax1.plot(time_points, protection_over_time, 'b-', linewidth=2, label='Protection Benefit')
    ax1.axhline(y=avg_protection, color='r', linestyle='--', linewidth=2, label=f'Average: {avg_protection:.4f}')
    ax1.axhline(y=target_protection, color='g', linestyle='--', linewidth=2, label=f'Target: {target_protection:.4f}')
    ax1.set_xlabel('Time (Hours)', fontsize=12)
    ax1.set_ylabel('Protection Benefit', fontsize=12)
    ax1.set_title('Protection Benefit Over Time', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 1])
    
    # 5.2 人员需求分析
    ax2 = fig.add_subplot(gs[1, 0])
    staffing_levels = range(1, min_staffing + 5)
    staffing_benefits = []
    
    for P in staffing_levels:
        temp_routes = dynamic_model.generate_patrol_routes(P, time_steps)
        temp_solution = TimeDynamicSolution(
            cameras=best_solution.cameras,
            camps=best_solution.camps,
            drones=drone_schedules,
            rangers=temp_routes,
            fences=best_solution.fences
        )
        temp_protection = dynamic_model.simulate_protection_over_time(temp_solution, time_steps)
        staffing_benefits.append(np.mean(temp_protection))
    
    ax2.plot(staffing_levels, staffing_benefits, 'bo-', linewidth=2, markersize=8)
    ax2.axhline(y=target_protection, color='g', linestyle='--', linewidth=2, label=f'Target: {target_protection:.4f}')
    ax2.axvline(x=min_staffing, color='r', linestyle='--', linewidth=2, label=f'Min Staffing: {min_staffing}')
    ax2.set_xlabel('Number of Rangers', fontsize=12)
    ax2.set_ylabel('Average Protection Benefit', fontsize=12)
    ax2.set_title('Staffing Requirement Analysis', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([0, 1])
    
    # 5.3 保护效益分布
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.hist(protection_over_time, bins=20, color='skyblue', edgecolor='black', alpha=0.7)
    ax3.axvline(x=avg_protection, color='r', linestyle='--', linewidth=2, label=f'Average: {avg_protection:.4f}')
    ax3.axvline(x=min_protection, color='orange', linestyle='--', linewidth=2, label=f'Min: {min_protection:.4f}')
    ax3.axvline(x=max_protection, color='purple', linestyle='--', linewidth=2, label=f'Max: {max_protection:.4f}')
    ax3.set_xlabel('Protection Benefit', fontsize=12)
    ax3.set_ylabel('Frequency', fontsize=12)
    ax3.set_title('Protection Benefit Distribution', fontsize=14, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/time_dynamic_protection_analysis.png', dpi=300, bbox_inches='tight')
    print(f"  时间动态保护分析图已保存到: {output_dir}/time_dynamic_protection_analysis.png")
    plt.close()
    
    # 生成综合报告
    print("=" * 80)
    print("生成综合报告...")
    print("=" * 80)
    
    report = f"""
================================================================================
                    20x20网格优化演示 - 综合报告
                  Complete 20x20 Grid Optimization Report
================================================================================

一、配置参数 (Configuration Parameters)
--------------------------------------------------------------------------------
网格尺寸: {grid_width} x {grid_height} = {total_grids} 个网格
高风险网格: {len(high_risk_grids)} 个 (随机分布)

资源约束:
  - 巡逻人员: {constraints['total_patrol']} 个
  - 扎营地: {constraints['total_camps']} 个 (容量: {constraints['max_rangers_per_camp']} 人/营地)
  - 摄像头: {constraints['total_cameras']} 个
  - 无人机: {constraints['total_drones']} 个
  - 围栏长度: {constraints['total_fence_length']} 米

覆盖参数:
  - 巡逻半径: {coverage_params['patrol_radius']} 米
  - 无人机半径: {coverage_params['drone_radius']} 米
  - 摄像头半径: {coverage_params['camera_radius']} 米
  - 围栏保护: {coverage_params['fence_protection']}
  - 权重: w_p={coverage_params['wp']}, w_d={coverage_params['wd']}, w_c={coverage_params['wc']}, w_f={coverage_params['wf']}

DSSA参数:
  - 种群大小: {dssa_config.population_size}
  - 最大迭代: {dssa_config.max_iterations}
  - 生产者比例: {dssa_config.producer_ratio}
  - 侦察者比例: {dssa_config.scout_ratio}
  - 安全阈值: {dssa_config.ST}
  - 警戒值: {dssa_config.R2}

二、优化结果 (Optimization Results)
--------------------------------------------------------------------------------
最优适应度: {best_fitness:.4f}

资源部署统计:
  - 摄像头: {stats['total_cameras']} / {constraints['total_cameras']} ✅
  - 无人机: {stats['total_drones']} / {constraints['total_drones']} ✅
  - 营地: {stats['total_camps']} / {constraints['total_camps']} ✅
  - 巡逻人员: {stats['total_rangers']} / {constraints['total_patrol']} ✅
  - 围栏长度: {stats['total_fence_length']} / {constraints['total_fence_length']} ✅

部署位置:
  - 摄像头: {stats['camera_locations']}
  - 无人机: {stats['drone_locations']}
  - 巡逻人员: {stats['ranger_locations']}
  - 营地: {stats['camp_locations']}

三、保护效益分析 (Protection Benefit Analysis)
--------------------------------------------------------------------------------
静态保护效益:
  - 总保护效益: {total_benefit:.4f}
  - 平均保护效益: {avg_benefit:.4f}
  - 覆盖网格数: {covered_grids} / {total_grids} ({covered_grids/total_grids*100:.2f}%)

动态保护效益 (时间步长: {time_steps} 小时):
  - 平均保护效益: {avg_protection:.4f}
  - 最小保护效益: {min_protection:.4f}
  - 最大保护效益: {max_protection:.4f}
  - 目标保护水平: {target_protection:.4f}
  - 最小人员需求: {min_staffing} 人

四、高风险网格保护情况 (High-Risk Grid Protection)
--------------------------------------------------------------------------------
"""
    
    for i, grid_id in enumerate(high_risk_grids, 1):
        benefit = protection_benefit.get(grid_id, 0.0)
        protection = protection_level.get(grid_id, 0.0)
        report += f"  网格 {grid_id:3d}: 保护效益 = {benefit:.4f}, 保护程度 = {protection:.4f}\n"
    
    report += f"""
五、生成的可视化文件 (Generated Visualization Files)
--------------------------------------------------------------------------------
1. 资源分布图: {output_dir}/resource_deployment_map.png
2. 保护程度热力图: {output_dir}/protection_heatmap.png
3. 网格风险值热力图: {output_dir}/risk_heatmap.png
4. DSSA收敛曲线: {output_dir}/dssa_convergence_curve.png
5. 时间动态保护分析图: {output_dir}/time_dynamic_protection_analysis.png

六、数据文件 (Data Files)
--------------------------------------------------------------------------------
1. 完整结果数据: {output_dir}/complete_demo_results.json

================================================================================
                              演示完成！
                           Demo Completed Successfully!
================================================================================
"""
    
    print(report)
    
    # 保存报告到文件
    with open(f'{output_dir}/demo_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"综合报告已保存到: {output_dir}/demo_report.txt")
    
    print("=" * 80)
    print("所有可视化生成完成！")
    print("All visualizations generated successfully!")
    print("=" * 80)


if __name__ == "__main__":
    run_complete_demo()
