import streamlit as st
import random
import string
import json
import streamlit.components.v1 as components

# --- Configuração da Página ---
st.set_page_config(page_title="Caça-Palavras Pro", layout="wide")

# --- Banco de Dados ---
DADOS = {
    "Animais": {
        "Fácil": ["GATO", "CAO", "VACA", "RATO", "PEIXE"],
        "Médio": ["CAVALO", "TIGRE", "LEAO", "ZEBRA", "URSO"],
        "Difícil": ["ORNITORRINCO", "FLAMINGO", "CROCODILO", "GOLFINHO", "CAMALEAO"]
    },
    "Frutas": {
        "Fácil": ["MACA", "PERA", "UVA", "BANANA", "KIWI"],
        "Médio": ["ABACAXI", "MELANCIA", "LARANJA", "MANGA", "COCO"],
        "Difícil": ["PITANGA", "JABUTICABA", "GRAVIOLA", "TAMARINDO", "ACEROLA"]
    },
    "Países": {
        "Fácil": ["BRASIL", "CHILE", "PERU", "MEXICO", "CANADA"],
        "Médio": ["ALEMANHA", "FRANCA", "ITALIA", "JAPAO", "RUSSIA"],
        "Difícil": ["MOCAMBIQUE", "AZERBAIJAO", "CAZAQUISTAO", "INDONESIA", "LUXEMBURGO"]
    }
}

# --- Sidebar ---
with st.sidebar:
    st.header("Configurações")
    categoria = st.selectbox("Categoria", list(DADOS.keys()))
    nivel = st.radio("Dificuldade", ["Fácil", "Médio", "Difícil"])
    btn_novo = st.button("Gerar Novo Jogo ♻️", use_container_width=True)

# --- Lógica de Geração ---
def gerar_tabuleiro(palavras, tamanho=15):
    grid = [['' for _ in range(tamanho)] for _ in range(tamanho)]
    locs = {}
    for p in palavras:
        p = p.upper()
        colocada = False
        for _ in range(100):
            if colocada: break
            ori = random.choice(['H', 'V'])
            l, c = (random.randint(0,tamanho-1), random.randint(0,tamanho-len(p))) if ori=='H' else (random.randint(0,tamanho-len(p)), random.randint(0,tamanho-1))
            if all(grid[l+i*(ori=='V')][c+i*(ori=='H')] in ('', p[i]) for i in range(len(p))):
                coords = []
                for i in range(len(p)):
                    grid[l+i*(ori=='V')][c+i*(ori=='H')] = p[i]
                    coords.append({'r': l+i*(ori=='V'), 'c': c+i*(ori=='H')})
                locs[p] = coords
                colocada = True
    for r in range(tamanho):
        for c in range(tamanho):
            if grid[r][c] == '': grid[r][c] = random.choice(string.ascii_uppercase)
    return grid, locs

if 'jogo' not in st.session_state or btn_novo:
    palavras = DADOS[categoria][nivel]
    grid, locs = gerar_tabuleiro(palavras)
    st.session_state.jogo = {"grid": grid, "locs": locs, "palavras": palavras}

# --- Interface Frontend (HTML/JS) ---
# O Canvas agora é auto-contido e desenha as marcações permanentes.
game_json = json.dumps(st.session_state.jogo)

html_content = f"""
<div id="wrapper" style="display: flex; flex-direction: column; align-items: center; font-family: sans-serif; color: white;">
    <canvas id="cvs" style="background: #1e1e1e; border: 3px solid #444; border-radius: 10px; cursor: crosshair; touch-action: none;"></canvas>
    <div id="list" style="margin-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center;"></div>
</div>

<script>
    const data = {game_json};
    const cvs = document.getElementById('cvs');
    const ctx = cvs.getContext('2d');
    const size = 15;
    const cellSize = 30;
    cvs.width = size * cellSize;
    cvs.height = size * cellSize;

    let foundWords = [];
    let isDown = false;
    let start = null, curr = null;

    function getPos(e) {{
        const r = cvs.getBoundingClientRect();
        const x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
        const y = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
        return {{ c: Math.floor(x/cellSize), r: Math.floor(y/cellSize) }};
    }}

    function draw() {{
        ctx.clearRect(0,0,cvs.width,cvs.height);
        
        // Desenha palavras já encontradas (VERDE PERMANENTE)
        foundWords.forEach(w => {{
            ctx.fillStyle = "rgba(76, 175, 80, 0.5)";
            data.locs[w].forEach(cell => ctx.fillRect(cell.c*cellSize, cell.r*cellSize, cellSize, cellSize));
        }});

        // Desenha seleção atual (VERMELHO)
        if(isDown && start && curr) {{
            ctx.fillStyle = "rgba(255, 75, 75, 0.4)";
            getPath(start, curr).forEach(cell => ctx.fillRect(cell.c*cellSize, cell.r*cellSize, cellSize, cellSize));
        }}

        // Desenha letras
        ctx.fillStyle = "white";
        ctx.font = "bold 16px monospace";
        ctx.textAlign = "center";
        for(let r=0; r<size; r++)
            for(let c=0; c<size; c++)
                ctx.fillText(data.grid[r][c], c*cellSize + cellSize/2, r*cellSize + cellSize/1.5);
    }}

    function getPath(s, e) {{
        let path = [];
        const dr = e.r - s.r, dc = e.c - s.c;
        if (dr !== 0 && dc !== 0) return []; // Apenas H e V
        const steps = Math.max(Math.abs(dr), Math.abs(dc));
        for(let i=0; i<=steps; i++) path.push({{ r: s.r + i*(dr===0?0:dr/steps), c: s.c + i*(dc===0?0:dc/steps) }});
        return path;
    }}

    function updateList() {{
        const div = document.getElementById('list');
        div.innerHTML = data.palavras.map(p => 
            `<span style="padding:5px 10px; border-radius:15px; background:${{foundWords.includes(p)?'#2e7d32':'#444'}}">${{foundWords.includes(p)?'✅':'⬜'}} ${{p}}</span>`
        ).join('');
    }}

    cvs.onmousedown = cvs.ontouchstart = (e) => {{ isDown = true; start = curr = getPos(e); draw(); if(e.touches) e.preventDefault(); }};
    window.onmousemove = window.ontouchmove = (e) => {{ if(isDown) {{ curr = getPos(e); draw(); }} }};
    window.onmouseup = window.ontouchend = () => {{
        if(isDown) {{
            const p = getPath(start, curr).map(c => data.grid[c.r][c.c]).join('');
            if(data.palavras.includes(p) && !foundWords.includes(p)) foundWords.push(p);
            isDown = false; draw(); updateList();
            if(foundWords.length === data.palavras.length) setTimeout(()=>alert("Você Venceu!"), 100);
        }}
    }};

    updateList(); draw();
</script>
"""

st.title("🧩 Caça-Palavras Master")
st.write(f"### {categoria} - {nivel}")
components.html(html_content, height=600)