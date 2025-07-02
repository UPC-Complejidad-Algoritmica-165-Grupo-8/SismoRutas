import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import warnings
from collections import Counter

warnings.filterwarnings("ignore", category=UserWarning)

def plot_full_graph(graph, title="Red Urbana Simulada"):
    plt.figure(figsize=(14, 10))
    ax = plt.gca() 
    pos = nx.get_node_attributes(graph, 'pos')

    node_colors = []
    node_sizes = []
    
    node_type_counts = Counter()
    
    node_type_info = {
        'hospital': {'color': 'red', 'label': 'Hospital', 'size': 200},
        'estacion_rescate': {'color': 'blue', 'label': 'Estación Rescate', 'size': 200},
        'refugio': {'color': 'lightgreen', 'label': 'Refugio', 'size': 150},
        'centro_salud': {'color': 'purple', 'label': 'Centro Salud', 'size': 150},
        'populated_zone': {'color': 'yellow', 'label': 'Zona Poblada (Manzana)', 'size': 50},
        'vial': {'color': 'gray', 'label': 'Nodo Vial', 'size': 20},
        'other_critical_infra': {'color': 'orange', 'label': 'Otra Infra. Crítica', 'size': 100}
    }

    for node, data in graph.nodes(data=True):
        node_type = 'vial'
        if data.get('type') == 'critical_infra':
            tipo_infra = data.get('tipo')
            if tipo_infra in node_type_info:
                node_type = tipo_infra
            else:
                node_type = 'other_critical_infra'
        elif data.get('type') == 'populated_zone':
            node_type = 'populated_zone'
        
        node_type_counts[node_type] += 1
        
        info = node_type_info[node_type]
        node_colors.append(info['color'])
        node_sizes.append(info['size'])

    nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=node_sizes, alpha=0.8, ax=ax) 

    edge_colors = ['#888888' for u, v, d in graph.edges(data=True)]
    edge_widths = [0.5 for u, v, d in graph.edges(data=True)]

    for i, (u, v, data) in enumerate(graph.edges(data=True)):
        if 'riesgo_sismico' in data:
            if data['riesgo_sismico'] == 'alto':
                edge_colors[i] = 'orange'
                edge_widths[i] = 1.0
            elif data['riesgo_sismico'] == 'medio':
                edge_colors[i] = 'cyan'
                edge_widths[i] = 0.8

    nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, width=edge_widths, alpha=0.7, ax=ax) 

    from matplotlib.lines import Line2D
    
    legend_elements_nodes = []
    for key, info in node_type_info.items():
        if node_type_counts[key] > 0:
            legend_elements_nodes.append(
                Line2D([0], [0], marker='o', color='w', label=info['label'], markerfacecolor=info['color'], markersize=10)
            )

    legend_elements_edges = [
        Line2D([0], [0], color='orange', lw=2, label='Arista Alto Riesgo'),
        Line2D([0], [0], color='cyan', lw=2, label='Arista Medio Riesgo'),
        Line2D([0], [0], color='#888888', lw=2, label='Arista Normal'),
    ]

    ax.legend(handles=legend_elements_nodes + legend_elements_edges, loc='lower left', bbox_to_anchor=(1, 0)) 
    ax.set_title(title) 
    
    table_data = []
    table_headers = ["Tipo de Nodo", "Cantidad"]
    
    for key, info in node_type_info.items():
        if node_type_counts[key] > 0:
            table_data.append([info['label'], node_type_counts[key]])

    table = ax.table(cellText=table_data, colLabels=table_headers, loc='upper left', bbox=[1.05, 0.6, 0.25, 0.3])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.2)

    plt.tight_layout(rect=[0, 0, 0.8, 1])
    plt.show()

