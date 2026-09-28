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

def parse_point(text, default):
    """Розбирає рядок виду '1.0, 0.0' або '1 0' на пару координат (x, y)."""
    try:
        parts = text.replace(",", " ").split()
        if len(parts) >= 2:
            return float(parts[0]), float(parts[1])
    except ValueError:
        pass
    return default

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
st.sidebar.caption("Формат вводу: `X, Y` або `X Y`")

# Зручні поля по 2 координати одразу
raw_v1 = st.sidebar.text_input("V1 (ліва нижня):", value="1.0, 0.0")
raw_v2 = st.sidebar.text_input("V2 (права нижня):", value="2.0, 0.0")
raw_v3 = st.sidebar.text_input("V3 (права верхня):", value="0.0, 2.0")
raw_v4 = st.sidebar.text_input("V4 (ліва верхня):", value="0.0, 1.0")

v1 = parse_point(raw_v1, (1.0, 0.0))
v2 = parse_point(raw_v2, (2.0, 0.0))
v3 = parse_point(raw_v3, (0.0, 2.0))
v4 = parse_point(raw_v4, (0.0, 1.0))

verts = [v1, v2, v3, v4]
b_types = [2, 1, 2, 3] # Типи границь для 12 варіанту

col1, col2 = st.columns([2, 1])

nodes, elements, boundaries = generate_mesh(nx, ny, verts, b_types)

element_angles = []
global_min_angle = 180.0
for element in elements:
    p1, p2, p3 = nodes[element[0]], nodes[element[1]], nodes[element[2]]
    min_deg = math.degrees(triangle_min_angle(p1, p2, p3))
    element_angles.append(min_deg)
    if min_deg < global_min_angle:
        global_min_angle = min_deg

with col1:
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
    st.metric("Найменший кут отриманої сітки", f"{global_min_angle:.2f}°")
    
    elements_log = "\n".join([f"E{i}: {e} | Мін. кут: {element_angles[i]:.1f}°" for i, e in enumerate(elements)])
    st.text_area("Масив зв'язності та кути", elements_log, height=180)
    
    nodes_log = "\n".join([f"N{i}: ({n[0]:.2f}, {n[1]:.2f}) | {b}" for i, (n, b) in enumerate(zip(nodes, boundaries))])
    st.text_area("Вузли (ID: X, Y | Тип границі)", nodes_log, height=180)

st.markdown("---")
with st.expander("📄 Звіт до виконання завдання №1 (Метод скінченних елементів)", expanded=True):
    st.markdown(r"""
### 1. Формулювання завдання
Розглядається двовимірне еліптичне диференціальне рівняння другого порядку:
$$-\sum_{i,j=1}^{2} \frac{\partial}{\partial x_i} a_{ij}(x) \frac{\partial u}{\partial x_j} + du = f, \quad x_1, x_2 \in \Omega$$

**Параметри для Варіанту 12:**
* Коефіцієнти: $a_{11} = 8$, $a_{12} = a_{21} = 0$, $a_{22} = 2$, $d = 0$, $f = 1$.
* Область $\Omega$: чотирикутник з вершинами $V_1(1,0)$, $V_2(2,0)$, $V_3(0,2)$, $V_4(0,1)$.
* Крайові умови:
  * Грань $V_2-V_3$: $1^\circ$ ($u = 0$, умова Діріхле).
  * Грані $V_1-V_2$ та $V_3-V_4$: $2^\circ$ ($Nu = 0$, умова Неймана).
  * Грань $V_4-V_1$: $3^\circ$ ($\beta Nu + \delta(u - u_c) = 0$, умова Робіна / змішана).

---

### 2. Загальна дорожня карта чисельного розв'язання (Етапи МСЕ)
1. **Триангуляція області (виконано в межах Завдання №1):** поділ неперервної області на множину симплекс-елементів (трикутників), нумерація вузлів, формування масиву зв'язності та маркування граничних вершин.
2. **Слабке (варіаційне) формулювання задачі:** зведення вихідного ДРЧП до інтегральної форми через множення на вагову (пробну) функцію $v$ та інтегрування частинами за формулою Гріна; теоретичне обґрунтування існування і єдиності розв'язку за теоремою Лакса–Мільграма (виконується аналітично на листку).
3. **Обчислення локальних матриць:** апроксимація розв'язку лінійними базисними функціями форми $u = N_e q_e$ та аналітичне/чисельне інтегрування локальної матриці жорсткості $K_e = \int_{\Omega_e} (CN)^T A (CN) d\Omega$ і вектора навантаження $F_e = \int_{\Omega_e} N^T f d\Omega$.
4. **Врахування граничних умов:** облік контурних інтегралів від умови 3-го роду вздовж ребер грані $V_4-V_1$ та модифікація глобальної СЛАР методом викреслювання рядків/стовпців або штрафних коефіцієнтів для умови 1-го роду ($u=0$).
5. **Розв'язок СЛАР:** розв'язання глобальної системи лінійних алгебраїчних рівнянь $K \cdot U = F$ відносно невідомих значень потенціалу у внутрішніх вузлах сітки.
6. **Візуалізація розв'язку:** побудова ізоліній (контурів), градієнтних полів або 3D-поверхні відновленої функції $u(x_1, x_2)$ по отриманих вузлових значеннях.

---

### 3. Опис підходів та способу реалізації Етапу 1
* **Генерація просторових вузлів:** використано білінійну інтерполяцію над чотирма опорними точками, параметризовану на квадраті $(u, v) \in [0, 1]^2$ із кроками дискретизації $Nx$ та $Ny$.
* **Триангуляція з критерієм Делоне:** кожна чотирикутна комірка розбивається однією з двох можливих діагоналей. За теоремою косинусів обчислюються всі внутрішні кути утворених трикутників; обирається варіант, який максимізує мінімальний кут (локальний фліп Делоне), усуваючи надмірно вироджені елементи.
* **Маркування граней:** реалізовано автоматичне зіставлення меж $u=0, 1$ та $v=0, 1$ із відповідними типами граничних умов 1–3 роду.

---

### 4. Отримані результати
* Побудовано інтерактивний графічний веб-додаток (Streamlit), що дозволяє керувати густиною $Nx, Ny$ та геометрією області.
* Сформовано наскрізну нумерацію та коректний масив зв'язності (інцидентності) елементів і вершин.
* Забезпечено числовий контроль мінімального кута отриманої сітки для оцінки її придатності до подальшого складання матриць жорсткості.

---

### 5. Висновок
Перший етап МСЕ (геометрична дискретизація) виконано у повному обсязі відповідно до вимог Делоне. Отримані масиви координат, зв'язності та маркування граничних вузлів є повністю підготовленими вхідними даними для переходу до Етапу 3 (обчислення локальних матриць $K_e, F_e$).
""")
