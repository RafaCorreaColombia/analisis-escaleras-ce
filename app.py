import streamlit as st
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Análisis de Escaleras | Criterio Estructural", layout="wide")

st.markdown("""
    <style>
    :root {
        --azul-profundo: #1A2530;
        --naranja-estructural: #E67E22;
        --gris-claro: #F4F5F7;
    }
    .titulo-principal { color: var(--azul-profundo); font-weight: bold; border-bottom: 3px solid var(--naranja-estructural); padding-bottom: 10px; }
    .stButton>button { background-color: var(--azul-profundo); color: white; border-radius: 5px; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: var(--naranja-estructural); color: white; border: none; }
    .caja-resultados { background-color: #f8fafc; padding: 15px; border-left: 5px solid var(--naranja-estructural); border-radius: 5px; margin-bottom: 15px;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="titulo-principal">Análisis Rápido de Escaleras</h1>', unsafe_allow_html=True)
st.markdown("**Criterio Estructural** | Herramienta didáctica para idealizar, analizar y verificar rápidamente modelos de escaleras de un tramo.")

# ==========================================
# BARRA LATERAL: ENTRADA DE DATOS
# ==========================================
with st.sidebar:
    st.image("https://via.placeholder.com/250x80/1A2530/FFFFFF?text=CRITERIO+ESTRUCTURAL")
    
    st.header("1. Geometría y Apoyos")
    modo_geo = st.radio("Modo de ingreso:", ["Rápido (Plantillas)", "Avanzado (Coordenadas)"])
    
    if modo_geo == "Rápido (Plantillas)":
        plantilla = st.selectbox("Configuración:", [
            "Descanso + Tramo inclinado", 
            "Tramo inclinado + Descanso", 
            "Dos tramos inclinados"
        ])
        col1, col2 = st.columns(2)
        with col1:
            L1 = st.number_input("L Tramo 1 (m)", value=1.20, step=0.1)
            H1 = st.number_input("Desnivel 1 (m)", value=0.00, step=0.1)
        with col2:
            L2 = st.number_input("L Tramo 2 (m)", value=3.00, step=0.1)
            H2 = st.number_input("Desnivel 2 (m)", value=1.60, step=0.1)
    else:
        st.caption("Coordenadas N1 (0,0) por defecto")
        col1, col2 = st.columns(2)
        with col1:
            x2 = st.number_input("X2 (m)", value=1.20, step=0.1)
            x3 = st.number_input("X3 (m)", value=4.20, step=0.1)
        with col2:
            y2 = st.number_input("Y2 (m)", value=0.00, step=0.1)
            y3 = st.number_input("Y3 (m)", value=1.60, step=0.1)

    st.markdown("**Condiciones de Apoyo**")
    apoyo_n1 = st.selectbox("Apoyo N1 (Inicial)", ["Articulado", "Empotrado", "Libre"])
    apoyo_n3 = st.selectbox("Apoyo N3 (Final)", ["Articulado", "Empotrado", "Libre"])
    
    st.markdown("---")
    st.header("2. Sección y Material")
    b = st.number_input("Ancho b (m)", value=1.00, step=0.1)
    h = st.number_input("Espesor h (m)", value=0.15, step=0.01)
    fc = st.number_input("f'c (MPa)", value=21.0, step=1.0)
    
    # Modificador didáctico de Inercia
    modificar_I = st.checkbox("⚙️ Modificar Inercia (I) manualmente")
    I_calc = (b * h**3) / 12
    if modificar_I:
        I_usada = st.number_input("I (m⁴)", value=float(I_calc), format="%.6f")
    else:
        I_usada = I_calc
        st.info(f"Inercia calculada: {I_calc:.6f} m⁴")

    st.markdown("---")
    st.header("3. Cargas Verticales")
    D = st.number_input("Carga Muerta D (kN/m)", value=6.6, step=0.1, help="Suma de peso propio, peldaños, acabados, etc.")
    L_carga = st.number_input("Carga Viva L (kN/m)", value=3.0, step=0.1)
    
    st.markdown("**Combinación de Diseño**")
    col3, col4 = st.columns(2)
    with col3:
        f_D = st.number_input("Factor D", value=1.20, step=0.05)
    with col4:
        f_L = st.number_input("Factor L", value=1.60, step=0.05)
        
    Wu = (f_D * D) + (f_L * L_carga)
    st.success(f"**Wu = {Wu:.2f} kN/m**")

    st.markdown("---")
    btn_analizar = st.button("▶ ANALIZAR Y DISEÑAR")


# ==========================================
# ÁREA PRINCIPAL
# ==========================================
if not btn_analizar:
    st.info("👈 Define la geometría, sección y cargas en el panel izquierdo. Luego haz clic en 'Analizar y Diseñar'.")
    # Placeholder para gráfico de geometría inicial
else:
    st.subheader("🟦 Nivel 1: Modelo Idealizado")
    st.write("*(Gráfico Plotly: Nodos, conectividad y apoyos)*")
    
    st.markdown("---")
    st.subheader("🟧 Nivel 2: Resultados del Análisis")
    tab_diag, tab_def, tab_reac = st.tabs(["📊 Diagramas (M, V, N)", "📉 Deformada", "📐 Reacciones"])
    
    with tab_diag:
        st.write("*(Gráficos Plotly: Momento, Cortante y Axial superpuestos en la geometría)*")
    with tab_def:
        st.write("*(Gráfico Plotly: Línea original vs Deformada amplificada)*")
        st.markdown(f'<div class="caja-resultados"><b>Desplazamiento máximo (\(\delta_{{max}}\)):</b> 8.4 mm (Elemento 2)</div>', unsafe_allow_html=True)
    with tab_reac:
        st.write("*(Tabla y esquema visual de reacciones Rx, Ry, Mz en N1 y N3)*")

    st.markdown("---")
    st.subheader("🟦 Nivel 3: Verificación de Diseño Crítico")
    st.write("Comprobación rápida de los puntos de máxima demanda. *Asume acero fy = 420 MPa y recubrimiento estándar.*")
    
    col_flex, col_cort = st.columns(2)
    with col_flex:
        st.markdown('<div class="caja-resultados">', unsafe_allow_html=True)
        st.markdown("#### 📏 Diseño a Flexión")
        st.write("**Demanda Crítica:** $M_u^+ = 32.5$ kN·m (Elemento 2)")
        st.write("**$A_s$ requerido:** 6.1 cm²")
        st.write("**$A_s$ mínimo (NSR-10):** 2.7 cm²")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_cort:
        st.markdown('<div class="caja-resultados">', unsafe_allow_html=True)
        st.markdown("#### ✂️ Diseño a Cortante")
        st.write("**Demanda Crítica:** $V_u = 28.4$ kN (Nodo 2)")
        st.write("**Capacidad del concreto $\phi V_c$:** 85.2 kN")
        st.write("✅ **Chequeo:** $V_u < \phi V_c$ (No requiere refuerzo transversal)")
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # CAJA NEGRA (REFERENCIA TÉCNICA)
    # ==========================================
    st.markdown("---")
    with st.expander("🔧 Información Técnica del Modelo (Motor Matricial)"):
        st.caption("La herramienta utiliza un modelo matricial de elementos de pórtico 2D (Euler-Bernoulli: Axial + Flexión). Esta información se muestra únicamente como referencia para validación técnica.")
        st.write("**Matriz Global Ensamblada [K]**")
        st.write("*(Aquí volcaremos el output de NumPy)*")
        st.write("**Vector de Cargas Nodal Equivalente {F}**")
        st.write("*(Transformación de cargas distribuidas a FEM)*")
