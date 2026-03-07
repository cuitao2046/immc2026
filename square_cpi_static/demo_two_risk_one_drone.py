#!/usr/bin/env python3
"""
演示：2个高风险网格，1个无人机
Square Grid Demo with 2 high-risk grids and 1 drone
"""

import os
import datetime
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig
from square_grid_model import SquareGridModel

# 确保输出目录存在
output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

def run_demo():
    """运行演示"""
    print("=" * 80)
    print("演示：2个高风险网格，1个无人机")
    print("Demo: 2 High-Risk Grids, 1 Drone")
    print("=" * 80)
    
    # 1. 创建优化器实例
    print("[1/6] 创建优化器实例...")
    optimizer = WildlifeProtectionOptimizer()
    
    # 2. 生成正方形网格
    print("[2/6] 生成正方形网格: 20 x 20 ...")
    grid_width, grid_height = 20, 20
    optimizer.data_loader.generate_rectangular_square_grid(width=grid_width, height=grid_height)
    
    # 3. 初始化矩阵
    print("[3/6] 初始化矩阵...")
    temp_grid_model = SquareGridModel(optimizer.data_loader.grids)
    edge_grids = temp_grid_model.get_edge_grids()
    print(f"      边缘网格数量: {len(edge_grids)}")
    
    optimizer.data_loader.initialize_deployment_matrix(edge_grids=edge_grids)
    optimizer.data_loader.initialize_visibility_params()
    
    # 4. 设置风险值
    print("[4/6] 设置风险值...")
    # 左下角网格ID: 0 (x=0, y=0)
    # 右上角网格ID: 399 (x=19, y=19)
    left_bottom_id = 0
    right_top_id = 399
    
    risk_map = {}
    terrain_map = {}
    
    for grid in optimizer.data_loader.grids:
        terrain_map[grid.grid_id] = 'SparseGrass'
        if grid.grid_id == left_bottom_id or grid.grid_id == right_top_id:
            risk_map[grid.grid_id] = 1.0
        else:
            risk_map[grid.grid_id] = 0.0
    
    optimizer.data_loader.set_terrain_types(terrain_map)
    optimizer.data_loader.set_risk_values(risk_map)
    
    print(f"      高风险网格: {left_bottom_id} (左下角), {right_top_id} (右上角)")
    
    # 5. 设置约束（只有1个无人机）
    print("[5/6] 设置约束...")
    constraints = {
        'total_patrol': 0,
        'total_camps': 0,
        'max_rangers_per_camp': 0,
        'total_cameras': 0,
        'total_drones': 1,
        'total_fence_length': 0
    }
    optimizer.data_loader.set_constraints(**constraints)
    
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
    
    print(f"      无人机: 1个")
    print(f"      其他资源: 0")
    
    # 6. 配置DSSA优化器
    print("[6/6] 配置DSSA优化器...")
    optimizer._initialize_models(grid_type='square')
    
    dssa_config = DSSAConfig(
        population_size=50,
        max_iterations=30,
        producer_ratio=0.2,
        scout_ratio=0.2,
        ST=0.8,
        R2=0.5
    )
    
    # 7. 运行优化
    print("=" * 80)
    print("开始优化...")
    best_solution, best_fitness, fitness_history = optimizer.run_optimization(dssa_config, verbose=True)
    
    # 8. 计算指标
    print("=" * 80)
    print("计算保护指标...")
    
    # 总保护效益
    total_benefit = optimizer.coverage_model.calculate_total_benefit(best_solution)
    
    # 平均保护效益
    avg_benefit = total_benefit / (grid_width * grid_height)
    
    # 覆盖网格数（无人机覆盖的网格）
    drone_coverage = optimizer.coverage_model.calculate_drone_coverage(best_solution)
    covered_grids = sum(1 for v in drone_coverage.values() if v > 0.01)
    
    # 9. 生成可视化
    print("=" * 80)
    print("生成可视化...")
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 风险热力图
    risk_map_path = os.path.join(output_dir, f'risk_heatmap_2risk_1drone_{timestamp}.png')
    optimizer.visualizer.plot_risk_heatmap(save_path=risk_map_path, show=False)
    
    # 资源分布图
    deployment_map_path = os.path.join(output_dir, f'deployment_map_2risk_1drone_{timestamp}.png')
    optimizer.visualizer.plot_deployment_map(best_solution, save_path=deployment_map_path, show=False)
    
    # 保护程度热力图
    protection_heatmap_path = os.path.join(output_dir, f'protection_heatmap_2risk_1drone_{timestamp}.png')
    optimizer.visualizer.plot_protection_heatmap(best_solution, optimizer.coverage_model, 
                                               save_path=protection_heatmap_path, show=False)
    
    # 10. 输出结果
    print("=" * 80)
    print("优化结果")
    print("=" * 80)
    print(f"最优适应度: {best_fitness:.4f}")
    print(f"总保护效益: {total_benefit:.4f}")
    print(f"平均保护效益: {avg_benefit:.6f}")
    print(f"覆盖网格数: {covered_grids} / {grid_width * grid_height}")
    
    print("=" * 80)
    print("资源部署")
    print("=" * 80)
    print(f"无人机位置: {list(best_solution.drones.keys())}")
    
    print("=" * 80)
    print("可视化文件")
    print("=" * 80)
    print(f"风险热力图: {risk_map_path}")
    print(f"资源分布图: {deployment_map_path}")
    print(f"保护程度热力图: {protection_heatmap_path}")
    
    print("=" * 80)
    print("演示完成!")
    print("=" * 80)

if __name__ == "__main__":
    run_demo()
