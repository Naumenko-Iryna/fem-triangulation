import streamlit as st
import math
import matplotlib.pyplot as plt

def dist(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def triangle_min_angle(p1, p2, p3):
    a, b, c = dist(p2, p3), dist(p1, p3), dist(p1, p2)
    def angle(adj1, adj2, opp):
        if adj1 * adj2 == 0: return 0
        val = max(-1.0, min(1.0, (adj1**2 + adj2**2 - opp**2) / (2 * adj1 * adj2)))
        return math.acos(val)
    return min(angle(b, c, a), angle(a, c, b), angle(a, b, c))

def generate_mesh(nx, ny, verts, edge_types):
    nodes, node_boundaries, elements = [], [], []
    for j in range(ny + 1):
        v = j / ny
        for i in range(nx + 1):
            u = i / nx
            x = (1-u)*(1-v)*verts[0][0] + u*(1-v)*verts[1][0] + u*v*verts[2][0] + (1-u)*v*verts[3][0]
            y = (1-u)*(1-v)*verts[0][1] + u*(1-v)*verts[1][1] + u*v*verts[2][1] + (1-u)*v*verts[3][1]
            nodes.append((x, y))
            
            b_mark = 0 
            if v == 0: b_mark = edge_types[0]
            elif u == 1: b_mark = edge_types[1]
            elif v == 1: b_mark = edge_types[2]
            elif u == 0: b_mark = edge_types[3]
            node_boundaries.append(b_mark)

    for j in range(ny):
        for i in range(nx):
            bl, br = j * (nx + 1) + i, j * (nx + 1) + i + 1
            tl, tr = (j + 1) * (nx + 1) + i, (j + 1) * (nx + 1) + i + 1
            
            a1 = min(triangle_min_angle(nodes[bl], nodes[br], nodes[tr]), triangle_min_angle(nodes[bl], nodes[tr], nodes[tl]))
            a2 = min(triangle_min_angle(nodes[bl], nodes[br], nodes[tl]), triangle_min_angle(nodes[br], nodes[tr], nodes[tl]))
            
            if a1 >= a2: elements.extend([(bl, br, tr), (bl, tr, tl)])
            else: elements.extend([(bl, br, tl), (br, tr, tl)])
                
    return nodes, elements, node_boundaries

st.set_page_config(page_title="Триангуляція Делоне", layout="wide")
st.title("Генератор сіток Делоне (Вар. 12)")

st.sidebar.header("Параметри розбиття")
nx = st.sidebar.number_input("Густина Nx", min_value=1, max_value=20, value=2)
ny = st.sidebar.number_input("Густина Ny", min_value=1, max_value=20, value=2)

st.sidebar.header("Вершини області (X, Y)")
v1_x = st.sidebar.number_input("Ліва нижня X", value=1.0)
v1_y = st.sidebar.number_input("Ліва нижня Y", value=0.0)
v2_x = st.sidebar.number_input("Права нижня X", value=2.0)
v2_y = st.sidebar.number_input("Права нижня Y", value=0.0)
v3_x = st.sidebar.number_input("Права верхня X", value=0.0)
v3_y = st.sidebar.number_input("Права верхня Y", value=2.0)
v4_x = st.sidebar.number_input("Ліва верхня X", value=0.0)
v4_y = st.sidebar.number_input("Ліва верхня Y", value=1.0)

verts = [(v1_x, v1_y), (v2_x, v2_y), (v3_x, v3_y), (v4_x, v4_y)]
b_types = [2, 1, 2, 3] # Типи границь для 12 варіанту

col1, col2 = st.columns([2, 1])

with col1:
    nodes, elements, boundaries = generate_mesh(nx, ny, verts, b_types)
    
    fig, ax = plt.subplots(figsize=(6, 6))
    for idx, element in enumerate(elements):
        pts = [nodes[n] for n in element] + [nodes[element[0]]]
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color='black', alpha=0.5)
        cx, cy = sum(nodes[n][0] for n in element)/3, sum(nodes[n][1] for n in element)/3
        ax.text(cx, cy, str(idx), color='blue', fontsize=8, ha='center', va='center')

    colors = {0: 'gray', 1: 'red', 2: 'green', 3: 'purple'}
    for idx, (node, b_mark) in enumerate(zip(nodes, boundaries)):
        ax.plot(node[0], node[1], color=colors.get(b_mark, 'black'), marker='o', markersize=6)
        ax.text(node[0]+0.02, node[1]+0.02, str(idx), fontsize=8)

    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.7)
    st.pyplot(fig)

with col2:
    st.write(f"**Вузлів:** {len(nodes)} | **Елементів:** {len(elements)}")
    st.text_area("Вузли (ID: X, Y | Тип границі)", "\n".join([f"N{i}: ({n[0]:.2f}, {n[1]:.2f}) | {b}" for i, (n, b) in enumerate(zip(nodes, boundaries))]), height=200)
    st.text_area("Масив зв'язності (ID: вершини)", "\n".join([f"E{i}: {e}" for i, e in enumerate(elements)]), height=200)
