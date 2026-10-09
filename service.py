"""
Core spatial indexing, graph traversal, and location recommendation service.
"""

import os
import csv
import math
import hashlib
from collections import deque, defaultdict
from typing import List, Dict, Tuple, Optional, Union


class LocationService:
    def __init__(self, locations_csv_path: str, default_link_path: Optional[str] = None):
        self.locations_csv_path = os.path.abspath(locations_csv_path)
        self.default_link_path = os.path.abspath(default_link_path) if default_link_path else None
        
        # Data structures for locations
        # locations list: index -> (id, lat, lon, category)
        self.locations: List[Tuple[int, float, float, str]] = []
        self.id_to_index: Dict[int, int] = {}
        self.cat_to_indices: Dict[str, List[int]] = defaultdict(list)
        
        # Load and index locations
        self._load_locations()
        
        # Dynamically determine grid dimension (e.g. 100 for 10,000 locations)
        self.total_locations = len(self.locations)
        self.grid_size = int(round(math.sqrt(self.total_locations))) if self.total_locations > 0 else 100
        self.max_coord_index = self.grid_size - 1
        
        # Cache for parsed graphs: cache_key -> adjacency list
        self.graph_cache: Dict[str, List[List[int]]] = {}
        
        # Load default link graph if provided
        if self.default_link_path and os.path.isfile(self.default_link_path):
            self.default_adj = self.get_or_load_graph(self.default_link_path)
        else:
            self.default_adj = [[] for _ in range(self.total_locations + 1)]

    def _load_locations(self):
        """Loads and indexes locations from CSV."""
        with open(self.locations_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                lid = int(r["ID"])
                lat = float(r["Latitude"])
                lon = float(r["Longitude"])
                cat = r["Category"].strip().lower()
                
                idx = len(self.locations)
                self.locations.append((lid, lat, lon, cat))
                self.id_to_index[lid] = idx
                self.cat_to_indices[cat].append(idx)

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_or_load_graph(self, link_source: Optional[Union[str, bytes]]) -> List[List[int]]:
        """
        Retrieves graph from cache or parses from file path, URL or raw text.
        """
        if link_source is None:
            return self.default_adj

        if isinstance(link_source, bytes):
            link_source = link_source.decode("utf-8", errors="replace")

        link_str = link_source.strip()
        if not link_str or link_str.lower() in ("none", "null", "default"):
            return self.default_adj

        # Determine if link_source is a file on disk
        is_file = False
        resolved_path = link_str
        if "\n" not in link_str and len(link_str) < 4096:
            if os.path.isfile(link_str):
                is_file = True
                resolved_path = os.path.abspath(link_str)
            else:
                candidate = os.path.join(os.path.dirname(self.locations_csv_path), link_str)
                if os.path.isfile(candidate):
                    is_file = True
                    resolved_path = os.path.abspath(candidate)

        if is_file:
            mtime = os.path.getmtime(resolved_path)
            cache_key = f"file:{resolved_path}:{mtime}"
            if cache_key in self.graph_cache:
                return self.graph_cache[cache_key]
            with open(resolved_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            cache_key = f"content:{self._hash_content(link_str)}"
            if cache_key in self.graph_cache:
                return self.graph_cache[cache_key]
            content = link_str

        # Parse links into adjacency list
        total_nodes = self.total_locations if self.total_locations > 0 else 10000
        adj = [[] for _ in range(total_nodes + 1)]
        g_size = self.grid_size
        max_idx = self.max_coord_index

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 4:
                try:
                    lat1, lon1, lat2, lon2 = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
                    i1 = max(0, min(max_idx, round(lat1 * max_idx)))
                    j1 = max(0, min(max_idx, round(lon1 * max_idx)))
                    i2 = max(0, min(max_idx, round(lat2 * max_idx)))
                    j2 = max(0, min(max_idx, round(lon2 * max_idx)))
                    
                    # Rule: No diagonal links; links can ONLY exist between immediate orthogonal neighbors
                    if abs(i1 - i2) + abs(j1 - j2) != 1:
                        continue

                    u = i1 * g_size + j1 + 1
                    v = i2 * g_size + j2 + 1
                    
                    if 1 <= u <= total_nodes and 1 <= v <= total_nodes:
                        adj[u].append(v)
                        adj[v].append(u)
                except (ValueError, TypeError):
                    continue

        self.graph_cache[cache_key] = adj
        return adj

    def search(
        self,
        lat: float,
        lon: float,
        cat: str,
        rad: float,
        link: Optional[Union[str, bytes]] = None,
        top_k: int = 10,
    ) -> List[int]:
        """
        Recommends top_k closest location IDs matching category and radius.
        
        Filter:
          - category == cat (case-insensitive)
          - circular distance <= rad: math.hypot(loc_lat - lat, loc_lon - lon) <= rad
          
        Ranking:
          - Primary: grid traversal distance (shortest path on the road network)
          - Secondary: circular distance to (lat, lon)
          - Tertiary: location ID (ascending)
        """
        norm_cat = cat.strip().lower()
        matching_indices = self.cat_to_indices.get(norm_cat, [])
        if not matching_indices:
            return []

        # 1. Filter valid locations by circular distance (Euclidean in 1x1 grid)
        rad_sq = rad * rad + 1e-12
        valid_candidates = []  # list of (lid, circ_dist)
        target_ids = set()

        for idx in matching_indices:
            lid, l_lat, l_lon, _ = self.locations[idx]
            d_sq = (l_lat - lat) ** 2 + (l_lon - lon) ** 2
            if d_sq <= rad_sq:
                circ_d = math.sqrt(d_sq)
                valid_candidates.append((lid, circ_d))
                target_ids.add(lid)

        if not valid_candidates:
            return []

        # 2. Get adjacency list for the road network
        adj = self.get_or_load_graph(link) if link else self.default_adj

        # 3. Determine start node by snapping query point to grid
        max_idx = self.max_coord_index
        g_size = self.grid_size
        total_nodes = self.total_locations if self.total_locations > 0 else 10000

        i_start = max(0, min(max_idx, round(lat * max_idx)))
        j_start = max(0, min(max_idx, round(lon * max_idx)))
        start_node = i_start * g_size + j_start + 1

        # 4. BFS to calculate shortest path traversal distance on grid
        dist = [-1] * (total_nodes + 1)
        dist[start_node] = 0
        queue = deque([start_node])
        
        found_target_count = 0
        max_dist_at_cutoff = -1

        while queue:
            curr = queue.popleft()
            d = dist[curr]

            if curr in target_ids:
                found_target_count += 1
                if found_target_count >= top_k and max_dist_at_cutoff == -1:
                    max_dist_at_cutoff = d

            # If we found at least top_k candidates and finished the current distance level
            if max_dist_at_cutoff != -1 and d > max_dist_at_cutoff:
                break

            nd = d + 1
            for nxt in adj[curr]:
                if dist[nxt] == -1:
                    dist[nxt] = nd
                    queue.append(nxt)

        # 5. Rank valid candidates
        ranked = []
        for lid, circ_d in valid_candidates:
            g_dist = dist[lid]
            if g_dist != -1:  # Reachable via grid network
                ranked.append((g_dist, circ_d, lid))

        # Sort: primary=grid_dist, secondary=circ_dist, tertiary=lid
        ranked.sort()

        return [lid for _, _, lid in ranked[:top_k]]