def plot_evacuation_route(original_graph, post_sismo_graph, node_positions,
                            origin_node_id, best_target_sin_sismo, path_sin_sismo,
                            best_target_con_sismo, path_con_sismo):
    plt.figure(figsize=(16, 14))

    all_x = [pos[0] for pos in node_positions.values()]
    all_y = [pos[1] for pos in node_positions.values()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    x_range = max_x - min_x
    y_range = max_y - min_y
    padding_x = x_range * 0.05
    padding_y = y_range * 0.05

    ax1 = plt.subplot(121)
    ax1.set_title("Ruta de Evacuación (Sin Sismo)")
    draw_graph_with_path(original_graph, node_positions, origin_node_id, best_target_sin_sismo, path_sin_sismo, ax1, is_post_sismo=False)
    ax1.set_xlim(min_x - padding_x, max_x + padding_x)
    ax1.set_ylim(min_y - padding_y, max_y + padding_y)


    ax2 = plt.subplot(122)
    ax2.set_title("Ruta de Evacuación (Con Sismo)")
    draw_graph_with_path(post_sismo_graph, node_positions, origin_node_id, best_target_con_sismo, path_con_sismo, ax2, is_post_sismo=True)
    ax2.set_xlim(min_x - padding_x, max_x + padding_x)
    ax2.set_ylim(min_y - padding_y, max_y + padding_y)


    plt.tight_layout()
    plt.show()

def draw_graph_with_path(graph, node_positions, origin_node_id, target_node_id, path, ax, is_post_sismo=False):
    nodes_to_draw = set(path)
    edges_to_draw = []
    path_edges = set()

    if path:
        nodes_to_draw.update(path)
        for node in path:
            nodes_to_draw.update(graph.neighbors(node))
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            path_edges.add(tuple(sorted((u, v))))
            if graph.has_edge(u, v):
                edges_to_draw.append((u, v, graph[u][v]))
            elif graph.has_edge(v, u):
                edges_to_draw.append((v, u, graph[v][u]))

    nodes_to_draw.add(origin_node_id)
    if target_node_id:
        nodes_to_draw.add(target_node_id)
        nodes_to_draw.update(graph.neighbors(target_node_id))

    for u, v, data in graph.edges(data=True):
        if (u in nodes_to_draw and v in nodes_to_draw) and (tuple(sorted((u, v))) not in path_edges):
            edges_to_draw.append((u, v, data))

    subgraph_nodes = [n for n in nodes_to_draw if n in graph]
    subgraph = graph.subgraph(subgraph_nodes)

    node_colors = []
    node_sizes = []
    node_labels = {}
    for node in subgraph.nodes():
        if node == origin_node_id:
            node_colors.append('magenta')
            node_sizes.append(300)
            node_labels[node] = 'ORIGEN'
        elif node == target_node_id:
            node_colors.append('lime')
            node_sizes.append(300)
            node_labels[node] = 'DESTINO'
        elif graph.nodes[node].get('type') == 'critical_infra':
            node_colors.append('red')
            node_sizes.append(150)
        elif graph.nodes[node].get('type') == 'populated_zone':
            node_colors.append('yellow')
            node_sizes.append(50)
        else:
            node_colors.append('gray')
            node_sizes.append(20)
    
    subgraph_pos = {n: node_positions[n] for n in subgraph.nodes()}
    nx.draw_networkx_nodes(subgraph, subgraph_pos, ax=ax, node_color=node_colors, node_size=node_sizes, alpha=0.8)
    nx.draw_networkx_labels(subgraph, subgraph_pos, labels=node_labels, font_size=8, font_color='black', ax=ax)


    edge_colors_list = []
    edge_widths_list = []
    edge_labels = {}
    
    for u, v, data in subgraph.edges(data=True):
        current_edge_tuple = tuple(sorted((u,v)))
        weight = data.get('weight', 1.0)

        if is_post_sismo and data.get('blocked', False):
            edge_colors_list.append('black')
            edge_widths_list.append(2.5)
            edge_labels[(u, v)] = f"{weight:.1f}m (Bloqueado)"
        elif current_edge_tuple in path_edges:
            edge_colors_list.append('cyan')
            edge_widths_list.append(3.5)
            edge_labels[(u, v)] = f"{weight:.1f}m" 
        else:
            edge_colors_list.append('lightgray')
            edge_widths_list.append(0.5)
            edge_labels[(u, v)] = f"{weight:.1f}m"

    nx.draw_networkx_edges(subgraph, subgraph_pos, edgelist=subgraph.edges(), edge_color=edge_colors_list, width=edge_widths_list, alpha=0.7, ax=ax)
    
    path_and_blocked_edge_labels = {
        (u,v): label for (u,v), label in edge_labels.items()
        if (tuple(sorted((u,v))) in path_edges) or (is_post_sismo and subgraph[u][v].get('blocked', False))
    }
    
    nx.draw_networkx_edge_labels(subgraph, subgraph_pos, edge_labels=path_and_blocked_edge_labels, ax=ax, font_color='darkblue', font_size=7)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Origen', markerfacecolor='magenta', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Destino', markerfacecolor='lime', markersize=10),
        Line2D([0], [0], color='cyan', lw=3, label='Ruta Óptima'),
        Line2D([0], [0], color='black', lw=2.5, label='Arista Bloqueada'),
        Line2D([0], [0], color='lightgray', lw=0.5, label='Arista Conectada'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1))

    ax.set_aspect('equal', adjustable='box')

