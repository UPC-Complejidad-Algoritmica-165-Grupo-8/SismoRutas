# src/earthquake_simulator.py

import networkx as nx
import random

class SimuladorSismo:
    def __init__(self, graph):
        self.original_graph = graph.copy()
        self.current_graph = graph.copy()

    def simular_bloqueos(self, magnitud_sismo=7.0, porcentaje_bloqueo_alto_riesgo=0.5, porcentaje_bloqueo_medio_riesgo=0.1):
        self.current_graph = self.original_graph.copy() # Resetear a grafo original
        bloqueos_aplicados = []

        for u, v, data in list(self.current_graph.edges(data=True)): # Iterar sobre una copia
            if data.get('type') == 'road':
                riesgo_sismico = data.get('riesgo_sismico', 'bajo')
                should_block = False

                if riesgo_sismico == 'alto':
                    if random.random() < porcentaje_bloqueo_alto_riesgo:
                        should_block = True
                elif riesgo_sismico == 'medio':
                    if random.random() < porcentaje_bloqueo_medio_riesgo:
                        should_block = True

                if should_block:
                    original_weight = data['weight']
                    self.current_graph[u][v]['weight'] = float('inf')
                    self.current_graph[u][v]['blocked'] = True
                    bloqueos_aplicados.append((u, v, original_weight))
                    
                    # Si es bidireccional, bloquear también el sentido contrario
                    if self.current_graph.has_edge(v, u) and self.current_graph[v][u].get('type') == 'road':
                         self.current_graph[v][u]['weight'] = float('inf')
                         self.current_graph[v][u]['blocked'] = True


        return self.current_graph, bloqueos_aplicados