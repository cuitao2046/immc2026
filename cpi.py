import math
import random
import heapq
from typing import Dict, List, Tuple, Callable, Optional

# -----------------------------
# 1) Basic geometry utilities
# -----------------------------

def dms_to_decimal(dms: str) -> float:
    """
    Convert DMS like 19°26'55.93"S or 14°24'43.35"E to decimal degrees.
    """
    dms = dms.strip()
    sign = -1 if dms.endswith(("S", "W")) else 1
    dms = dms[:-1]
    deg, rest = dms.split("°")
    minutes, rest = rest.split("'")
    seconds = rest.replace('"', '')
    return sign * (float(deg) + float(minutes) / 60 + float(seconds) / 3600)

def point_in_polygon(pt: Tuple[float, float], poly: List[Tuple[float, float]]) -> bool:
    """
    Ray casting algorithm. Works for non-self-intersecting polygon.
    pt = (lon, lat), poly is list of (lon, lat)
    """
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        # Check if edge crosses horizontal ray to the right of pt
        if ((y1 > y) != (y2 > y)):
            xinters = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-15) + x1
            if x < xinters:
                inside = not inside
    return inside

def dist2(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx*dx + dy*dy

# -----------------------------
# 2) Minimum Enclosing Circle
#    (for "外接圆" of 4 points)
# -----------------------------

def _circle_from_2_points(a, b):
    center = ((a[0]+b[0])/2, (a[1]+b[1])/2)
    r = math.sqrt(dist2(center, a))
    return center, r

def _circle_from_3_points(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax*(by-cy) + bx*(cy-ay) + cx*(ay-by))
    if abs(d) < 1e-12:
        return None
    ux = ((ax*ax+ay*ay)*(by-cy) + (bx*bx+by*by)*(cy-ay) + (cx*cx+cy*cy)*(ay-by)) / d
    uy = ((ax*ax+ay*ay)*(cx-bx) + (bx*bx+by*by)*(ax-cx) + (cx*cx+cy*cy)*(bx-ax)) / d
    center = (ux, uy)
    r = math.sqrt(dist2(center, a))
    return center, r

def _is_in_circle(p, center, r):
    return dist2(p, center) <= r*r + 1e-12

def minimum_enclosing_circle(points: List[Tuple[float, float]]) -> Tuple[Tuple[float, float], float]:
    """
    Welzl's randomized algorithm (expected linear time).
    Returns center and radius.
    """
    pts = points[:]
    random.shuffle(pts)
    center = pts[0]
    r = 0.0
    for i in range(len(pts)):
        p = pts[i]
        if not _is_in_circle(p, center, r):
            center = p
            r = 0.0
            for j in range(i):
                q = pts[j]
                if not _is_in_circle(q, center, r):
                    center, r = _circle_from_2_points(p, q)
                    for k in range(j):
                        s = pts[k]
                        if not _is_in_circle(s, center, r):
                            c = _circle_from_3_points(p, q, s)
                            if c is not None:
                                center, r = c
    return center, r

# -----------------------------
# 3) Fire risk model
# -----------------------------

def build_fire_risk_function(
    park_boundary: List[Tuple[float, float]],
    fire_quads: List[List[Tuple[float, float]]],
    combine: str = "max",  # "max" or "sum"
    radial_mode: str = "linear",  # "linear" or "gaussian"
    gaussian_alpha: float = 0.5
) -> Callable[[float, float], float]:
    """
    Create a function fire_risk(lon, lat) in [0,1].
    - Two quads -> each converted to minimum enclosing circle.
    - Risk increases from circle edge to center.
    """
    circles = []
    for quad in fire_quads:
        center, r = minimum_enclosing_circle(quad)
        circles.append((center, r))

    def risk_from_circle(lon, lat, center, r):
        d = math.sqrt(dist2((lon, lat), center))
        if d > r:
            return 0.0
        if radial_mode == "gaussian":
            # risk is highest at center, decays to edge
            # alpha controls spread; smaller = steeper
            return math.exp(- (d / (r * gaussian_alpha + 1e-12)) ** 2)
        # linear: 1 at center, 0 at edge
        return max(0.0, 1.0 - d / (r + 1e-12))

    def fire_risk(lon, lat):
        if not point_in_polygon((lon, lat), park_boundary):
            return 0.0
        risks = [risk_from_circle(lon, lat, c, r) for (c, r) in circles]
        if combine == "sum":
            return min(1.0, sum(risks))
        return max(risks)

    return fire_risk

# -----------------------------
# 4) Shortest-path travel time
# -----------------------------

def dijkstra_multi_source(
    nodes: List[int],
    neighbors: Dict[int, List[int]],
    terrain_cost: Dict[int, float],
    sources: List[int],
    blocked: Optional[Callable[[int], bool]] = None
) -> Dict[int, float]:
    """
    Dijkstra from multiple sources.
    - neighbors: adjacency list by node id
    - terrain_cost: cost to ENTER node (or you can precompute edge weights)
    - blocked: function(node_id)->bool (impassable)
    """
    INF = float("inf")
    dist = {n: INF for n in nodes}
    pq = []

    for s in sources:
        if blocked and blocked(s):
            continue
        dist[s] = 0.0
        heapq.heappush(pq, (0.0, s))

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v in neighbors.get(u, []):
            if blocked and blocked(v):
                continue
            w = terrain_cost.get(v, 1.0)
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist

# -----------------------------
# 5) CPI computation
# -----------------------------

def compute_cpi_for_cell(
    cell_id: int,
    species_id: str,
    device_type: str,
    params: Dict,
    precomp: Dict
) -> float:
    """
    device_type: 'none' | 'camera' | 'uav'
    """
    # Deterrence + verification
    if device_type == "none":
        D = 0.0
        eta = 0.0
    elif device_type == "camera":
        D = params["D_device"]
        eta = params["eta_camera"]
    elif device_type == "uav":
        D = params["D_device"]
        eta = params["eta_uav"]
    else:
        raise ValueError("Unknown device_type")

    # Travel time and survival
    T_c = precomp["T_c"][cell_id]
    if math.isinf(T_c):
        S = 0.0
    else:
        S = math.exp(-params["lambda"] * T_c)

    # Species weight (optionally activated by habitat)
    W_i = params["W"][species_id]
    if not precomp["species_active"][species_id].get(cell_id, True):
        W_i = params.get("W_base", 0.0)

    # Ecological penalty (only if device placed)
    Phi = 0.0
    if precomp["eco_sensitive"][cell_id] and device_type != "none":
        Phi = params["eco_penalty"]

    # Fire penalty (always applied)
    gamma_fire = precomp["fire_penalty"][cell_id]

    CPI = (D + (1.0 - D) * eta * S) * W_i - Phi - gamma_fire
    return CPI

# -----------------------------
# 6) End-to-end pipeline example
# -----------------------------

def build_and_compute_example():
    # ---- Park boundary (DMS -> decimal) ----
    park_boundary = [
        (dms_to_decimal("14°24'43.35\"E"), dms_to_decimal("19°26'55.93\"S")),
        (dms_to_decimal("14°15'46.12\"E"), dms_to_decimal("18°37'00.78\"S")),
        (dms_to_decimal("17°08'59.58\"E"), dms_to_decimal("18°29'09.57\"S")),
        (dms_to_decimal("17°06'34.10\"E"), dms_to_decimal("19°19'33.18\"S")),
    ]

    # ---- Two fire quads (already decimal) ----
    fire_quad_1 = [(16.595, -18.834), (17.116, -18.832), (16.552, -19.084), (17.093, -19.145)]
    fire_quad_2 = [(15.482, -19.289), (15.875, -19.310), (15.879, -19.114), (15.515, -19.140)]

    fire_risk_fn = build_fire_risk_function(
        park_boundary,
        [fire_quad_1, fire_quad_2],
        combine="max",
        radial_mode="linear"
    )

    # ---- Example cells (replace with your 982 hexes) ----
    # Each cell has id, lon, lat, terrain
    cells = {
        1: {"lon": 16.7, "lat": -18.95, "terrain": "road"},
        2: {"lon": 15.7, "lat": -19.2, "terrain": "grass"},
        3: {"lon": 16.2, "lat": -18.6, "terrain": "grass"},
    }

    # Example adjacency
    neighbors = {1: [2,3], 2:[1,3], 3:[1,2]}

    # Terrain weights (time cost)
    terrain_weight = {"road": 1.0, "grass": 3.0, "swamp": float("inf")}

    # Convert terrain to cost per node
    terrain_cost = {cid: terrain_weight[cells[cid]["terrain"]] for cid in cells}

    # Fire penalty values per cell
    # gamma_fire = gamma_max * risk
    gamma_max = 20.0
    fire_penalty = {}
    fire_risk = {}
    for cid, info in cells.items():
        r = fire_risk_fn(info["lon"], info["lat"])
        fire_risk[cid] = r
        fire_penalty[cid] = gamma_max * r

    # Fire blocking rule for travel
    fire_blocks_travel = True
    def blocked(cid):
        return fire_blocks_travel and fire_risk[cid] > 0.0

    # Camps (sources)
    camps = [1]  # example: cell 1 is a camp

    # Shortest travel time
    T_c = dijkstra_multi_source(
        nodes=list(cells.keys()),
        neighbors=neighbors,
        terrain_cost=terrain_cost,
        sources=camps,
        blocked=blocked
    )

    # Precomputed maps
    precomp = {
        "T_c": T_c,
        "eco_sensitive": {1: False, 2: True, 3: False},
        "fire_penalty": fire_penalty,
        "species_active": {
            "rhino": {1: True, 2: False, 3: True},
            "elephant": {1: True, 2: True, 3: False}
        }
    }

    # Parameters (tunable)
    params = {
        "lambda": 0.4,            # survival decay rate
        "D_device": 0.8,          # deterrence if device placed
        "eta_camera": 0.5,
        "eta_uav": 1.0,
        "eco_penalty": 50.0,      # may be large if you want hard constraint
        "W": {"rhino": 10.0, "elephant": 2.0},
        "W_base": 0.5             # optional baseline for non-habitat cells
    }

    # Compute CPI for each cell & species
    results = {}
    for cid in cells:
        for sp in ["rhino", "elephant"]:
            cpi = compute_cpi_for_cell(cid, sp, device_type="uav", params=params, precomp=precomp)
            results[(cid, sp)] = cpi

    return results

# Uncomment to run the example
# print(build_and_compute_example())