def plot_mst_distribution(original_graph, post_sismo_graph, node_positions,
                            supply_center_id, distribution_points_ids,
                            mst_edges, total_cost):
    plt.figure(figsize=(10, 8))

    all_x = [pos[0] for pos in node_positions.values()]
    all_y = [pos[1] for pos in node_positions.values()]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    x_range = max_x - min_x
    y_range = max_y - min_y
    padding_x = x_range * 0.05
    padding_y = y_range * 0.05

    ax = plt.gca()
    ax.set_title(f"Red de Distribución (MST)\nCosto Total: {total_cost:.2f}m")
    
    draw_mst_subplot(original_graph, post_sismo_graph, node_positions,
                     supply_center_id, distribution_points_ids, mst_edges, ax)
    
    ax.set_xlim(min_x - padding_x, max_x + padding_x)
    ax.set_ylim(min_y - padding_y, max_y + padding_y)

    plt.tight_layout()
    plt.show()

def draw_mst_subplot(original_graph, graph_post_sismo, node_positions,
                     supply_center_id, distribution_points_ids, mst_edges, ax):
    
    nodes_in_mst_visualization = set([supply_center_id])
    nodes_in_mst_visualization.update(distribution_points_ids)
    
    all_graph_edges = list(graph_post_sismo.edges(data=True))
    edge_colors_bg = []
    edge_widths_bg = []
    for u, v, data in all_graph_edges:
        if data.get('blocked', False):
            edge_colors_bg.append('black')
            edge_widths_bg.append(1.5)
        else:
            edge_colors_bg.append('lightgray')
            edge_widths_bg.append(0.3)
    nx.draw_networkx_edges(graph_post_sismo, node_positions, edgelist=all_graph_edges, edge_color=edge_colors_bg, width=edge_widths_bg, alpha=0.4, ax=ax)


    node_colors = []
    node_sizes = []
    node_labels = {}
    
    nodes_to_draw_actual = list(graph_post_sismo.nodes())
    
    for node in nodes_to_draw_actual:
        data = graph_post_sismo.nodes[node]
        if node == supply_center_id:
            node_colors.append('red')
            node_sizes.append(400)
            node_labels[node] = 'S'
        elif node in distribution_points_ids:
            node_colors.append('lime')
            node_sizes.append(250)
            node_labels[node] = 'D'
        elif data.get('type') == 'vial':
            node_colors.append('skyblue')
            node_sizes.append(80)
        else:
            node_colors.append('gray')
            node_sizes.append(50)
            
    pos_filtered = {n: node_positions[n] for n in nodes_to_draw_actual if node_positions.get(n)}

    nx.draw_networkx_nodes(graph_post_sismo, pos_filtered, nodelist=nodes_to_draw_actual, 
                           node_color=node_colors, node_size=node_sizes, alpha=0.9, ax=ax)
    
    labels_filtered = {n: label for n, label in node_labels.items() if n in nodes_to_draw_actual and (n == supply_center_id or n in distribution_points_ids)}
    nx.draw_networkx_labels(graph_post_sismo, pos_filtered, labels=labels_filtered, font_size=10, font_color='black', ax=ax)


    mst_drawn_edges = []
    mst_edge_labels = {}

    for u, v, data in mst_edges:
        mst_drawn_edges.append((u, v))
        
        if u in node_positions and v in node_positions:
            x_mid = (node_positions[u][0] + node_positions[v][0]) / 2
            y_mid = (node_positions[u][1] + node_positions[v][1]) / 2
            
            mst_edge_labels[(u, v)] = (f"{data['weight']:.1f}m", (x_mid, y_mid))


    nx.draw_networkx_edges(graph_post_sismo, node_positions, edgelist=mst_drawn_edges, edge_color='blue', width=3, ax=ax, alpha=0.8)
    
    for (u, v), (label_text, (x_pos, y_pos)) in mst_edge_labels.items():
        ax.text(x_pos, y_pos, label_text, color='darkblue', fontsize=8, ha='center', va='center',
                bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.2', alpha=0.7))


    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Centro Abastecimiento (S)', markerfacecolor='red', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Punto Distribución (D)', markerfacecolor='lime', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Nodo Vial', markerfacecolor='skyblue', markersize=8),
        Line2D([0], [0], color='blue', lw=3, label='Conexión MST (Directa)'),
        Line2D([0], [0], color='black', lw=1.5, label='Arista Bloqueada (fondo)'),
        Line2D([0], [0], color='lightgray', lw=0.3, label='Otras Aristas (fondo)'),
        Line2D([0], [0], color='w', label='Etiqueta: Costo de Tramo (m)', marker='s', markerfacecolor='white', markeredgecolor='darkblue', markersize=7),
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1))
    ax.set_aspect('equal', adjustable='box')


