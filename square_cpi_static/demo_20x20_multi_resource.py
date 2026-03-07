import numpy as np
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig
import json
import os


def run_20x20_multi_resource_demo():
    """运行20x20网格多资源优化演示"""
    print("=" * 80)
    print("20x20网格多资源优化演示")
    print("20x20 Grid Multi-Resource Optimization Demo")
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
    print(f"摄像头: {stats['total_cameras']} / {constraints['total_cameras']}")
    print(f"无人机: {stats['total_drones']} / {constraints['total_drones']}")
    print(f"营地: {stats['total_camps']} / {constraints['total_camps']}")
    print(f"巡逻人员: {stats['total_rangers']} / {constraints['total_patrol']}")
    print(f"围栏长度: {stats['total_fence_length']} / {constraints['total_fence_length']}")
    
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
    print(f"覆盖网格数: {covered_grids}")
    
    # 打印地形分布
    print("=" * 80)
    print("地形分布")
    print("=" * 80)
    terrain_dist = optimizer.data_loader.get_terrain_distribution()
    for terrain, count in terrain_dist.items():
        total = sum(terrain_dist.values())
        percentage = (count / total) * 100
        print(f"{terrain:15}: {count:3} ({percentage:.1f}%)")
    
    # 打印高风险网格保护情况
    print("=" * 80)
    print("高风险网格保护情况")
    print("=" * 80)
    for grid_id in high_risk_grids:
        benefit = protection_benefit.get(grid_id, 0.0)
        print(f"网格 {grid_id}: 保护程度 = {benefit:.4f}")
    
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
        'terrain_distribution': terrain_dist,
        'high_risk_grids': high_risk_grids,
        'protection_benefit': {str(k): float(v) for k, v in protection_benefit.items()}
    }
    
    with open(f'{output_dir}/demo_20x20_multi_resource_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"结果已保存到: ./output/demo_20x20_multi_resource_results.json")
    
    # 生成可视化
    print("=" * 80)
    print("生成可视化...")
    print("=" * 80)
    
    # 生成综合部署图
    import matplotlib.pyplot as plt
    
    def plot_comprehensive_deployment(ax, grid_model, solution, terrain_map, hex_size):
        """绘制综合部署图"""
        grid_ids = grid_model.get_all_grid_ids()
        
        # 绘制网格
        for grid_id in grid_ids:
            corners = grid_model.get_grid_corners(grid_id, hex_size)
            terrain = terrain_map.get(grid_id, 'Unknown')
            
            # 根据地形类型设置颜色
            terrain_colors = {
                'SparseGrass': '#8DC63F',  # 浅绿色
                'DenseGrass': '#39B54A',   # 深绿色
                'SaltMarsh': '#FFDE59',     # 黄色
                'WaterHole': '#4A90E2',     # 蓝色
                'Road': '#808080'           # 灰色
            }
            
            color = terrain_colors.get(terrain, '#CCCCCC')
            
            polygon = plt.Polygon(corners, facecolor=color, edgecolor='gray', 
                             linewidth=0.3, alpha=0.8)
            ax.add_patch(polygon)
        
        # 摄像头 - 红色圆圈
        for grid_id in solution.cameras.keys():
            if solution.cameras[grid_id] > 0:
                center = grid_model.get_grid_center_coords(grid_id, hex_size)
                circle = plt.Circle(center, hex_size * 0.3, facecolor='red', 
                               edgecolor='darkred', linewidth=1.5, alpha=0.8, zorder=5)
                ax.add_patch(circle)
        
        # 无人机 - 蓝色三角形
        for grid_id in solution.drones.keys():
            if solution.drones[grid_id] > 0:
                center = grid_model.get_grid_center_coords(grid_id, hex_size)
                triangle = plt.Polygon([
                    (center[0], center[1] + hex_size * 0.3),
                    (center[0] - hex_size * 0.25, center[1] - hex_size * 0.2),
                    (center[0] + hex_size * 0.25, center[1] - hex_size * 0.2)
                ], facecolor='blue', edgecolor='darkblue', linewidth=1.5, alpha=0.8, zorder=5)
                ax.add_patch(triangle)
        
        # 巡逻人员 - 黄色五角星
        for grid_id in solution.rangers.keys():
            if solution.rangers[grid_id] > 0:
                center = grid_model.get_grid_center_coords(grid_id, hex_size)
                # 绘制五角星
                from matplotlib.patches import RegularPolygon
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
        
        # 营地 - 绿色方块
        for grid_id in solution.camps.keys():
            if solution.camps[grid_id] > 0:
                center = grid_model.get_grid_center_coords(grid_id, hex_size)
                square = plt.Rectangle(
                    (center[0] - hex_size * 0.2, center[1] - hex_size * 0.2),
                    hex_size * 0.4, hex_size * 0.4,
                    facecolor='green', edgecolor='darkgreen', linewidth=1.5, alpha=0.8, zorder=5
                )
                ax.add_patch(square)
        
        # 围栏 - 棕色线段
        for edge in solution.fences.keys():
            if solution.fences[edge] > 0:
                grid_id1, grid_id2 = edge
                center1 = grid_model.get_grid_center_coords(grid_id1, hex_size)
                center2 = grid_model.get_grid_center_coords(grid_id2, hex_size)
                line = plt.Line2D(
                    [center1[0], center2[0]],
                    [center1[1], center2[1]],
                    color='brown', linewidth=2.0, alpha=0.8, zorder=4
                )
                ax.add_line(line)
        
        # 设置边界
        bounds = grid_model.get_grid_bounds(hex_size)
        margin = 2.0
        ax.set_xlim(bounds[0] - margin, bounds[1] + margin)
        ax.set_ylim(bounds[2] - margin, bounds[3] + margin)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 添加图例
        import matplotlib.patches as mpatches
        legend_elements = []
        if solution.cameras:
            legend_elements.append(mpatches.Patch(facecolor='red', edgecolor='darkred', label=f"Camera ({len(solution.cameras)})"))
        if solution.drones:
            legend_elements.append(mpatches.Patch(facecolor='blue', edgecolor='darkblue', label=f"Drone ({len(solution.drones)})"))
        if solution.rangers:
            legend_elements.append(mpatches.Patch(facecolor='yellow', edgecolor='orange', label=f"Ranger ({sum(solution.rangers.values())})"))
        if solution.camps:
            legend_elements.append(mpatches.Patch(facecolor='green', edgecolor='darkgreen', label=f"Camp ({len(solution.camps)})"))
        if solution.fences:
            legend_elements.append(mpatches.Patch(facecolor='brown', edgecolor='brown', label=f"Fence ({len(solution.fences)})"))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    def calculate_protection_level(grid_model, solution, coverage_params, hex_size):
        """计算每个网格的保护程度"""
        grid_ids = grid_model.get_all_grid_ids()
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
            # 1. 巡逻覆盖
            patrol_intensity = 0.0
            # 来自营地的巡逻人员
            for camp_id in solution.camps.keys():
                rangers = solution.rangers.get(camp_id, 0)
                distance = grid_model.get_distance(grid_id, camp_id)
                patrol_intensity += rangers * np.exp(-distance / patrol_radius)
            # 直接部署的巡逻人员
            for ranger_id, ranger_count in solution.rangers.items():
                if ranger_count > 0 and ranger_id not in solution.camps:
                    distance = grid_model.get_distance(grid_id, ranger_id)
                    patrol_intensity += ranger_count * np.exp(-distance / patrol_radius)
            patrol_cov = 1 - np.exp(-patrol_intensity)
            
            # 2. 无人机覆盖
            drone_cov = 0.0
            for drone_id in solution.drones.keys():
                distance = grid_model.get_distance(grid_id, drone_id)
                if distance <= drone_radius * 2:
                    drone_cov += np.exp(-distance / drone_radius)
            drone_cov = min(1.0, drone_cov)
            
            # 3. 摄像头覆盖
            camera_cov = 0.0
            for cam_id in solution.cameras.keys():
                distance = grid_model.get_distance(grid_id, cam_id)
                if distance <= camera_radius * 2:
                    camera_cov += np.exp(-distance / camera_radius)
            camera_cov = min(1.0, camera_cov)
            
            # 4. 围栏保护
            fence_prot = 0.0
            neighbors = grid_model.get_neighbors(grid_id)
            for neighbor_id in neighbors:
                edge_key = tuple(sorted((grid_id, neighbor_id)))
                if edge_key in solution.fences and solution.fences[edge_key] > 0:
                    fence_prot += fence_protection
            fence_prot = min(1.0, fence_prot)
            
            # 综合保护程度
            protection = wp * patrol_cov + wd * drone_cov + wc * camera_cov + wf * fence_prot
            protection_level[grid_id] = min(1.0, protection)
        
        return protection_level
    
    def plot_protection_heatmap(ax, grid_model, solution, coverage_params, hex_size):
        """绘制保护程度热力图"""
        grid_ids = grid_model.get_all_grid_ids()
        
        # 计算保护程度
        protection_level = calculate_protection_level(grid_model, solution, coverage_params, hex_size)
        
        # 绘制保护程度热力图
        for grid_id in grid_ids:
            corners = grid_model.get_grid_corners(grid_id, hex_size)
            protection = protection_level.get(grid_id, 0.0)
            
            # 保护程度颜色：白色(低保护) -> 绿色(高保护)
            color_intensity = protection
            color = plt.cm.Greens(color_intensity)
            
            polygon = plt.Polygon(corners, facecolor=color, edgecolor='gray', 
                             linewidth=0.3, alpha=0.8)
            ax.add_patch(polygon)
        
        # 绘制资源位置
        for grid_id in solution.cameras.keys():
            if solution.cameras[grid_id] > 0:
                center = grid_model.get_grid_center_coords(grid_id, hex_size)
                circle = plt.Circle(center, hex_size * 0.2, facecolor='none', 
                               edgecolor='red', linewidth=1.5, zorder=5)
                ax.add_patch(circle)
        
        for grid_id in solution.drones.keys():
            if solution.drones[grid_id] > 0:
                center = grid_model.get_grid_center_coords(grid_id, hex_size)
                triangle = plt.Polygon([
                    (center[0], center[1] + hex_size * 0.2),
                    (center[0] - hex_size * 0.15, center[1] - hex_size * 0.1),
                    (center[0] + hex_size * 0.15, center[1] - hex_size * 0.1)
                ], facecolor='none', edgecolor='blue', linewidth=1.5, zorder=5)
                ax.add_patch(triangle)
        
        # 绘制巡逻人员位置
        for grid_id in solution.rangers.keys():
            if solution.rangers[grid_id] > 0:
                center = grid_model.get_grid_center_coords(grid_id, hex_size)
                # 绘制五角星轮廓
                from matplotlib.patches import RegularPolygon
                star = RegularPolygon(
                    (center[0], center[1]),
                    numVertices=5,
                    radius=hex_size * 0.2,
                    facecolor='none',
                    edgecolor='yellow',
                    linewidth=1.5,
                    zorder=5
                )
                ax.add_patch(star)
        
        for grid_id in solution.camps.keys():
            if solution.camps[grid_id] > 0:
                center = grid_model.get_grid_center_coords(grid_id, hex_size)
                square = plt.Rectangle(
                    (center[0] - hex_size * 0.15, center[1] - hex_size * 0.15),
                    hex_size * 0.3, hex_size * 0.3,
                    facecolor='none', edgecolor='green', linewidth=1.5, zorder=5
                )
                ax.add_patch(square)
        
        # 设置边界
        bounds = grid_model.get_grid_bounds(hex_size)
        margin = 2.0
        ax.set_xlim(bounds[0] - margin, bounds[1] + margin)
        ax.set_ylim(bounds[2] - margin, bounds[3] + margin)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 添加颜色条
        sm = plt.cm.ScalarMappable(cmap=plt.cm.Greens, norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Protection Level', rotation=270, labelpad=20)
        
        # 添加统计信息
        avg_protection = np.mean(list(protection_level.values()))
        max_protection = max(protection_level.values())
        min_protection = min(protection_level.values())
        
        stats_text = f"""
        Protection Statistics:
        - Average: {avg_protection:.3f}
        - Maximum: {max_protection:.3f}
        - Minimum: {min_protection:.3f}
        """
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    def plot_risk_heatmap(ax, grid_model, risk_map, hex_size):
        """绘制网格风险值热力图"""
        grid_ids = grid_model.get_all_grid_ids()
        
        # 绘制风险值热力图
        for grid_id in grid_ids:
            corners = grid_model.get_grid_corners(grid_id, hex_size)
            risk = risk_map.get(grid_id, 0.0)
            
            # 风险颜色：白色(低风险) -> 红色(高风险)
            color_intensity = risk
            color = plt.cm.Reds(color_intensity)
            
            polygon = plt.Polygon(corners, facecolor=color, edgecolor='gray', 
                             linewidth=0.3, alpha=0.8)
            ax.add_patch(polygon)
        
        # 设置边界
        bounds = grid_model.get_grid_bounds(hex_size)
        margin = 2.0
        ax.set_xlim(bounds[0] - margin, bounds[1] + margin)
        ax.set_ylim(bounds[2] - margin, bounds[3] + margin)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # 添加颜色条
        sm = plt.cm.ScalarMappable(cmap=plt.cm.Reds, norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Risk Level', rotation=270, labelpad=20)
    
    def plot_convergence_curve(ax, fitness_history):
        """绘制DSSA收敛曲线"""
        iterations = range(len(fitness_history))
        ax.plot(iterations, fitness_history, 'b-', linewidth=2, label='Fitness')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Fitness')
        ax.set_title('DSSA Convergence Curve', fontsize=14, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()

    def visualize_20x20_multi_resource_deployment(grid_model, solution, terrain_map, risk_map, results, coverage_params, fitness_history):
        """生成20x20网格多资源部署可视化图"""

        fig, axes = plt.subplots(2, 2, figsize=(30, 20))
        fig.suptitle('20x20 Grid Multi-Resource Deployment Visualization', fontsize=18, fontweight='bold')

        hex_size = 1.0
        grid_ids = grid_model.get_all_grid_ids()

        # 图1: 综合部署图
        ax1 = axes[0, 0]
        plot_comprehensive_deployment(ax1, grid_model, solution, terrain_map, hex_size)
        ax1.set_title('Resource Deployment', fontsize=14, fontweight='bold')

        # 图2: 保护程度热力图
        ax2 = axes[0, 1]
        plot_protection_heatmap(ax2, grid_model, solution, coverage_params, hex_size)
        ax2.set_title('Protection Level Heatmap', fontsize=14, fontweight='bold')

        # 图3: 网格风险值热力图
        ax3 = axes[1, 0]
        plot_risk_heatmap(ax3, grid_model, risk_map, hex_size)
        ax3.set_title('Grid Risk Value Heatmap', fontsize=14, fontweight='bold')

        # 图4: DSSA收敛曲线
        ax4 = axes[1, 1]
        plot_convergence_curve(ax4, fitness_history)

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        save_path = f'{output_dir}/20x20_multi_resource_deployment_visualization.png'
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return save_path

    # 生成可视化
    save_path = visualize_20x20_multi_resource_deployment(
        optimizer.grid_model,
        best_solution,
        terrain_map,
        risk_map,
        results,
        coverage_params,
        fitness_history
    )
    
    print(f"资源部署可视化图已保存到: {save_path}")
    
    print("=" * 80)
    print("演示完成!")
    print("=" * 80)


if __name__ == "__main__":
    run_20x20_multi_resource_demo()
