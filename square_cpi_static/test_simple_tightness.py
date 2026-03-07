import numpy as np
from data_loader import DataLoader
from grid_model import HexGridModel


def test_simple_tightness():
    """简单测试：检查相邻网格的中心距离"""
    print("=" * 70)
    print("简单测试：相邻网格中心距离")
    print("=" * 70)
    
    # 创建数据加载器
    data_loader = DataLoader()
    
    # 生成小网格
    grids = data_loader.generate_rectangular_hex_grid(width=3, height=3)
    
    print(f"\n生成 {len(grids)} 个网格 (3x3)")
    
    # 创建网格模型
    grid_model = HexGridModel(grids)
    
    hex_size = 1.0
    
    # 检查相邻网格的中心距离
    print("\n相邻网格中心距离:")
    print(f"{'Grid1':<8} {'Grid2':<8} {'距离':<10} {'预期':<10} {'状态'}")
    print("-" * 50)
    
    for grid in grids:
        neighbors = grid_model.get_neighbors(grid.grid_id)
        for neighbor_id in neighbors:
            if grid.grid_id < neighbor_id:  # 避免重复
                center1 = grid_model.get_grid_center_coords(grid.grid_id, hex_size)
                center2 = grid_model.get_grid_center_coords(neighbor_id, hex_size)
                
                dist = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
                expected = np.sqrt(3) * hex_size  # 相邻六边形中心距离 = sqrt(3) * hex_size
                
                status = "✅" if abs(dist - expected) < 0.01 else "❌"
                print(f"{grid.grid_id:<8} {neighbor_id:<8} {dist:.4f}    {expected:.4f}    {status}")
    
    # 检查网格坐标
    print("\n网格坐标和中心点:")
    print(f"{'Grid':<6} {'Q':<4} {'R':<4} {'Row':<4} {'Col':<4} {'X':<10} {'Y':<10}")
    print("-" * 50)
    
    for grid in grids:
        center = grid_model.get_grid_center_coords(grid.grid_id, hex_size)
        row = grid.r
        col = grid.q + (row // 2)
        print(f"{grid.grid_id:<6} {grid.q:<4} {grid.r:<4} {row:<4} {col:<4} {center[0]:<10.4f} {center[1]:<10.4f}")
    
    # 检查角点
    print("\n网格角点 (Grid 0):")
    corners = grid_model.get_grid_corners(0, hex_size)
    for i, corner in enumerate(corners):
        print(f"  角点 {i}: ({corner[0]:.4f}, {corner[1]:.4f})")
    
    print("\n网格角点 (Grid 1, Grid 0的邻居):")
    corners = grid_model.get_grid_corners(1, hex_size)
    for i, corner in enumerate(corners):
        print(f"  角点 {i}: ({corner[0]:.4f}, {corner[1]:.4f})")
    
    # 检查Grid 0和Grid 1是否共享边
    print("\n检查Grid 0和Grid 1是否共享边:")
    corners0 = grid_model.get_grid_corners(0, hex_size)
    corners1 = grid_model.get_grid_corners(1, hex_size)
    
    shared = False
    for i in range(6):
        edge0_start = corners0[i]
        edge0_end = corners0[(i + 1) % 6]
        
        for j in range(6):
            edge1_start = corners1[j]
            edge1_end = corners1[(j + 1) % 6]
            
            # 检查边是否重合
            if (abs(edge0_start[0] - edge1_start[0]) < 0.001 and 
                abs(edge0_start[1] - edge1_start[1]) < 0.001 and
                abs(edge0_end[0] - edge1_end[0]) < 0.001 and 
                abs(edge0_end[1] - edge1_end[1]) < 0.001):
                print(f"  ✅ 发现共享边: Grid 0角点{i}-{i+1} 与 Grid 1角点{j}-{j+1}")
                shared = True
                break
            elif (abs(edge0_start[0] - edge1_end[0]) < 0.001 and 
                  abs(edge0_start[1] - edge1_end[1]) < 0.001 and
                  abs(edge0_end[0] - edge1_start[0]) < 0.001 and 
                  abs(edge0_end[1] - edge1_start[1]) < 0.001):
                print(f"  ✅ 发现共享边: Grid 0角点{i}-{i+1} 与 Grid 1角点{j+1}-{j}")
                shared = True
                break
        
        if shared:
            break
    
    if not shared:
        print("  ❌ 未发现共享边")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_simple_tightness()
