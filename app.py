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
with st.expander("📄 Звіт до виконання завдання №1", expanded=True):
    st.markdown("""
### 1. Формулювання завдання
Здійснити розбиття двовимірної області на скінченні елементи трикутної форми (триангуляцію) для чисельного розв'язання крайової задачі математичної фізики.
* **Область (Варіант 12):** Чотирикутник з вершинами $V_1(1,0)$, $V_2(2,0)$, $V_3(0,2)$, $V_4(0,1)$.
* **Вимоги:**
  1. Виконання геометричної умови Делоне.
  2. Можливість параметричного згущення сітки та контроль мінімального кута.
  3. Наскрізне нумерування вузлів та трикутників, формування масиву зв'язності.
  4. Маркування вузлів границь відповідними типами крайових умов ($1^0, 2^0, 3^0$).
  5. Можливість побудови сітки для довільної геометрії чотирикутника через вебінтерфейс.

---

### 2. Опис підходів і способу реалізації
1. **Генерація базових координат:** Реалізовано узагальнену білінійну інтерполяцію між чотирма довільними точками контуру. Простір параметрів $(u, v) \in [0, 1] [0, 1]$ розбивається на кроки $Nx$ та $Ny$, що формує базову множину просторових вузлів.
2. **Оптимізація Делоне та контроль кутів:** Для кожної утвореної чотирикутної комірки розглядаються два варіанти проведення діагоналей. За допомогою теореми косинусів обчислюються внутрішні кути трикутників. Алгоритм фіксує діагональ, що максимізує мінімальний внутрішній кут (локальний критерій Делоне), запобігаючи появі вироджених елементів[cite: 7].
3. **Маркування границь:** Перевіряється належність кожного вузла параметричним межам $u=0, u=1, v=0, v=1$, кожній з яких відповідає заданий тип граничних умов:
   * Грань $V_2-V_3$: $1^0$ (умова Діріхле, $u=0$).
   * Грані $V_1-V_2$ та $V_3-V_4$: $2^0$ (умова Неймана, $Nu=0$).
   * Грань $V_4-V_1$: $3^0$ (змішана крайова умова).

---

### 3. Отримані результати
* Створено інтерактивний вебдодаток на базі Python та Streamlit.
* Реалізовано компактну панель введення координат точок парою чисел (`X, Y`) та регулювання густини ($Nx, Ny$).
* Програма динамічно формує та візуалізує:
  * Двовимірну сітку скінченних елементів з підписами номерів вузлів та трикутників.
  * Кольорове маркування граничних вузлів відповідно до роду крайових умов.
  * Топологічну матрицю зв'язності (інцидентності).
  * Числове значення мінімального кута сітки для контролю якості розбиття.

---

### 4. Висновок
Розроблений алгоритм успішно розв'язує задачу дискретизації двовимірної області для подальшого застосування методу скінченних елементів. Локальна оптимізація за Делоне забезпечує коректну геометрію трикутників[cite: 7], а структура масиву зв'язності та вектор маркування границь повністю готові для формування глобальної матриці жорсткості та вектора навантаження[cite: 1, 7].
""")
