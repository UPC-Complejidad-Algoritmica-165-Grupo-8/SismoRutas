# SismoRutas

1. Instala las Dependencias del Proyecto
Con el entorno virtual activo en la terminal de VS Code, instala las librerías necesarias:

Bash

pip install networkx geopandas shapely matplotlib pandas openpyxl
Explicación de las librerías:

networkx: Para la creación, manipulación y análisis de grafos (redes).

geopandas: Extensión de Pandas para trabajar con datos geoespaciales (manejo de puntos, líneas, polígonos con coordenadas geográficas).

shapely: Biblioteca para operaciones de geometría computacional (utilizada por GeoPandas).

matplotlib: Para la creación de gráficos y visualizaciones de los resultados.

pandas: Para el manejo y análisis de datos en formato de tablas (DataFrames).

openpyxl: Para leer y escribir archivos Excel (usado para cargar los datos de entrada).

2. Ejecuta la Aplicación
Ahora que todas las dependencias están instaladas y el entorno está configurado, puedes ejecutar la aplicación.

Desde la terminal de VS Code (con el entorno virtual activo):

Bash

python app_gui.py
Esto abrirá la interfaz gráfica de la aplicación.

Alternativamente, puedes abrir el archivo app_gui.py en el editor de VS Code y hacer clic en el botón Run (Ejecutar) en la esquina superior derecha (parece un triángulo verde), o usar F5 para depurar/ejecutar.
