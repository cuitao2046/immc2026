from risk_calculator import RiskCalculator, GridData, GeoFeature, RiskCoefficients


def create_sample_data():
    grids = [
        GridData(grid_id=1, center_lat=-18.5, center_lon=31.5, season=1),
        GridData(grid_id=2, center_lat=-18.6, center_lon=31.6, season=1),
        GridData(grid_id=3, center_lat=-18.7, center_lon=31.4, season=2),
        GridData(grid_id=4, center_lat=-18.8, center_lon=31.7, season=1),
        GridData(grid_id=5, center_lat=-18.9, center_lon=31.3, season=2),
    ]
    
    boundary = GeoFeature(
        name="保护区边界",
        coordinates=[(-18.0, 31.0), (-18.0, 32.0), (-19.0, 32.0), (-19.0, 31.0)]
    )
    
    roads = [
        GeoFeature(
            name="主路1",
            coordinates=[(-18.5, 31.0), (-18.5, 32.0)]
        ),
        GeoFeature(
            name="主路2",
            coordinates=[(-18.0, 31.5), (-19.0, 31.5)]
        )
    ]
    
    water_holes = [
        GeoFeature(name="水坑1", coordinates=[(-18.5, 31.5)]),
        GeoFeature(name="水坑2", coordinates=[(-18.6, 31.6)]),
        GeoFeature(name="水坑3", coordinates=[(-18.7, 31.4)]),
    ]
    
    fire_areas = [
        GeoFeature(name="火灾区域1", coordinates=[(-18.4, 31.4), (-18.4, 31.6), (-18.6, 31.6), (-18.6, 31.4)]),
        GeoFeature(name="火灾区域2", coordinates=[(-18.8, 31.2), (-18.8, 31.4), (-19.0, 31.4), (-19.0, 31.2)]),
    ]
    
    savanna = GeoFeature(
        name="稀树草原",
        coordinates=[(-18.5, 31.2), (-18.5, 31.8), (-18.8, 31.8), (-18.8, 31.2)]
    )
    
    jungle = GeoFeature(
        name="丛林",
        coordinates=[(-18.6, 31.3), (-18.6, 31.7), (-18.9, 31.7), (-18.9, 31.3)]
    )
    
    salt_marsh = GeoFeature(
        name="盐沼",
        coordinates=[(-18.7, 31.1), (-18.7, 31.5), (-19.0, 31.5), (-19.0, 31.1)]
    )
    
    rhino_areas = [
        GeoFeature(name="黑犀牛区域1", coordinates=[(-18.5, 31.4), (-18.5, 31.6), (-18.7, 31.6), (-18.7, 31.4)]),
        GeoFeature(name="黑犀牛区域2", coordinates=[(-18.8, 31.2), (-18.8, 31.4), (-19.0, 31.4), (-19.0, 31.2)]),
    ]
    
    ele_areas = [
        GeoFeature(name="大象区域1", coordinates=[(-18.4, 31.3), (-18.4, 31.7), (-18.6, 31.7), (-18.6, 31.3)]),
        GeoFeature(name="大象区域2", coordinates=[(-18.7, 31.1), (-18.7, 31.5), (-18.9, 31.5), (-18.9, 31.1)]),
    ]
    
    bird_areas = [
        GeoFeature(name="鸟类区域1", coordinates=[(-18.5, 31.2), (-18.5, 31.8), (-18.8, 31.8), (-18.8, 31.2)]),
        GeoFeature(name="鸟类区域2", coordinates=[(-18.6, 31.1), (-18.6, 31.5), (-18.9, 31.5), (-18.9, 31.1)]),
    ]
    
    return {
        'grids': grids,
        'boundary': boundary,
        'roads': roads,
        'water_holes': water_holes,
        'fire_areas': fire_areas,
        'savanna': savanna,
        'jungle': jungle,
        'salt_marsh': salt_marsh,
        'rhino_areas': rhino_areas,
        'ele_areas': ele_areas,
        'bird_areas': bird_areas
    }


def main():
    print("=== 网格风险严重程度计算器 ===\n")
    
    coeffs = RiskCoefficients(
        alpha_1=0.4,
        alpha_2=0.4,
        alpha_3=0.2,
        beta_1=0.5,
        beta_2=0.5,
        omega_1=0.6,
        omega_2=0.4,
        w_rhino=0.5,
        w_ele=0.3,
        w_bird=0.2
    )
    
    calculator = RiskCalculator(coefficients=coeffs)
    
    data = create_sample_data()
    
    print("风险系数设置:")
    print(f"  人为风险分配系数: α1={coeffs.alpha_1}, α2={coeffs.alpha_2}, α3={coeffs.alpha_3}")
    print(f"  环境风险分配系数: β1={coeffs.beta_1}, β2={coeffs.beta_2}")
    print(f"  综合调节权重: ω1={coeffs.omega_1}, ω2={coeffs.omega_2}")
    print(f"  物种价值权重: w_rhino={coeffs.w_rhino}, w_ele={coeffs.w_ele}, w_bird={coeffs.w_bird}\n")
    
    print("计算单个网格风险:")
    grid = data['grids'][0]
    R_prime = calculator.calculate_risk_score(
        grid=grid,
        boundary=data['boundary'],
        roads=data['roads'],
        water_holes=data['water_holes'],
        fire_areas=data['fire_areas'],
        savanna=data['savanna'],
        jungle=data['jungle'],
        salt_marsh=data['salt_marsh'],
        rhino_areas=data['rhino_areas'],
        ele_areas=data['ele_areas'],
        bird_areas=data['bird_areas'],
        fire_frequency=0.5
    )
    print(f"  网格 {grid.grid_id} 的原始风险值: {R_prime:.4f}\n")
    
    print("计算所有网格风险并归一化:")
    results = calculator.calculate_all_grids(
        grids=data['grids'],
        boundary=data['boundary'],
        roads=data['roads'],
        water_holes=data['water_holes'],
        fire_areas=data['fire_areas'],
        savanna=data['savanna'],
        jungle=data['jungle'],
        salt_marsh=data['salt_marsh'],
        rhino_areas=data['rhino_areas'],
        ele_areas=data['ele_areas'],
        bird_areas=data['bird_areas'],
        fire_frequency=0.5
    )
    
    print("  网格风险严重程度 (归一化到 [0, 100]):")
    for grid_id, risk_score in sorted(results.items()):
        print(f"    网格 {grid_id}: {risk_score:.2f}")
    
    print(f"\n最高风险网格: {max(results, key=results.get)} (风险值: {max(results.values()):.2f})")
    print(f"最低风险网格: {min(results, key=results.get)} (风险值: {min(results.values()):.2f})")
    print(f"平均风险值: {sum(results.values()) / len(results):.2f}")


if __name__ == "__main__":
    main()
