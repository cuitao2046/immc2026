#!/usr/bin/env python3
"""
演示：5个高风险网格，1个巡逻人员、1个无人机、1个摄像头
Square Grid Demo with 5 high-risk grids and 3 resources
"""

import os
import datetime
import random
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig
from square_grid_model import SquareGridModel

# 确保输出目录存在
output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

def run_demo():
    """运行演示"""
    print("=" * 80)
    print("演示：5个高风险网格，3个资源")
    print("Demo: 5 High-Risk Grids, 3 Resources")
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
    # 随机选择5个网格作为高风险网格
    total_grids = grid_width * grid_height
    high_risk_grids = random.sample(range(total_grids), 5)
    
    risk_map = {}
    terrain_map = {}
    
    for grid in optimizer.data_loader.grids:
        terrain_map[grid.grid_id] = 'SparseGrass'
        if grid.grid_id in high_risk_grids:
            risk_map[grid.grid_id] = 1.0
        else:
            risk_map[grid.grid_id] = 0.0
    
    optimizer.data_loader.set_terrain_types(terrain_map)
    optimizer.data_loader.set_risk_values(risk_map)
    
    print(f"      高风险网格: {high_risk_grids}")
    
    # 5. 设置约束
    print("[5/6] 设置约束...")
    constraints = {
        'total_patrol': 1,
        'total_camps': 1,  # 需要至少1个营地来部署巡逻人员
        'max_rangers_per_camp': 1,
        'total_cameras': 1,
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
    
    print(f"      巡逻人员: 1个")
    print(f"      无人机: 1个")
    print(f"      摄像头: 1个")
    print(f"      营地: 1个")
    
    # 6. 配置DSSA优化器
    print("[6/6] 配置DSSA优化器...")
    optimizer._initialize_models(grid_type='square')
    
    dssa_config = DSSAConfig(
        population_size=100,
        max_iterations=50,
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
    
    # 计算总覆盖网格数
    patrol_coverage = optimizer.coverage_model.calculate_patrol_coverage(best_solution)
    drone_coverage = optimizer.coverage_model.calculate_drone_coverage(best_solution)
    camera_coverage = optimizer.coverage_model.calculate_camera_coverage(best_solution)
    
    covered_grids = set()
    for grid_id, value in patrol_coverage.items():
        if value > 0.01:
            covered_grids.add(grid_id)
    for grid_id, value in drone_coverage.items():
        if value > 0.01:
            covered_grids.add(grid_id)
    for grid_id, value in camera_coverage.items():
        if value > 0.01:
            covered_grids.add(grid_id)
    
    # 9. 生成可视化
    print("=" * 80)
    print("生成可视化...")
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 风险热力图
    risk_map_path = os.path.join(output_dir, f'risk_heatmap_5risk_3res_{timestamp}.png')
    optimizer.visualizer.plot_risk_heatmap(save_path=risk_map_path, show=False)
    
    # 资源分布图
    deployment_map_path = os.path.join(output_dir, f'deployment_map_5risk_3res_{timestamp}.png')
    optimizer.visualizer.plot_deployment_map(best_solution, save_path=deployment_map_path, show=False)
    
    # 保护程度热力图
    protection_heatmap_path = os.path.join(output_dir, f'protection_heatmap_5risk_3res_{timestamp}.png')
    optimizer.visualizer.plot_protection_heatmap(best_solution, optimizer.coverage_model, 
                                               save_path=protection_heatmap_path, show=False)
    
    # 10. 输出结果
    print("=" * 80)
    print("优化结果")
    print("=" * 80)
    print(f"最优适应度: {best_fitness:.4f}")
    print(f"总保护效益: {total_benefit:.4f}")
    print(f"平均保护效益: {avg_benefit:.6f}")
    print(f"覆盖网格数: {len(covered_grids)} / {grid_width * grid_height}")
    
    print("=" * 80)
    print("资源部署")
    print("=" * 80)
    print(f"摄像头位置: {list(best_solution.cameras.keys())}")
    print(f"无人机位置: {list(best_solution.drones.keys())}")
    print(f"营地位置: {list(best_solution.camps.keys())}")
    print(f"巡逻人员位置: {list(best_solution.rangers.keys())}")
    
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
