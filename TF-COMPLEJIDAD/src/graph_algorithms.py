import networkx as nx
import heapq 

def find_shortest_path_dijkstra(graph, origin_node_id, target_nodes_ids):
    best_path_length = float('inf')
    best_target_node = None
    best_path = []

    lengths, paths_predecessors = nx.single_source_dijkstra(graph, source=origin_node_id, weight='weight')

    for target_id in target_nodes_ids:
        if target_id in lengths:
            current_path_length = lengths[target_id]
            if current_path_length < best_path_length:
                best_path_length = current_path_length
                best_target_node = target_id

    if best_target_node is not None:
        best_path = nx.shortest_path(graph, source=origin_node_id, target=best_target_node, weight='weight')

    return best_path, best_target_node, best_path_length

class DisjointSet:
    """
    Clase auxiliar para la estructura de datos Union-Find (Conjuntos Disjuntos).
    Esencial para el algoritmo de Kruskal para detectar ciclos.
    """
    def __init__(self, nodes):
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}

    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)

        if root_i != root_j:
            if self.rank[root_i] < self.rank[root_j]:
                self.parent[root_i] = root_j
            elif self.rank[root_i] > self.rank[root_j]:
                self.parent[root_j] = root_i
            else:
                self.parent[root_j] = root_i
                self.rank[root_i] += 1
            return True
        return False

def kruskal_mst(graph):
    """
    Implementación del algoritmo de Kruskal para encontrar el Árbol/Bosque de Expansión Mínima.
    Devuelve las aristas del MST/MSF y su costo total.
    """
    mst_edges = []
    total_cost = 0.0
    nodes = list(graph.nodes())
    if not nodes:
        return [], 0.0

    edges = []
    for u, v, data in graph.edges(data=True):
        if 'weight' in data:
            edges.append((data['weight'], u, v))
        else:
            print(f"Advertencia: La arista ({u}, {v}) no tiene atributo 'weight'. Se ignorará.")

    edges.sort()

    ds = DisjointSet(nodes)
    
    # Kruskal para un bosque de expansión mínima
    for weight, u, v in edges:
        if ds.union(u, v):
            mst_edges.append((u, v, {'weight': weight}))
            total_cost += weight
            
    # No se incluye la validación de grafo conectado aquí,
    # se permite el bosque de expansión mínima.

    return mst_edges, total_cost


def prim_mst(graph):
    """
    Implementación del algoritmo de Prim para encontrar el Árbol/Bosque de Expansión Mínima.
    Devuelve las aristas del MST/MSF y su costo total.
    """
    mst_edges = []
    total_cost = 0.0
    nodes = list(graph.nodes())
    num_nodes = len(nodes)

    if num_nodes == 0:
        return [], 0.0

    # Usaremos un conjunto para los nodos ya incluidos en el MST
    visited = set()

    # Cola de prioridad para las aristas (peso, u, v)
    # heapq mantiene el elemento más pequeño al inicio
    priority_queue = []

    # Diccionario para almacenar el costo mínimo para alcanzar cada nodo desde el MST
    # y la arista que lleva a ese nodo
    min_cost = {node: float('inf') for node in nodes}
    parent_edge = {node: None for node in nodes} # Para reconstruir el MST

    # Lista para almacenar los resultados del MST para cada componente conectado
    all_mst_edges = []
    all_total_costs = 0.0

    # Prim debe ejecutarse para cada componente conectado en el grafo
    # Si el grafo es desconectado, Prim encontrará un MSF
    for start_node in nodes:
        if start_node in visited:
            continue # Este nodo ya fue cubierto por un MST de un componente anterior

        # Inicializar para el componente actual
        current_mst_edges = []
        current_total_cost = 0.0
        
        min_cost[start_node] = 0 # El costo para el nodo inicial es 0
        heapq.heappush(priority_queue, (0, start_node, None)) # (costo, nodo_destino, nodo_origen)

        while priority_queue:
            weight, u, prev_v = heapq.heappop(priority_queue)

            if u in visited:
                continue

            visited.add(u) # Marcar el nodo como visitado (parte del MST)

            if prev_v is not None: # Si no es el nodo inicial del componente
                current_mst_edges.append((prev_v, u, {'weight': weight}))
                current_total_cost += weight
            
            # Explorar los vecinos del nodo 'u'
            for v, data in graph[u].items():
                edge_weight = data.get('weight')
                if edge_weight is None:
                    print(f"Advertencia: La arista ({u}, {v}) no tiene atributo 'weight'. Se ignorará.")
                    continue

                if v not in visited and edge_weight < min_cost[v]:
                    min_cost[v] = edge_weight
                    parent_edge[v] = (u, v, edge_weight) # Guarda la arista
                    heapq.heappush(priority_queue, (edge_weight, v, u))

        # Después de procesar un componente, añadir sus aristas al resultado final
        all_mst_edges.extend(current_mst_edges)
        all_total_costs += current_total_cost
        
        # Reiniciar min_cost y parent_edge para nodos no visitados, si hay más componentes
        # (Esto no es estrictamente necesario si `min_cost` solo se usa dentro del bucle de `start_node`)
        for node in nodes:
            if node not in visited:
                min_cost[node] = float('inf')
                parent_edge[node] = None

    return all_mst_edges, all_total_costs


