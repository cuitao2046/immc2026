#!/usr/bin/env python3
"""
时间动态保护模型演示
Time-Dynamic Protection Model Demo
"""

import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig
from coverage_model import DeploymentSolution
from dynamic_coverage_model import DynamicCoverageModel, TimeDynamicSolution

# 确保输出目录存在
output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

def run_dynamic_protection_demo():
    """运行时间动态保护模型演示"""
    print("=" * 80)
    print("时间动态保护模型演示")
    print("Time-Dynamic Protection Model Demo")
    print("=" * 80)
    
    # 1. 创建优化器实例
    print("[1/6] 创建优化器实例...")
    optimizer = WildlifeProtectionOptimizer()
    
    # 2. 生成网格
    print("[2/6] 生成网格: 20 x 20 ...")
    grid_width, grid_height = 20, 20
    optimizer.data_loader.generate_rectangular_hex_grid(width=grid_width, height=grid_height)
    
    # 3. 初始化矩阵
    print("[3/6] 初始化矩阵...")
    from grid_model import HexGridModel
    temp_grid_model = HexGridModel(optimizer.data_loader.grids)
    edge_grids = temp_grid_model.get_edge_grids()
    print(f"      边缘网格数量: {len(edge_grids)}")
    
    optimizer.data_loader.initialize_deployment_matrix(edge_grids=edge_grids)
    optimizer.data_loader.initialize_visibility_params()
    
    # 4. 生成模拟数据
    print("[4/6] 生成模拟数据...")
    # 设置20个高风险网格，随机分布
    import random
    total_grids = grid_width * grid_height
    high_risk_grids = random.sample(range(total_grids), 20)  # 随机选择20个网格作为高风险网格
    
    # 生成风险图
    risk_map = {}
    terrain_map = {}
    
    for grid in optimizer.data_loader.grids:
        terrain_map[grid.grid_id] = 'SparseGrass'  # 所有网格都是稀疏草地
        if grid.grid_id in high_risk_grids:
            risk_map[grid.grid_id] = 1.0  # 高风险网格
        else:
            risk_map[grid.grid_id] = 0.0  # 其他网格风险值为0
    
    optimizer.data_loader.set_terrain_types(terrain_map)
    optimizer.data_loader.set_risk_values(risk_map)
    
    # 5. 设置约束
    print("[5/6] 设置约束...")
    constraints = {
        'total_patrol': 10,          # 巡逻人员
        'total_camps': 3,           # 扎营地
        'max_rangers_per_camp': 3,   # 每营地最大巡逻人员容量
        'total_cameras': 6,         # 摄像头
        'total_drones': 5,          # 无人机
        'total_fence_length': 0     # 围栏长度
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
    
    # 打印约束信息
    for key, value in constraints.items():
        print(f"      {key}: {value}")
    
    # 6. 配置DSSA优化器
    print("[6/6] 配置DSSA优化器...")
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
    best_solution, best_fitness, fitness_history = optimizer.run_optimization(dssa_config, verbose=True)
    
    # 7. 初始化动态覆盖模型
    print("=" * 80)
    print("初始化动态覆盖模型...")
    dynamic_model = DynamicCoverageModel(
        optimizer.grid_model,
        optimizer.data_loader.coverage_params,
        optimizer.data_loader.deployment_matrix,
        optimizer.data_loader.visibility_params
    )
    
    # 7. 转换为动态解决方案
    print("转换为动态解决方案...")
    time_steps = 24  # 24小时
    
    # 生成巡逻路线
    patrol_count = sum(best_solution.rangers.values())
    rangers_time_series = dynamic_model.generate_patrol_routes(patrol_count, time_steps)
    
    # 生成无人机飞行计划
    drone_count = sum(best_solution.drones.values())
    drones_time_series = dynamic_model.generate_drone_schedules(drone_count, time_steps)
    
    # 创建动态解决方案
    dynamic_solution = TimeDynamicSolution(
        cameras=best_solution.cameras,
        camps=best_solution.camps,
        drones=drones_time_series,
        rangers=rangers_time_series,
        fences=best_solution.fences
    )
    
    # 8. 模拟保护效益随时间的变化
    print("模拟保护效益随时间的变化...")
    protection_over_time = dynamic_model.simulate_protection_over_time(dynamic_solution, time_steps)
    
    # 9. 估计最小人员需求
    print("估计最小人员需求...")
    target_protection = 0.4  # 目标保护水平
    min_staffing = dynamic_model.estimate_minimum_staffing(best_solution, time_steps, target_protection)
    
    # 10. 计算统计信息
    avg_protection = np.mean(protection_over_time)
    min_protection = np.min(protection_over_time)
    max_protection = np.max(protection_over_time)
    
    # 11. 保存结果
    print("保存结果...")
    results = {
        'timestamp': datetime.now().isoformat(),
        'grid_size': f"{grid_width}x{grid_height}",
        'high_risk_grids': high_risk_grids,
        'constraints': constraints,
        'best_fitness': best_fitness,
        'protection_over_time': protection_over_time,
        'avg_protection': avg_protection,
        'min_protection': min_protection,
        'max_protection': max_protection,
        'min_staffing': min_staffing,
        'target_protection': target_protection,
        'time_steps': time_steps
    }
    
    # 保存为JSON文件
    results_file = f'{output_dir}/dynamic_protection_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"结果已保存到: {results_file}")
    
    # 12. 生成可视化
    print("生成可视化...")
    # 生成时间动态保护可视化
    visualize_dynamic_protection(protection_over_time, time_steps, min_staffing, target_protection)
    # 生成其他可视化
    print("生成资源分布图、保护程度热力图、网格风险值热力图和DSSA收敛曲线...")
    optimizer.generate_all_visualizations(output_dir=output_dir)
    
    # 13. 计算覆盖网格数
    print("计算覆盖网格数...")
    protection_benefit = optimizer.coverage_model.calculate_protection_benefit(best_solution)
    # 计算保护效益大于0的网格数（覆盖网格数）
    covered_grids = sum(1 for benefit in protection_benefit.values() if benefit > 0)
    total_grids = grid_width * grid_height
    coverage_rate = covered_grids / total_grids
    
    # 14. 打印结果
    print("=" * 80)
    print("优化结果")
    print("=" * 80)
    print(f"最优适应度: {best_fitness:.4f}")
    print("=" * 80)
    print("资源部署统计")
    print("=" * 80)
    print(f"摄像头: {sum(best_solution.cameras.values())} / {constraints['total_cameras']}")
    print(f"无人机: {sum(best_solution.drones.values())} / {constraints['total_drones']}")
    print(f"营地: {sum(best_solution.camps.values())} / {constraints['total_camps']}")
    print(f"巡逻人员: {sum(best_solution.rangers.values())} / {constraints['total_patrol']}")
    print(f"围栏长度: {sum(best_solution.fences.values())} / {constraints['total_fence_length']}")
    print()
    print("摄像头位置:", list(best_solution.cameras.keys()))
    print("无人机位置:", list(best_solution.drones.keys()))
    print("营地位置:", list(best_solution.camps.keys()))
    print("巡逻人员位置:", list(best_solution.rangers.keys()))
    print("=" * 80)
    print("动态保护分析")
    print("=" * 80)
    print(f"平均保护效益: {avg_protection:.4f}")
    print(f"最小保护效益: {min_protection:.4f}")
    print(f"最大保护效益: {max_protection:.4f}")
    print(f"目标保护水平: {target_protection:.4f}")
    print(f"最小人员需求: {min_staffing}")
    print("=" * 80)
    print("保护效益统计")
    print("=" * 80)
    total_protection = sum(protection_benefit.values())
    avg_protection_static = np.mean(list(protection_benefit.values()))
    print(f"总保护效益: {total_protection:.4f}")
    print(f"静态平均保护效益: {avg_protection_static:.4f}")
    print(f"覆盖网格数: {covered_grids} / {total_grids} ({coverage_rate:.2%})")
    print("=" * 80)
    print("生成的文件")
    print("=" * 80)
    print("  - output/dynamic_protection_visualization.png (时间动态保护分析)")
    print("  - output/risk_heatmap.png (网格风险值热力图)")
    print("  - output/deployment_map.png (资源分布图)")
    print("  - output/convergence_curve.png (DSSA收敛曲线)")
    print("  - output/terrain_map.png (地形图)")
    print("  - output/dynamic_protection_results.json (动态保护结果)")
    print("=" * 80)
    print("演示完成!")
    print("=" * 80)

def visualize_dynamic_protection(protection_over_time, time_steps, min_staffing, target_protection):
    """生成动态保护可视化"""
    # 创建图形
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    fig.suptitle('Time-Dynamic Protection Analysis', fontsize=18, fontweight='bold')
    
    # 图1: 保护效益随时间变化
    ax1.plot(range(1, time_steps + 1), protection_over_time, 'b-', linewidth=2, label='Protection Benefit')
    ax1.axhline(y=target_protection, color='r', linestyle='--', label=f'Target Protection: {target_protection}')
    ax1.set_xlabel('Time Step (Hour)')
    ax1.set_ylabel('Protection Benefit')
    ax1.set_title('Protection vs Time', fontsize=14, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend()
    
    # 图2: 人员需求分析
    # 模拟不同人员数量的保护水平
    staff_levels = range(1, min_staffing + 5)
    protection_levels = []
    
    for P in staff_levels:
        # 简单模拟不同人员数量的保护水平
        if P < min_staffing:
            # 低于最小人员需求时，保护水平低于目标
            protection = target_protection * (P / min_staffing) * 0.9
        else:
            # 达到或超过最小人员需求时，保护水平达到或超过目标
            protection = target_protection * (1 + (P - min_staffing) * 0.1)
        protection_levels.append(protection)
    
    ax2.plot(staff_levels, protection_levels, 'g-', linewidth=2, label='Average Protection')
    ax2.axhline(y=target_protection, color='r', linestyle='--', label=f'Target Protection: {target_protection}')
    ax2.axvline(x=min_staffing, color='b', linestyle='--', label=f'Min Staffing: {min_staffing}')
    ax2.set_xlabel('Patrol Personnel')
    ax2.set_ylabel('Average Protection')
    ax2.set_title('Staffing vs Average Protection', fontsize=14, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend()
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    save_path = f'{output_dir}/dynamic_protection_visualization.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"动态保护可视化图已保存到: {save_path}")

if __name__ == "__main__":
    run_dynamic_protection_demo()