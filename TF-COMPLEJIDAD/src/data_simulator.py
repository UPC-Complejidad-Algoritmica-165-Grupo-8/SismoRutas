# src/data_simulator.py

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import random
import numpy as np

def simulate_vial_network(base_lat, base_lon, num_grid_x, num_grid_y, spacing):
    """Simula los nodos y aristas de la red vial."""
    vial_nodes_coords = {}
    node_id_counter = 0
    for i in range(num_grid_x):
        for j in range(num_grid_y):
            node_id_counter += 1
            vial_nodes_coords[f'V_{node_id_counter}'] = (
                base_lon + (i - num_grid_x/2) * spacing + random.uniform(-spacing/4, spacing/4),
                base_lat + (j - num_grid_y/2) * spacing + random.uniform(-spacing/4, spacing/4)
            )

    red_vial_edges_data = []
    for i in range(num_grid_x):
        for j in range(num_grid_y):
            current_node_id = f'V_{i * num_grid_y + j + 1}'
            current_lon, current_lat = vial_nodes_coords[current_node_id]

            if j < num_grid_y - 1:
                right_node_id = f'V_{i * num_grid_y + (j + 1) + 1}'
                right_lon, right_lat = vial_nodes_coords[right_node_id]
                length = Point(current_lon, current_lat).distance(Point(right_lon, right_lat)) * 111000
                red_vial_edges_data.append({
                    'origen': current_node_id,
                    'destino': right_node_id,
                    'longitud': length,
                    'tipo_via': random.choice(['avenida', 'calle', 'pasaje']),
                    'riesgo_sismico_zona': random.choice(['bajo', 'medio', 'alto'])
                })

            if i < num_grid_x - 1:
                up_node_id = f'V_{(i + 1) * num_grid_y + j + 1}'
                up_lon, up_lat = vial_nodes_coords[up_node_id]
                length = Point(current_lon, current_lat).distance(Point(up_lon, up_lat)) * 111000
                red_vial_edges_data.append({
                    'origen': current_node_id,
                    'destino': up_node_id,
                    'longitud': length,
                    'tipo_via': random.choice(['avenida', 'calle', 'pasaje']),
                    'riesgo_sismico_zona': random.choice(['bajo', 'medio', 'alto'])
                })

    df_red_vial_edges = pd.DataFrame(red_vial_edges_data)
    gdf_vial_nodes = gpd.GeoDataFrame(
        pd.DataFrame(list(vial_nodes_coords.items()), columns=['node_id', 'coords']),
        geometry=gpd.points_from_xy([c[0] for c in vial_nodes_coords.values()], [c[1] for c in vial_nodes_coords.values()]),
        crs="EPSG:4326"
    )
    gdf_vial_nodes['lon'] = gdf_vial_nodes.geometry.x
    gdf_vial_nodes['lat'] = gdf_vial_nodes.geometry.y
    return df_red_vial_edges, gdf_vial_nodes

def simulate_critical_infrastructure(base_lat, base_lon, area_scale, num_infra):
    """Simula puntos de infraestructura crítica."""
    infra_critica_data = {
        'nombre': [f'IC_{i+1}' for i in range(num_infra)],
        'tipo': [random.choice(['hospital', 'refugio', 'estacion_rescate', 'centro_salud']) for _ in range(num_infra)],
        'latitud': [base_lat + random.uniform(-area_scale * 0.8, area_scale * 0.8) for _ in range(num_infra)],
        'longitud': [base_lon + random.uniform(-area_scale * 0.8, area_scale * 0.8) for _ in range(num_infra)]
    }
    df_infra_critica = pd.DataFrame(infra_critica_data)
    gdf_infra_critica = gpd.GeoDataFrame(
        df_infra_critica,
        geometry=gpd.points_from_xy(df_infra_critica.longitud, df_infra_critica.latitud),
        crs="EPSG:4326"
    )
    return gdf_infra_critica

def simulate_populated_zones(base_lat, base_lon, area_scale, num_zones):
    """Simula centroides de zonas pobladas (manzanas)."""
    zonas_pobladas_data = {
        'manzana_id': [f'M_{i+1}' for i in range(num_zones)],
        'latitud': [base_lat + random.uniform(-area_scale * 0.9, area_scale * 0.9) for _ in range(num_zones)],
        'longitud': [base_lon + random.uniform(-area_scale * 0.9, area_scale * 0.9) for _ in range(num_zones)],
        'poblacion': [random.randint(50, 500) for _ in range(num_zones)],
        'vulnerabilidad_nbi': [random.uniform(0.05, 0.5) for _ in range(num_zones)],
        'p_ge_0a14': [random.uniform(0.1, 0.3) for _ in range(num_zones)],
        'p_ge_65ym': [random.uniform(0.03, 0.15) for _ in range(num_zones)],
        'p_dl_mov': [random.uniform(0.005, 0.03) for _ in range(num_zones)]
    }
    df_zonas_pobladas = pd.DataFrame(zonas_pobladas_data)
    gdf_zonas_pobladas = gpd.GeoDataFrame(
        df_zonas_pobladas,
        geometry=gpd.points_from_xy(df_zonas_pobladas.longitud, df_zonas_pobladas.latitud),
        crs="EPSG:4326"
    )
    return gdf_zonas_pobladas

# Diccionario de riesgo sísmico (para usar en graph_builder)
RIESGO_PONDERACION = {
    'bajo': 1.0,
    'medio': 1.5,
    'alto': 2.5
}