def calculate_mst_for_distribution(graph_post_sismo, supply_center_id, distribution_points_ids, mst_algorithm='kruskal_custom'):
    """
    Calcula el Árbol de Expansión Mínimo para conectar un centro de abastecimiento
    con puntos de distribución, usando las rutas más cortas entre ellos.
    Permite seleccionar entre los algoritmos 'prim' y 'kruskal'.
    """
    mst_subgraph = nx.Graph()

    nodes_for_mst = [supply_center_id] + list(distribution_points_ids)

    for node_id in nodes_for_mst:
        if node_id in graph_post_sismo:
            mst_subgraph.add_node(node_id, pos=graph_post_sismo.nodes[node_id]['pos'])
        else:
            print(f"Advertencia: El nodo {node_id} (centro/punto de distribución) no existe en el grafo post-sismo y será ignorado para el MST.")


    for i in range(len(nodes_for_mst)):
        for j in range(i + 1, len(nodes_for_mst)):
            source = nodes_for_mst[i]
            target = nodes_for_mst[j]
            if source in graph_post_sismo and target in graph_post_sismo and \
               source in mst_subgraph and target in mst_subgraph:
                try:
                    path_length = nx.shortest_path_length(graph_post_sismo, source=source, target=target, weight='weight')
                    if path_length != float('inf'):
                        mst_subgraph.add_edge(source, target, weight=path_length)
                except nx.NetworkXNoPath:
                    pass

    if mst_subgraph.number_of_nodes() < 2:
        return [], 0.0

    try:
        if mst_algorithm == 'kruskal_custom':
            mst_edges, total_mst_cost = kruskal_mst(mst_subgraph) 
        elif mst_algorithm == 'prim':
            mst_edges, total_mst_cost = prim_mst(mst_subgraph) 
        else:
            raise ValueError("Algoritmo MST no reconocido. Use 'kruskal_custom' o 'prim'.")

        return mst_edges, total_mst_cost
    except Exception as e:
        print(f"Error al calcular MST con {mst_algorithm}: {e}. Posiblemente el subgrafo del MST está desconectado o no se puede formar un árbol.")
        return [], float('inf')


def analyze_post_earthquake_connectivity(graph_post_sismo):
    """
    Analiza la conectividad del grafo después de un sismo para identificar
    el componente conectado más grande y los nodos aislados.
    """
    if graph_post_sismo.is_directed():
        components = list(nx.weakly_connected_components(graph_post_sismo))
    else:
        components = list(nx.connected_components(graph_post_sismo))

    if not components:
        return set(), set(graph_post_sismo.nodes())

    largest_component = max(components, key=len)
    largest_component_nodes = set(largest_component)

    isolated_nodes = set()
    for component in components:
        if len(component) == 1:
            isolated_nodes.add(list(component)[0])
        else:
            isolated_nodes.update(component - largest_component_nodes)


    return largest_component_nodes, isolated_nodes