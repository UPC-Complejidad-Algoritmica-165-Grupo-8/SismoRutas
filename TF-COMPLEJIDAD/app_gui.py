import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import random
import warnings

from src.data_simulator import (
    simulate_vial_network,
    simulate_critical_infrastructure,
    simulate_populated_zones,
    RIESGO_PONDERACION
)
from src.graph_builder import build_urban_graph
from src.earthquake_simulator import SimuladorSismo
from src.graph_algorithms import find_shortest_path_dijkstra, calculate_mst_for_distribution, analyze_post_earthquake_connectivity
from src.visualize_graph import plot_full_graph, plot_evacuation_route, plot_mst_distribution, plot_connectivity_analysis

warnings.filterwarnings("ignore", category=UserWarning)

class EarthquakeApp:
    def __init__(self, master):
        self.master = master
        master.title("Simulador de Sismos y Planificador de Rutas")
        master.geometry("800x600")

        self.graph = None
        self.graph_post_sismo = None
        self.node_positions = {}
        self.origen_usuario_id = None
        self.supply_center_id = None

        self._create_widgets()
        self._initialize_simulation_data()

    def _create_widgets(self):
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        self.sim_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sim_frame, text="Simulación y Grafo")
        self._setup_sim_frame()

        self.evac_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.evac_frame, text="Evacuación (Dijkstra)")
        self._setup_evac_frame()

        self.dist_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dist_frame, text="Distribución de Ayuda (MST)")
        self._setup_dist_frame()

        self.connectivity_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connectivity_frame, text="Análisis de Conectividad")
        self._setup_connectivity_frame()

    def _setup_sim_frame(self):
        ttk.Label(self.sim_frame, text="Parámetros de Simulación:").pack(pady=5)

        ttk.Label(self.sim_frame, text="Magnitud Sismo (solo visual):").pack()
        self.sismo_mag_var = tk.DoubleVar(value=7.5)
        ttk.Entry(self.sim_frame, textvariable=self.sismo_mag_var).pack(pady=2)

        ttk.Label(self.sim_frame, text="Prob. Bloqueo Alto Riesgo (0-1):").pack()
        self.prob_alto_var = tk.DoubleVar(value=0.5)
        ttk.Entry(self.sim_frame, textvariable=self.prob_alto_var).pack(pady=2)

        ttk.Label(self.sim_frame, text="Prob. Bloqueo Medio Riesgo (0-1):").pack()
        self.prob_medio_var = tk.DoubleVar(value=0.1)
        ttk.Entry(self.sim_frame, textvariable=self.prob_medio_var).pack(pady=2)

        ttk.Button(self.sim_frame, text="1. Construir y Visualizar Grafo", command=self._build_and_plot_graph).pack(pady=10)
        ttk.Button(self.sim_frame, text="2. Simular Sismo y Bloqueos", command=self._simulate_earthquake).pack(pady=5)

        self.sim_status_label = ttk.Label(self.sim_frame, text="Estado: Inicializando...")
        self.sim_status_label.pack(pady=5)

        self.nodes_count_label = ttk.Label(self.sim_frame, text="Nodos en Grafo: N/A")
        self.nodes_count_label.pack(pady=2)
        self.edges_count_label = ttk.Label(self.sim_frame, text="Aristas en Grafo: N/A")
        self.edges_count_label.pack(pady=2)

    def _setup_evac_frame(self):
        ttk.Label(self.evac_frame, text="Planificación de Evacuación").pack(pady=10)

        origin_frame = ttk.Frame(self.evac_frame)
        origin_frame.pack(pady=5)
        ttk.Label(origin_frame, text="ID de la Manzana Origen (ej. M_123):").pack(side=tk.LEFT, padx=5)
        self.origin_manzana_entry = ttk.Entry(origin_frame, width=15)
        self.origin_manzana_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(origin_frame, text="Usar Manzana Aleatoria", command=self._set_random_origin).pack(side=tk.LEFT, padx=5)
        self.current_origin_label = ttk.Label(self.evac_frame, text="Origen Actual: Ninguno")
        self.current_origin_label.pack(pady=2)

        ttk.Label(self.evac_frame, text="Tipo de Destino:").pack(pady=5)
        self.destination_type_var = tk.StringVar()
        self.destination_type_combobox = ttk.Combobox(self.evac_frame, textvariable=self.destination_type_var,
                                                     values=["Refugio", "Hospital", "Estacion de Rescate", "Centro de Salud"])
        self.destination_type_combobox.set("Refugio")
        self.destination_type_combobox.pack(pady=2)

        ttk.Button(self.evac_frame, text="Calcular Ruta Óptima", command=self._calculate_evacuation_route).pack(pady=10)
        self.evac_status_label = ttk.Label(self.evac_frame, text="Estado: Ingresa origen y tipo de destino.")
        self.evac_status_label.pack(pady=5)

    def _setup_dist_frame(self):
        ttk.Label(self.dist_frame, text="Planificación de Distribución de Ayuda").pack(pady=10)

        ttk.Label(self.dist_frame, text="Centro de Abastecimiento:").pack()
        ttk.Button(self.dist_frame, text="Seleccionar Centro (ej. Hospital)", command=self._select_supply_center).pack(pady=5)
        self.supply_center_label = ttk.Label(self.dist_frame, text="Centro Seleccionado: N/A")
        self.supply_center_label.pack(pady=2)

        ttk.Label(self.dist_frame, text="Número de Refugios a Conectar:").pack()
        self.num_refugios_var = tk.IntVar(value=5)
        ttk.Entry(self.dist_frame, textvariable=self.num_refugios_var).pack(pady=2)

        ttk.Label(self.dist_frame, text="Algoritmo MST:").pack(pady=5)
        self.mst_algo_var = tk.StringVar(value="Kruskal")
        self.mst_algo_combobox = ttk.Combobox(self.dist_frame, textvariable=self.mst_algo_var,
                                               values=["Kruskal", "Prim"])
        self.mst_algo_combobox.pack(pady=2)

        ttk.Button(self.dist_frame, text="Calcular Red de Distribución (MST)", command=self._calculate_mst).pack(pady=10)
        self.dist_status_label = ttk.Label(self.dist_frame, text="Estado: Esperando centro y cálculo...")
        self.dist_status_label.pack(pady=5)

    def _setup_connectivity_frame(self):
        ttk.Label(self.connectivity_frame, text="Análisis de Conectividad Post-Sismo").pack(pady=10)

        ttk.Button(self.connectivity_frame, text="Analizar Conectividad", command=self._analyze_connectivity).pack(pady=10)

        self.connectivity_status_label = ttk.Label(self.connectivity_frame, text="Estado: Esperando análisis...")
        self.connectivity_status_label.pack(pady=5)

        self.largest_component_label = ttk.Label(self.connectivity_frame, text="Nodos en Componente Principal: N/A")
        self.largest_component_label.pack(pady=2)

        self.isolated_nodes_label = ttk.Label(self.connectivity_frame, text="Nodos Aislados: N/A")
        self.isolated_nodes_label.pack(pady=2)


    def _initialize_simulation_data(self):
        self.base_lat, self.base_lon = -12.0463, -77.0428
        self.num_grid_x = 40
        self.num_grid_y = 40
        self.spacing = 0.002

        self.num_infra_critica = 100
        self.num_zonas_pobladas = 500

        self.df_red_vial_edges = None
        self.gdf_vial_nodes = None
        self.gdf_infra_critica = None
        self.gdf_zonas_pobladas = None

        self.sim_status_label.config(text="Estado: Datos inicializados. Construye el grafo.")

    def _build_and_plot_graph(self):
        self.sim_status_label.config(text="Estado: Simulando datasets...")
        self.nodes_count_label.config(text="Nodos en Grafo: Calculando...")
        self.edges_count_label.config(text="Aristas en Grafo: Calculando...")
        self.master.update_idletasks()

        try:
            self.df_red_vial_edges, self.gdf_vial_nodes = simulate_vial_network(
                self.base_lat, self.base_lon, self.num_grid_x, self.num_grid_y, self.spacing
            )
            self.gdf_infra_critica = simulate_critical_infrastructure(
                self.base_lat, self.base_lon, self.num_grid_x / 2 * self.spacing, self.num_infra_critica
            )
            self.gdf_zonas_pobladas = simulate_populated_zones(
                self.base_lat, self.base_lon, self.num_grid_x / 2 * self.spacing, self.num_zonas_pobladas
            )

            self.sim_status_label.config(text="Estado: Construyendo grafo...")
            self.master.update_idletasks()

            self.graph = build_urban_graph(
                self.df_red_vial_edges, self.gdf_vial_nodes, self.gdf_infra_critica, self.gdf_zonas_pobladas, RIESGO_PONDERACION
            )
            self.graph_post_sismo = self.graph.copy()

            self.node_positions = {n: self.graph.nodes[n]['pos'] for n in self.graph.nodes() if 'pos' in self.graph.nodes[n]}

            self.nodes_count_label.config(text=f"Nodos en Grafo: {self.graph.number_of_nodes()}")
            self.edges_count_label.config(text=f"Aristas en Grafo: {self.graph.number_of_edges()}")

            self.sim_status_label.config(text="Estado: Grafo construido. Visualizando...")
            self.master.update_idletasks()

            plot_full_graph(self.graph)
            self.sim_status_label.config(text="Estado: Grafo construido y visualizado.")

        except Exception as e:
            messagebox.showerror("Error de Simulación", f"Ocurrió un error al construir el grafo: {e}")
            self.sim_status_label.config(text="Estado: Error al construir grafo.")
            self.nodes_count_label.config(text="Nodos en Grafo: N/A")
            self.edges_count_label.config(text="Aristas en Grafo: N/A")


    def _simulate_earthquake(self):
        if self.graph is None:
            messagebox.showwarning("Advertencia", "Primero construye el grafo.")
            return

        try:
            magnitud = self.sismo_mag_var.get()
            prob_alto = self.prob_alto_var.get()
            prob_medio = self.prob_medio_var.get()

            self.sim_status_label.config(text=f"Estado: Simulando sismo M{magnitud}...")
            self.master.update_idletasks()

            simulador = SimuladorSismo(self.graph)
            self.graph_post_sismo, bloqueos_aplicados = simulador.simular_bloqueos(
                magnitud_sismo=magnitud,
                porcentaje_bloqueo_alto_riesgo=prob_alto,
                porcentaje_bloqueo_medio_riesgo=prob_medio
            )
            messagebox.showinfo("Sismo Simulado", f"Sismo de magnitud {magnitud} simulado. Total de aristas bloqueadas: {len(bloqueos_aplicados)}")
            self.sim_status_label.config(text=f"Estado: Sismo M{magnitud} simulado. {len(bloqueos_aplicados)} aristas bloqueadas.")

        except Exception as e:
            messagebox.showerror("Error de Sismo", f"Ocurrió un error al simular el sismo: {e}")
            self.sim_status_label.config(text="Estado: Error al simular sismo.")

    def _set_random_origin(self):
        if self.gdf_zonas_pobladas is None:
            messagebox.showwarning("Advertencia", "Primero construye el grafo para simular ubicaciones.")
            return

        self.origen_usuario_id = self.gdf_zonas_pobladas.sample(1)['manzana_id'].iloc[0]
        self.origin_manzana_entry.delete(0, tk.END)
        self.origin_manzana_entry.insert(0, self.origen_usuario_id)
        self.current_origin_label.config(text=f"Origen Actual: {self.origen_usuario_id}")


    def _calculate_evacuation_route(self):
        if self.graph_post_sismo is None:
            messagebox.showwarning("Advertencia", "Primero construye el grafo y simula un sismo.")
            return

        self.origen_usuario_id = self.origin_manzana_entry.get().strip()
        if not self.origen_usuario_id:
            messagebox.showwarning("Advertencia", "Por favor, ingresa un ID de manzana de origen o usa el botón 'Usar Manzana Aleatoria'.")
            return

        if self.origen_usuario_id not in self.graph_post_sismo.nodes():
            messagebox.showwarning("Advertencia", f"El ID de manzana '{self.origen_usuario_id}' no existe en el grafo. Verifica el formato (ej. M_123).")
            return

        self.current_origin_label.config(text=f"Origen Actual: {self.origen_usuario_id}")

        tipo_destino_str = self.destination_type_var.get()
        tipo_destino_map = {
            "Refugio": "refugio",
            "Hospital": "hospital",
            "Estacion de Rescate": "estacion_rescate",
            "Centro de Salud": "centro_salud"
        }
        target_node_types_in_graph = [tipo_destino_map.get(tipo_destino_str, "refugio")]

        destinos_ids = [n for n, data in self.graph.nodes(data=True) if data.get('type') == 'critical_infra' and data.get('tipo') in target_node_types_in_graph]

        if not destinos_ids:
            messagebox.showwarning("Advertencia", f"No hay destinos de tipo '{tipo_destino_str}' disponibles en el grafo simulado.")
            self.evac_status_label.config(text=f"Estado: No hay destinos de tipo '{tipo_destino_str}'.")
            return

        try:
            self.evac_status_label.config(text="Estado: Calculando rutas de evacuación...")
            self.master.update_idletasks()

            path_sin_sismo, best_target_sin_sismo, length_sin_sismo = find_shortest_path_dijkstra(
                self.graph, self.origen_usuario_id, destinos_ids
            )

            path_con_sismo, best_target_con_sismo, length_con_sismo = find_shortest_path_dijkstra(
                self.graph_post_sismo, self.origen_usuario_id, destinos_ids
            )

            plot_evacuation_route(
                self.graph,
                self.graph_post_sismo,
                self.node_positions,
                self.origen_usuario_id,
                best_target_sin_sismo, path_sin_sismo,
                best_target_con_sismo, path_con_sismo
            )

            status_msg = "Ruta de evacuación calculada y visualizada.\n"
            if path_sin_sismo:
                status_msg += f"Sin sismo: a {best_target_sin_sismo} ({length_sin_sismo:.2f}m).\n"
            else:
                status_msg += "Sin sismo: No se encontró ruta.\n"

            if path_con_sismo:
                status_msg += f"Con sismo: a {best_target_con_sismo} ({length_con_sismo:.2f}m)."
            else:
                status_msg += "Con sismo: No se encontró ruta (posiblemente bloqueada)."

            self.evac_status_label.config(text=f"Estado: {status_msg}")
            messagebox.showinfo("Ruta Calculada", status_msg)

        except Exception as e:
            messagebox.showerror("Error de Evacuación", f"Ocurrió un error al calcular la ruta: {e}")
            self.evac_status_label.config(text="Estado: Error al calcular ruta.")


    def _select_supply_center(self):
        if self.graph is None:
            messagebox.showwarning("Advertencia", "Primero construye el grafo.")
            return

        supply_centers = [n for n, data in self.graph.nodes(data=True) if data.get('type') == 'critical_infra' and data.get('tipo') in ['hospital', 'estacion_rescate']]
        if not supply_centers:
            messagebox.showwarning("Advertencia", "No hay hospitales o estaciones de rescate en el grafo simulado.")
            self.supply_center_label.config(text="Centro Seleccionado: N/A")
            return

        self.supply_center_id = random.choice(supply_centers)
        self.supply_center_label.config(text=f"Centro Seleccionado: {self.supply_center_id}")
        messagebox.showinfo("Centro Seleccionado", f"Centro de abastecimiento simulado: {self.supply_center_id}")
        self.dist_status_label.config(text=f"Centro seleccionado: {self.supply_center_id}. Listo para calcular MST.")


    def _calculate_mst(self):
        if self.graph_post_sismo is None or self.supply_center_id is None:
            messagebox.showwarning("Advertencia", "Primero construye el grafo, simula un sismo y selecciona un centro de abastecimiento.")
            return

        try:
            self.dist_status_label.config(text="Estado: Calculando MST para distribución...")
            self.master.update_idletasks()

            refugios_ids = [n for n, data in self.graph.nodes(data=True) if data.get('type') == 'critical_infra' and data.get('tipo') == 'refugio']
            if not refugios_ids:
                messagebox.showwarning("Advertencia", "No hay refugios disponibles en el grafo simulado para distribuir.")
                self.dist_status_label.config(text="Estado: No hay refugios.")
                return

            num_refugios = self.num_refugios_var.get()
            selected_distribution_points = random.sample(refugios_ids, min(num_refugios, len(refugios_ids)))

            mst_option = self.mst_algo_var.get()
            
            mst_edges = []
            total_cost = 0.0
            
            if mst_option == "Prim":
                mst_edges, total_cost = calculate_mst_for_distribution(
                    self.graph_post_sismo, self.supply_center_id, selected_distribution_points, mst_algorithm='prim'
                )
            elif mst_option == "Kruskal":
                mst_edges, total_cost = calculate_mst_for_distribution(
                    self.graph_post_sismo, self.supply_center_id, selected_distribution_points, mst_algorithm='kruskal_custom'
                )
            else:
                messagebox.showerror("Error de Selección", "Algoritmo MST no reconocido. Por favor, selecciona 'Kruskal' o 'Prim'.")
                self.dist_status_label.config(text="Estado: Error de selección de algoritmo.")
                return
            
            # Plot based on the option
            plot_mst_distribution(
                self.graph, self.graph_post_sismo, self.node_positions,
                self.supply_center_id, selected_distribution_points,
                mst_edges, total_cost
            )
            
            if not mst_edges and len(selected_distribution_points) > 1: 
                status_msg = f"No se pudo calcular el MST con {mst_option} para todos los puntos (posibles desconexiones)."
            else:
                status_msg = f"MST de {mst_option} calculado y visualizado.\nCosto total: {total_cost:.2f} metros."

            self.dist_status_label.config(text=f"Estado: {status_msg}")
            messagebox.showinfo("MST Calculado", status_msg)

        except Exception as e:
            messagebox.showerror("Error de Distribución", f"Ocurrió un error al calcular el MST: {e}")
            self.dist_status_label.config(text="Estado: Error al calcular MST.")

    def _analyze_connectivity(self):
        if self.graph_post_sismo is None:
            messagebox.showwarning("Advertencia", "Primero construye el grafo y simula un sismo para analizar la conectividad.")
            return

        try:
            self.connectivity_status_label.config(text="Estado: Analizando conectividad...")
            self.master.update_idletasks()

            largest_component_nodes, isolated_nodes = analyze_post_earthquake_connectivity(self.graph_post_sismo)

            num_largest_component = len(largest_component_nodes)
            num_isolated_nodes = len(isolated_nodes)

            self.largest_component_label.config(text=f"Nodos en Componente Principal: {num_largest_component}")
            self.isolated_nodes_label.config(text=f"Nodos Aislados o Desconectados: {num_isolated_nodes}")

            example_isolated_node = next(iter(isolated_nodes), "N/A")
            if example_isolated_node != "N/A":
                messagebox.showinfo(
                    "Análisis de Conectividad",
                    f"Análisis completado:\n"
                    f"El componente conectado más grande contiene {num_largest_component} nodos.\n"
                    f"Se han identificado {num_isolated_nodes} nodos aislados o en componentes pequeños. (Ejemplo: {example_isolated_node})"
                )
            else:
                messagebox.showinfo(
                    "Análisis de Conectividad",
                    f"Análisis completado:\n"
                    f"El componente conectado más grande contiene {num_largest_component} nodos.\n"
                    f"No se identificaron nodos aislados significativos. La red está bien conectada."
                )

            plot_connectivity_analysis(self.graph_post_sismo, self.node_positions, largest_component_nodes, isolated_nodes)

            self.connectivity_status_label.config(text="Estado: Conectividad analizada y visualizada.")

        except Exception as e:
            messagebox.showerror("Error de Conectividad", f"Ocurrió un error al analizar la conectividad: {e}")
            self.connectivity_status_label.config(text="Estado: Error al analizar conectividad.")


if __name__ == "__main__":
    root = tk.Tk()
    app = EarthquakeApp(root)
    root.mainloop()