def plot_connectivity_analysis(graph_post_sismo, node_positions, largest_component_nodes, isolated_nodes):
    plt.figure(figsize=(12, 10))
    
    node_colors = []
    node_sizes = []
    for node in graph_post_sismo.nodes():
        if node in largest_component_nodes:
            node_colors.append('green')
            node_sizes.append(100)
        elif node in isolated_nodes:
            node_colors.append('red')
            node_sizes.append(100)
        else:
            node_colors.append('orange')
            node_sizes.append(50)

    nx.draw_networkx_nodes(graph_post_sismo, node_positions, node_color=node_colors, node_size=node_sizes, alpha=0.8)

    edge_colors = []
    edge_widths = []
    for u, v, data in graph_post_sismo.edges(data=True):
        if data.get('blocked', False):
            edge_colors.append('black')
            edge_widths.append(2.0)
        else:
            edge_colors.append('gray')
            edge_widths.append(0.5)
    nx.draw_networkx_edges(graph_post_sismo, node_positions, edge_color=edge_colors, width=edge_widths, alpha=0.5)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Componente Principal', markerfacecolor='green', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Nodos Aislados', markerfacecolor='red', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Otras Componentes', markerfacecolor='orange', markersize=8),
        Line2D([0], [0], color='black', lw=2, label='Arista Bloqueada'),
        Line2D([0], [0], color='gray', lw=2, label='Arista Desbloqueada'),
    ]
    plt.legend(handles=legend_elements, loc='lower left', bbox_to_anchor=(1, 0))

    plt.title("Análisis de Conectividad Post-Sismo")
    plt.tight_layout(rect=[0, 0, 0.8, 1])
    plt.show()