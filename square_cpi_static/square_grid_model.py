import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass
from data_loader import GridData


@dataclass
class SquareCoordinates:
    x: int
    y: int


class SquareGridModel:
    def __init__(self, grids: List[GridData]):
        self.grids = grids
        self.grid_dict = {grid.grid_id: grid for grid in grids}
        self.adjacency_matrix = self._build_adjacency_matrix()
        self.distance_matrix = self._build_distance_matrix()

    def _build_adjacency_matrix(self) -> Dict[int, List[int]]:
        adjacency = {}
        directions = [
            (1, 0), (-1, 0), (0, 1), (0, -1),  # 四邻域
            (1, 1), (1, -1), (-1, 1), (-1, -1)  # 八邻域
        ]

        for grid in self.grids:
            neighbors = []
            for dx, dy in directions:
                neighbor_x = grid.q + dx  # 用q表示x坐标
                neighbor_y = grid.r + dy  # 用r表示y坐标
                neighbor_grid = self._find_grid_by_coords(neighbor_x, neighbor_y)
                if neighbor_grid:
                    neighbors.append(neighbor_grid.grid_id)
            adjacency[grid.grid_id] = neighbors

        return adjacency

    def _build_distance_matrix(self) -> np.ndarray:
        n = len(self.grids)
        distance_matrix = np.zeros((n, n))

        for i, grid_i in enumerate(self.grids):
            for j, grid_j in enumerate(self.grids):
                distance_matrix[i][j] = self.square_distance(grid_i, grid_j)

        return distance_matrix

    def _find_grid_by_coords(self, x: int, y: int) -> GridData:
        for grid in self.grids:
            if grid.q == x and grid.r == y:
                return grid
        return None

    @staticmethod
    def square_distance(grid1: GridData, grid2: GridData) -> float:
        """计算正方形网格中两个网格的欧几里得距离"""
        dx = grid1.q - grid2.q
        dy = grid1.r - grid2.r
        return np.sqrt(dx**2 + dy**2)

    def get_distance(self, grid_id1: int, grid_id2: int) -> float:
        if grid_id1 not in self.grid_dict or grid_id2 not in self.grid_dict:
            return float('inf')
        grid1 = self.grid_dict[grid_id1]
        grid2 = self.grid_dict[grid_id2]
        return self.square_distance(grid1, grid2)

    def get_neighbors(self, grid_id: int) -> List[int]:
        return self.adjacency_matrix.get(grid_id, [])

    def get_all_grid_ids(self) -> List[int]:
        return list(self.grid_dict.keys())

    def get_grid_by_id(self, grid_id: int) -> GridData:
        return self.grid_dict.get(grid_id, None)

    def get_grid_center_coords(self, grid_id: int, square_size: float = 1.0) -> Tuple[float, float]:
        """获取正方形网格中心坐标"""
        grid = self.get_grid_by_id(grid_id)
        if not grid:
            return (0.0, 0.0)

        # 正方形网格的笛卡尔坐标
        x = grid.q * square_size + square_size / 2
        y = grid.r * square_size + square_size / 2
        return (x, y)

    def get_grid_corners(self, grid_id: int, square_size: float = 1.0) -> List[Tuple[float, float]]:
        """获取正方形网格的四个角点坐标"""
        center_x, center_y = self.get_grid_center_coords(grid_id, square_size)
        half_size = square_size / 2
        corners = [
            (center_x - half_size, center_y - half_size),
            (center_x + half_size, center_y - half_size),
            (center_x + half_size, center_y + half_size),
            (center_x - half_size, center_y + half_size)
        ]
        return corners

    def get_boundary_edges(self) -> List[Tuple[int, int, float]]:
        boundary_edges = []
        grid_ids = self.get_all_grid_ids()

        for grid_id in grid_ids:
            neighbors = self.get_neighbors(grid_id)
            for neighbor_id in neighbors:
                if grid_id < neighbor_id:
                    boundary_edges.append((grid_id, neighbor_id, 1.0))

        return boundary_edges

    def get_fencing_edges(self) -> List[Tuple[int, int, float]]:
        return self.get_boundary_edges()

    def get_grid_risk(self, grid_id: int) -> float:
        grid = self.get_grid_by_id(grid_id)
        return grid.risk if grid else 0.0

    def get_grid_terrain(self, grid_id: int) -> str:
        grid = self.get_grid_by_id(grid_id)
        return grid.terrain_type if grid else 'Unknown'

    def get_grids_by_terrain(self, terrain_type: str) -> List[int]:
        return [grid.grid_id for grid in self.grids if grid.terrain_type == terrain_type]

    def get_high_risk_grids(self, threshold: float = 0.7) -> List[int]:
        return [grid.grid_id for grid in self.grids if grid.risk >= threshold]

    def get_edge_grids(self) -> List[int]:
        """获取地图边缘的网格ID列表
        
        边缘网格定义为：
        1. 邻居数量少于8的网格（边界网格）
        2. 位于矩形地图边界的网格
        """
        edge_grids = []
        
        # 获取网格的行列范围
        xs = set()
        ys = set()
        grid_info = {}  # grid_id -> (x, y)
        
        for grid in self.grids:
            x = grid.q
            y = grid.r
            xs.add(x)
            ys.add(y)
            grid_info[grid.grid_id] = (x, y)
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        for grid_id, (x, y) in grid_info.items():
            # 检查是否为边缘网格
            is_edge = False
            
            # 1. 邻居数量少于8（边界网格）
            neighbors = self.get_neighbors(grid_id)
            if len(neighbors) < 8:
                is_edge = True
            
            # 2. 位于矩形地图边界
            if x == min_x or x == max_x or y == min_y or y == max_y:
                is_edge = True
            
            if is_edge:
                edge_grids.append(grid_id)
        
        return sorted(edge_grids)

    def get_grid_bounds(self, square_size: float = 1.0) -> Tuple[float, float, float, float]:
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for grid_id in self.get_all_grid_ids():
            corners = self.get_grid_corners(grid_id, square_size)
            for x, y in corners:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

        return (min_x, max_x, min_y, max_y)

    def get_grid_count(self) -> int:
        return len(self.grids)

    def get_distance_matrix(self) -> np.ndarray:
        return self.distance_matrix

    def get_adjacency_matrix(self) -> Dict[int, List[int]]:
        return self.adjacency_matrix