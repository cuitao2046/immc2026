#!/usr/bin/env python3
"""
正方形网格演示脚本
Square Grid Demo
"""

import os
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig

# 确保输出目录存在
output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

def run_square_grid_demo():
    """运行正方形网格演示"""
    print("=" * 80)
    print("正方形网格演示")
    print("Square Grid Demo")
    print("=" * 80)
    
    # 1. 创建优化器实例
    print("[1/5] 创建优化器实例...")
    optimizer = WildlifeProtectionOptimizer()
    
    # 2. 设置默认场景，使用正方形网格
    print("[2/5] 设置默认场景...")
    grid_width, grid_height = 20, 20
    optimizer.setup_default_scenario(
        grid_width=grid_width,
        height=grid_height,
        grid_type='square'  # 使用正方形网格
    )
    
    # 3. 配置DSSA优化器
    print("[3/5] 配置DSSA优化器...")
    dssa_config = DSSAConfig(
        population_size=100,
        max_iterations=50,
        producer_ratio=0.2,
        scout_ratio=0.2,
        ST=0.8,
        R2=0.5
    )
    
    # 4. 运行优化
    print("[4/5] 运行优化...")
    best_solution, best_fitness, fitness_history = optimizer.run_optimization(dssa_config, verbose=True)
    
    # 5. 生成可视化
    print("[5/5] 生成可视化...")
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 生成风险热力图
    risk_map_path = os.path.join(output_dir, f'risk_heatmap_square_{timestamp}.png')
    optimizer.visualizer.plot_risk_heatmap(save_path=risk_map_path, show=False)
    
    # 生成资源部署图
    deployment_map_path = os.path.join(output_dir, f'deployment_map_square_{timestamp}.png')
    optimizer.visualizer.plot_deployment_map(best_solution, save_path=deployment_map_path, show=False)
    
    # 生成收敛曲线
    convergence_curve_path = os.path.join(output_dir, f'convergence_curve_square_{timestamp}.png')
    optimizer.visualizer.plot_convergence_curve(fitness_history, save_path=convergence_curve_path, show=False)
    
    # 生成保护覆盖图
    protection_coverage_path = os.path.join(output_dir, f'protection_coverage_square_{timestamp}.png')
    optimizer.visualizer.plot_protection_coverage(best_solution, optimizer.coverage_model, 
                                               save_path=protection_coverage_path, show=False)
    
    # 生成地形图
    terrain_map_path = os.path.join(output_dir, f'terrain_map_square_{timestamp}.png')
    optimizer.visualizer.plot_terrain_map(save_path=terrain_map_path, show=False)
    
    # 6. 计算保护效益
    protection_benefit = optimizer.coverage_model.calculate_total_benefit(best_solution)
    
    # 7. 计算覆盖网格数（简化版本）
    covered_grids = len(set(list(best_solution.cameras.keys()) + list(best_solution.drones.keys()) + list(best_solution.camps.keys())))
    
    # 8. 输出结果
    print("=" * 80)
    print("优化结果")
    print("=" * 80)
    print(f"最优适应度: {best_fitness:.4f}")
    print(f"总保护效益: {protection_benefit:.4f}")
    print(f"覆盖网格数: {covered_grids} / {grid_width * grid_height}")
    print("=" * 80)
    print("资源部署统计")
    print("=" * 80)
    print(f"摄像头: {len(best_solution.cameras)} / {optimizer.data_loader.constraints.total_cameras}")
    print(f"无人机: {len(best_solution.drones)} / {optimizer.data_loader.constraints.total_drones}")
    print(f"营地: {len(best_solution.camps)} / {optimizer.data_loader.constraints.total_camps}")
    print(f"巡逻人员: {sum(best_solution.rangers.values())} / {optimizer.data_loader.constraints.total_patrol}")
    print(f"围栏长度: {sum(best_solution.fences.values())} / {optimizer.data_loader.constraints.total_fence_length}")
    
    print("\n摄像头位置:", list(best_solution.cameras.keys()))
    print("无人机位置:", list(best_solution.drones.keys()))
    print("营地位置:", list(best_solution.camps.keys()))
    print("巡逻人员位置:", list(best_solution.rangers.keys()))
    
    print("=" * 80)
    print("可视化文件已生成:")
    print(f"- 风险热力图: {risk_map_path}")
    print(f"- 资源部署图: {deployment_map_path}")
    print(f"- 收敛曲线: {convergence_curve_path}")
    print(f"- 保护覆盖图: {protection_coverage_path}")
    print(f"- 地形图: {terrain_map_path}")
    print("=" * 80)
    print("演示完成!")
    print("=" * 80)

if __name__ == "__main__":
    run_square_grid_demo()