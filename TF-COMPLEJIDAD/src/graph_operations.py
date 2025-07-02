# src/graph_operations.py

import networkx as nx
from math import radians, sin, cos, sqrt, atan2

# Constante para la aproximación de metros por grado de latitud/longitud
METERS_PER_DEGREE = 111000

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia Haversine entre dos puntos geográficos en metros.
    """
    R = 6371000  # Radio de la Tierra en metros

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def create_graph(data):
    """
    Crea un grafo NetworkX a partir de los datos procesados.
    Cada nodo tiene una posición (lat, lon) y un tipo.
    Las aristas tienen un 'weight' (distancia en metros).
    """
    G = nx.Graph()

    # Añadir nodos
    for node_id, attrs in data['nodes'].items():
        G.add_node(node_id, pos=(attrs['lon'], attrs['lat']), type=attrs['type'], subtype=attrs.get('subtype'))

    # Añadir aristas
    for edge_id, attrs in data['edges'].items():
        u = attrs['source']
        v = attrs['target']
        # Calcular peso basado en la distancia Haversine
        if u in G.nodes and v in G.nodes:
            lat1, lon1 = G.nodes[u]['pos'][1], G.nodes[u]['pos'][0]
            lat2, lon2 = G.nodes[v]['pos'][1], G.nodes[v]['pos'][0]
            distance = haversine_distance(lat1, lon1, lat2, lon2)
            G.add_edge(u, v, weight=distance, type=attrs['type'])
    return G

def apply_earthquake_damage(G_original, affected_nodes_data):
    """
    Aplica daños al grafo, marcando ciertas aristas como bloqueadas.
    Retorna un nuevo grafo con los cambios.
    """
    G_post_sismo = G_original.copy()
    for edge_id, status in affected_nodes_data.items():
        if status == 'blocked':
            u, v = G_post_sismo.edges[edge_id]['source'], G_post_sismo.edges[edge_id]['target']
            # Para simular un bloqueo total, podemos remover la arista o asignarle un peso infinito.
            # Remover la arista es más directo para Dijkstra y Bellman-Ford.
            if G_post_sismo.has_edge(u, v):
                G_post_sismo.remove_edge(u, v)
            elif G_post_sismo.has_edge(v, u): # Considerar aristas no dirigidas
                 G_post_sismo.remove_edge(v, u)
            # También podríamos añadir un atributo 'blocked' para la visualización
            # G_post_sismo.edges[u,v]['blocked'] = True # Esto no funcionaría si se remueve

            # Para la visualización, necesitamos saber qué aristas estaban bloqueadas en el original
            # pero no las eliminamos completamente, sino que las marcamos y asignamos un peso muy alto
            # para Dijkstra. Para Bellman-Ford, es mejor simplemente quitarlas si el peso es infinito.
            # Una estrategia es crear un grafo 'con_bloqueos_marcados' para visualización
            # y otro 'sin_bloqueos_para_algoritmos'
    
    # Para el propósito de visualización y Bellman-Ford/Dijkstra,
    # es mejor simplemente quitar las aristas bloqueadas del grafo que se pasa a los algoritmos.
    # La información de "bloqueado" para la visualización se manejará aparte.

    # Regresamos el grafo sin las aristas bloqueadas para los cálculos
    return G_post_sismo


def find_shortest_path_dijkstra(G, start_node, end_node):
    """
    Encuentra la ruta más corta usando Dijkstra.
    Retorna la ruta y el costo total.
    """
    try:
        path = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
        cost = nx.shortest_path_length(G, source=start_node, target=end_node, weight='weight')
        return path, cost
    except nx.NetworkXNoPath:
        return None, float('inf')


def find_mst(G, start_node=None):
    """
    Calcula el Árbol de Expansión Mínimo (MST) del grafo G.
    Retorna una lista de aristas que forman el MST.
    Si se proporciona un start_node, se asegura que el MST conecte ese nodo
    a los demás componentes o sea el centro si el grafo es conectado.
    """
    if not nx.is_connected(G):
        # Si el grafo no está conectado, Kruskal puede encontrar un bosque de expansión mínimo.
        # Necesitamos decidir si queremos el MST de cada componente o unificarlos.
        # Para un problema de distribución, usualmente esperamos un grafo conectado.
        # Para simplificar, asumiremos que G es el subgrafo relevante para el MST.
        print("Advertencia: El grafo no está completamente conectado para el MST. Se calculará un bosque de expansión mínimo.")
    
    # Usamos Kruskal para encontrar el MST
    mst_edges = list(nx.tree.minimum_spanning_edges(G, weight='weight', data=True))
    return mst_edges


def bellman_ford_path(G_original, start_node, end_node, reabastecimiento_points_benefits=None):
    """
    Encuentra la ruta más eficiente usando Bellman-Ford, considerando beneficios (pesos negativos)
    en puntos de reabastecimiento.

    Args:
        G_original (nx.Graph): El grafo original con pesos de distancia positivos.
        start_node: El nodo de inicio de la ruta.
        end_node: El nodo de destino de la ruta.
        reabastecimiento_points_benefits (dict): Un diccionario donde las claves son IDs de nodos
                                                 de reabastecimiento y los valores son los beneficios
                                                 (ej. {'R1': 1000, 'R5': 500}). Estos se convierten
                                                 a pesos negativos.

    Returns:
        tuple: Una tupla (path, cost) de la ruta más eficiente y su costo neto,
               o (None, float('inf')) si no hay ruta o se detecta un ciclo negativo.
    """
    # Crear un grafo temporal para Bellman-Ford que pueda tener pesos negativos
    G_bellman = G_original.copy()

    # Aplicar beneficios como pesos negativos a las aristas que *llegan* a los puntos de reabastecimiento.
    # O, una forma más robusta es crear un "subgrafo" virtual para cada beneficio
    # Es más sencillo aplicar el beneficio al nodo: crear una arista ficticia con peso negativo
    # desde un nodo dummy o ajustar el peso de las aristas entrantes.
    # Una forma práctica para Bellman-Ford es ajustar los pesos de las aristas *que salen*
    # de un nodo inmediatamente después de pasar por él, si ese nodo es un punto de reabastecimiento.
    # Sin embargo, Bellman-Ford busca el camino más corto, así que un costo negativo
    # al llegar a un nodo es más intuitivo.

    # La forma estándar de modelar beneficios en nodos para algoritmos de caminos es
    # asociar el costo negativo a una arista saliente del nodo de beneficio, o
    # ajustar los pesos de las aristas de llegada.
    # Para simplicidad y claridad, asociaremos el beneficio a la arista *que llega* al nodo de reabastecimiento.
    # Esto significa que el "costo" de la última etapa para llegar a un punto de reabastecimiento se reduce.
    
    if reabastecimiento_points_benefits:
        for node_id, benefit in reabastecimiento_points_benefits.items():
            if node_id in G_bellman.nodes:
                # Iterar sobre las aristas que llegan a este nodo
                for u, v, data in G_bellman.in_edges(node_id, data=True):
                    # Solo modificamos si 'v' es el nodo de reabastecimiento
                    if v == node_id:
                        # Asegurarse de que el peso original es numérico
                        original_weight = data.get('weight', 0)
                        # Aplicar el beneficio como una reducción del costo
                        G_bellman[u][v]['weight'] = original_weight - benefit
                        # print(f"Arista ({u}, {v}) peso modificado de {original_weight:.2f} a {G_bellman[u][v]['weight']:.2f} (beneficio: {benefit})")

    try:
        # NetworkX tiene una implementación de Bellman-Ford
        path = nx.bellman_ford_path(G_bellman, source=start_node, target=end_node, weight='weight')
        cost = nx.bellman_ford_path_length(G_bellman, source=start_node, target=end_node, weight='weight')
        return path, cost
    except nx.NetworkXNoPath:
        return None, float('inf')
    except nx.NetworkXUnbounded:
        print("¡Advertencia: Se detectó un ciclo de peso negativo! La ruta es indeterminada.")
        return None, float('-inf') # Representa un costo ilimitadamente bajo (problema)