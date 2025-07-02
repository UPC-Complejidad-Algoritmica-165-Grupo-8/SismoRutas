# src/graph_builder.py

import networkx as nx
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial import cKDTree

# Función auxiliar para conectar puntos (infraestructura, zonas pobladas) a la red vial
def _add_and_connect_points(G, gdf_points, gdf_vial_nodes, node_type, id_col, additional_attrs):
    vial_coords_list = gdf_vial_nodes[['lon', 'lat']].values
    vial_node_ids = gdf_vial_nodes['node_id'].values
    kdtree = cKDTree(vial_coords_list)

    for index, row in gdf_points.iterrows():
        node_id = row[id_col]
        point_lon, point_lat = row.geometry.x, row.geometry.y

        G.add_node(node_id,
                   type=node_type,
                   pos=(point_lon, point_lat),
                   lon=point_lon,
                   lat=point_lat,
                   **{attr: row[attr] for attr in additional_attrs})

        distance, idx = kdtree.query([point_lon, point_lat])
        closest_vial_node_id = vial_node_ids[idx]
        access_weight = distance * 111000

        G.add_edge(node_id, closest_vial_node_id, weight=access_weight, type='access', subtype='out')
        G.add_edge(closest_vial_node_id, node_id, weight=access_weight, type='access', subtype='in')
    return G

def build_urban_graph(df_red_vial_edges, gdf_vial_nodes, gdf_infra_critica, gdf_zonas_pobladas, riesgo_ponderacion):
    """
    Construye el grafo urbano a partir de los datos proporcionados.
    """
    G = nx.DiGraph()

    # Añadir Nodos Viales
    for index, row in gdf_vial_nodes.iterrows():
        node_id = row['node_id']
        G.add_node(node_id,
                   type='vial',
                   pos=(row['lon'], row['lat']),
                   lon=row['lon'],
                   lat=row['lat'])

    # Añadir Nodos de Infraestructura Crítica y Zonas Pobladas y conectarlos a la red vial
    G = _add_and_connect_points(G, gdf_infra_critica, gdf_vial_nodes, 'critical_infra', 'nombre', ['tipo'])
    G = _add_and_connect_points(G, gdf_zonas_pobladas, gdf_vial_nodes, 'populated_zone', 'manzana_id',
                                ['poblacion', 'vulnerabilidad_nbi', 'p_ge_0a14', 'p_ge_65ym', 'p_dl_mov'])

    # Añadir Aristas de la Red Vial
    for index, row in df_red_vial_edges.iterrows():
        source_node = row['origen']
        target_node = row['destino']

        if source_node in G and target_node in G:
            weight = row['longitud']
            risk_factor = riesgo_ponderacion.get(row['riesgo_sismico_zona'], 1.0)
            weight *= risk_factor

            G.add_edge(source_node, target_node,
                       weight=weight,
                       type='road',
                       longitud=row['longitud'],
                       tipo_via=row['tipo_via'],
                       riesgo_sismico=row['riesgo_sismico_zona'])

            G.add_edge(target_node, source_node,
                       weight=weight,
                       type='road',
                       longitud=row['longitud'],
                       tipo_via=row['tipo_via'],
                       riesgo_sismico=row['riesgo_sismico_zona'])
    return G