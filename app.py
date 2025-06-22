import streamlit as st
import networkx as nx
import math
import folium
import re

# Carregar dados do grafo a partir do arquivo HTML do Folium
HTML_FILE = "grafo_aereo_folium.html"
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Extrair aeroportos (nós) e coordenadas
nodes = {}
pattern_node = re.compile(r'>([A-Z]{3}) - (-?\d+\.\d+), (-?\d+\.\d+)<')
for match in pattern_node.finditer(html_content):
    code = match.group(1)
    lat = float(match.group(2))
    lon = float(match.group(3))
    nodes[code] = (lat, lon)

# Extrair rotas (arestas) e distâncias
edges = []
seen_pairs = set()
pattern_edge = re.compile(r'<div>\s*([A-Z]{3}) <=> ([A-Z]{3}): (\d+) km\s*</div>')
for match in pattern_edge.finditer(html_content):
    a, b = match.group(1), match.group(2)
    dist = float(match.group(3))
    pair = tuple(sorted([a, b]))
    if pair not in seen_pairs:
        seen_pairs.add(pair)
        edges.append((a, b, dist))

# Construir grafo
G = nx.Graph()
for (a, b, dist) in edges:
    G.add_edge(a, b, weight=dist)

def haversine_distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(d_lambda/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return 6371.0 * c

def heuristic(n1, n2):
    return haversine_distance(nodes[n1], nodes[n2])

# Interface
st.title("Caminho Mais Curto entre Aeroportos (Algoritmo A*)")
st.markdown("Selecione a origem e o destino:")

origem = st.selectbox("Aeroporto de Origem", list(nodes.keys()))
destino = st.selectbox("Aeroporto de Destino", list(nodes.keys()))

if origem and destino and origem != destino:
    try:
        caminho = nx.astar_path(G, origem, destino, heuristic=heuristic, weight='weight')
        distancia_total = nx.astar_path_length(G, origem, destino, heuristic=heuristic, weight='weight')
        st.success(f"Caminho: {' ➝ '.join(caminho)}")
        st.info(f"Distância total: {distancia_total:.1f} km")
    except nx.NetworkXNoPath:
        caminho = None
        st.error("Não foi encontrado um caminho entre os aeroportos selecionados.")
else:
    caminho = None
    if origem == destino:
        st.warning("Origem e destino devem ser diferentes.")

# Criar o mapa
m = folium.Map(location=[-28.5, -52.5], zoom_start=6)

for code, (lat, lon) in nodes.items():
    folium.Marker([lat, lon], popup=f"{code} - {lat:.3f}, {lon:.3f}",
                  icon=folium.Icon(color='blue', icon='plane', prefix='fa')).add_to(m)

for a, b, dist in edges:
    folium.PolyLine([nodes[a], nodes[b]], color='red', weight=3, opacity=0.6).add_child(
        folium.Tooltip(f"{a} ↔ {b}: {dist:.0f} km")
    ).add_to(m)

if caminho:
    for i in range(len(caminho) - 1):
        a = caminho[i]
        b = caminho[i + 1]
        folium.PolyLine([nodes[a], nodes[b]], color='green', weight=6, opacity=0.8).add_to(m)

st.components.v1.html(m._repr_html_(), height=600)

st.markdown("## ℹ️ Como funciona o Algoritmo A*")
st.markdown("""
O algoritmo A* encontra o caminho mais curto entre dois pontos em um grafo. Ele usa:
- **g(n)**: custo do início até o ponto atual
- **h(n)**: estimativa (heurística) do custo restante até o destino

A soma `f(n) = g(n) + h(n)` determina qual nó explorar primeiro. Neste app, usamos a **distância em linha reta** como heurística.
""")

