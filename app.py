import streamlit as st
import numpy as np
import motor_rigidez as mr
import cargas as cr
import visualizador as vi

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Análisis de Escaleras | Criterio Estructural", layout="wide")

st.markdown("""
    <style>
    :root {
        --azul-profundo: #1A2530;
        --naranja-estructural: #E67E22;
        --gris-claro: #F4F5F7;
    }
    .titulo-principal { color: #1A2530; font-weight: bold; border-bottom: 3px solid #E67E22; padding-bottom: 10px; }
    .stButton>button { background-color: #1A2530; color: white; border-radius: 5px; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: #E67E22; color: white; border: none; }
    .caja-resultados { background-color: #f8fafc; padding: 15px; border-left: 5px solid #E67E22; border-radius: 5px; margin-bottom: 15px;}
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
    
    # Variables globales de coordenadas
    x1, y1 = 0.0, 0.0
    x2, y2, x3, y3 = 0.0, 0.0, 0.0, 0.0
    
    if modo_geo == "Rápido (Plantillas)":
        plantilla = st.selectbox("Configuración:", [
            "Descanso + Tramo inclinado", 
            "Tramo inclinado + Descanso", 
            "Dos tramos inclinados"
        ])
        
        # Lógica de apagado UI para desniveles según plantilla
        es_descanso_1 = (plantilla == "Descanso + Tramo inclinado")
        es_descanso_2 = (plantilla == "Tramo inclinado + Descanso")
        
        col1, col2 = st.columns(2)
        with col1:
            L1 = st.number_input("L horiz. Tramo 1 (m)", value=1.20, step=0.1)
            H1 = st.number_input("Desnivel 1 (m)", value=0.00, step=0.1, disabled=es_descanso_1)
            if es_descanso_1: H1 = 0.0 # Fuerza a 0 internamente aunque esté deshabilitado
        with col2:
            L2 = st.number_input("L horiz. Tramo 2 (m)", value=3.00, step=0.1)
            H2 = st.number_input("Desnivel 2 (m)", value=1.60, step=0.1, disabled=es_descanso_2)
            if es_descanso_2: H2 = 0.0
            
        # Traducción de plantilla a coordenadas
        if plantilla == "Descanso + Tramo inclinado":
            x2, y2 = L1, 0.0
            x3, y3 = L1 + L2, H2
        elif plantilla == "Tramo inclinado + Descanso":
            x2, y2 = L1, H1
            x3, y3 = L1 + L2, H1
        else:
            x2, y2 = L1, H1
            x3, y3 = L1 + L2, H1 + H2
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
    # Agregado: Rodillo
    apoyo_n1 = st.selectbox("Apoyo N1 (Inicial)", ["Articulado", "Empotrado", "Rodillo", "Libre"], index=0)
    apoyo_n3 = st.selectbox("Apoyo N3 (Final)", ["Articulado", "Empotrado", "Rodillo", "Libre"], index=0)
    
    st.markdown("---")
    st.header("2. Sección y Material")
    b = st.number_input("Ancho b (m)", value=1.00, step=0.1)
    h = st.number_input("Espesor h (m)", value=0.15, step=0.01)
    fc = st.number_input("f'c (MPa)", value=28.0, step=1.0)
    
    modificar_I = st.checkbox("⚙️ Modificar Inercia (I) manualmente")
    I_calc = (b * h**3) / 12
    if modificar_I:
        I_usada = st.number_input("I (m⁴)", value=float(I_calc), format="%.6f")
    else:
        I_usada = I_calc
        st.info(f"Inercia calculada: {I_calc:.6f} m⁴")

    st.markdown("---")
    # Título y nota actualizados
    st.header("3. Cargas Gravitacionales (kN/m horizontal)")
    st.caption("Ingresa las cargas por metro de proyección horizontal. La app realiza automáticamente la estática sobre la longitud inclinada.")
    
    # Cargas divididas por tramo
    colA, colB = st.columns(2)
    with colA: st.markdown("**Tramo 1**")
    with colB: st.markdown("**Tramo 2**")
    
    colC, colD = st.columns(2)
    with colC: D1 = st.number_input("C. Muerta D1", value=6.6, step=0.1)
    with colD: D2 = st.number_input("C. Muerta D2", value=6.6, step=0.1)
    
    colE, colF = st.columns(2)
    with colE: L1_carga = st.number_input("C. Viva L1", value=3.0, step=0.1)
    with colF: L2_carga = st.number_input("C. Viva L2", value=3.0, step=0.1)
    
    st.markdown("**Combinación de Diseño**")
    col3, col4 = st.columns(2)
    with col3:
        f_D = st.number_input("Factor D", value=1.20, step=0.05)
    with col4:
        f_L = st.number_input("Factor L", value=1.60, step=0.05)
        
    Wu1 = (f_D * D1) + (f_L * L1_carga)
    Wu2 = (f_D * D2) + (f_L * L2_carga)
    st.success(f"**Wu1 = {Wu1:.2f} kN/m | Wu2 = {Wu2:.2f} kN/m**")

    st.markdown("---")
    btn_analizar = st.button("▶ ANALIZAR")


# ==========================================
# ÁREA PRINCIPAL
# ==========================================
if not btn_analizar:
    st.info("👈 Define la geometría, sección y cargas en el panel izquierdo. Luego haz clic en 'Analizar'.")
    
    # Dibujar geometría vacía previa con los apoyos seleccionados
    nodos_ini = [[x1, y1], [x2, y2], [x3, y3]]
    elems_ini = [(0, 1), (1, 2)]
    fig_ini = vi.graficar_modelo_basico(nodos_ini, elems_ini, "Geometría Definida", apoyos=[apoyo_n1, "Libre", apoyo_n3])
    st.plotly_chart(fig_ini, use_container_width=True)

else:
    # ---------------------------------------------------------
    # MOTOR DE CÁLCULO
    # ---------------------------------------------------------
    E = 4700 * np.sqrt(fc) * 1000 # kN/m2
    A = b * h
    I = I_usada
    
    nodos = [[x1, y1], [x2, y2], [x3, y3]]
    elementos = [(0, 1), (1, 2)]
    gdl_elementos = [[0,1,2, 3,4,5], [3,4,5, 6,7,8]]
    
    # Elemento 1 (Usa Wu1)
    L_e1, c1, s1 = mr.calcular_geometria_elemento(x1, y1, x2, y2)
    k1_loc = mr.matriz_rigidez_local(E, A, I, L_e1)
    T1 = mr.matriz_transformacion(c1, s1)
    k1_glob = mr.matriz_rigidez_global_elemento(k1_loc, T1)
    
    wx1, wy1 = cr.descomponer_carga_gravedad(Wu1, c1, s1, es_proyeccion_horizontal=True)
    Ffem1 = cr.calcular_FEM_local(wx1, wy1, L_e1)
    Feq1 = cr.vector_cargas_equivalentes_global(Ffem1, T1)
    
    # Elemento 2 (Usa Wu2)
    L_e2, c2, s2 = mr.calcular_geometria_elemento(x2, y2, x3, y3)
    k2_loc = mr.matriz_rigidez_local(E, A, I, L_e2)
    T2 = mr.matriz_transformacion(c2, s2)
    k2_glob = mr.matriz_rigidez_global_elemento(k2_loc, T2)
    
    wx2, wy2 = cr.descomponer_carga_gravedad(Wu2, c2, s2, es_proyeccion_horizontal=True)
    Ffem2 = cr.calcular_FEM_local(wx2, wy2, L_e2)
    Feq2 = cr.vector_cargas_equivalentes_global(Ffem2, T2)
    
    # Ensamblaje
    K_sis = mr.ensamblar_K_sistema([k1_glob, k2_glob], gdl_elementos, 3)
    
    F_sis = np.zeros(9)
    F_sis[0:6] += Feq1
    F_sis[3:9] += Feq2
    
    # El nodo 2 (descanso/quiebre) es libre por defecto en escaleras
    restricciones = mr.definir_gdl_restringidos([apoyo_n1, "Libre", apoyo_n3])
    
    # Solución (con captura de error para estructuras inestables)
    try:
        Desp, Reacciones = mr.resolver_sistema(K_sis, F_sis, restricciones)
    except np.linalg.LinAlgError:
        st.error("🚨 **Error de Estática:** La estructura es inestable (matriz singular). Por ejemplo, si usas dos rodillos horizontales, la escalera no tiene restricción para no deslizarse. Cambia al menos un apoyo a 'Articulado' o 'Empotrado'.")
        st.stop()
    
    # Recuperación de Fuerzas
    Fext1 = cr.fuerzas_finales_extremos(k1_loc, T1, Desp[0:6], Ffem1)
    Fext2 = cr.fuerzas_finales_extremos(k2_loc, T2, Desp[3:9], Ffem2)
    
    x1_arr, N1, V1, M1 = cr.generar_datos_diagramas(Fext1, wx1, wy1, L_e1)
    x2_arr, N2, V2, M2 = cr.generar_datos_diagramas(Fext2, wx2, wy2, L_e2)
    
    # ---------------------------------------------------------
    # RENDERIZADO DE INTERFAZ
    # ---------------------------------------------------------
    st.subheader("🟧 Nivel 2: Resultados del Análisis")
    tab_diag, tab_def, tab_reac = st.tabs(["📊 Diagramas (M, V, N)", "📉 Deformada", "📐 Reacciones"])
    
    with tab_diag:
        # Momento
        fig_M = vi.graficar_diagrama(nodos, elementos, [x1_arr, x2_arr], [M1, M2], 
                                     "Diagrama de Momento (kN·m)", "#E67E22", "rgba(230, 126, 34, 0.2)", invertir_signo=True)
        st.plotly_chart(fig_M, use_container_width=True)
        
        # Cortante
        fig_V = vi.graficar_diagrama(nodos, elementos, [x1_arr, x2_arr], [V1, V2], 
                                     "Diagrama de Cortante (kN)", "#1A2530", "rgba(26, 37, 48, 0.2)")
        st.plotly_chart(fig_V, use_container_width=True)
        
        # Axial
        fig_N = vi.graficar_diagrama(nodos, elementos, [x1_arr, x2_arr], [N1, N2], 
                                     "Diagrama de Fuerza Axial (kN)", "#64748b", "rgba(100, 116, 139, 0.2)")
        st.plotly_chart(fig_N, use_container_width=True)

    with tab_def:
        # Calcular desplazamiento nodal máximo (traslacional)
        desp_traslacionales = [np.hypot(Desp[i], Desp[i+1]) for i in range(0, 9, 3)]
        max_delta_mm = max(desp_traslacionales) * 1000
        
        # Graficadora de deformada actualizada (ahora auto-escala)
        fig_def = vi.graficar_deformada(nodos, elementos, Desp)
        st.plotly_chart(fig_def, use_container_width=True)
        st.markdown(f'<div class="caja-resultados"><b>Desplazamiento nodal máximo (\(\delta_{{max}}\)):</b> {max_delta_mm:.2f} mm</div>', unsafe_allow_html=True)
        
    with tab_reac:
        colR1, colR2 = st.columns(2)
        with colR1:
            st.write(f"**Reacciones Nodo 1 ({apoyo_n1})**")
            st.write(f"Rx: {Reacciones[0]:.2f} kN")
            st.write(f"Ry: {Reacciones[1]:.2f} kN")
            st.write(f"Mz: {Reacciones[2]:.2f} kN·m")
        with colR2:
            st.write(f"**Reacciones Nodo 3 ({apoyo_n3})**")
            st.write(f"Rx: {Reacciones[6]:.2f} kN")
            st.write(f"Ry: {Reacciones[7]:.2f} kN")
            st.write(f"Mz: {Reacciones[8]:.2f} kN·m")

    # ---------------------------------------------------------
    # MÓDULO DE VERIFICACIONES BÁSICAS DE DISEÑO (NSR-10 / ACI 318)
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("🟦 Nivel 3: Verificaciones Básicas de Diseño")
    st.write("Comprobación de la máxima demanda. *Asume acero fy = 420 MPa y recubrimiento al centroide de 4 cm.*")
    
    # Encontrar máximos absolutos
    Mu_max = max(np.max(np.abs(M1)), np.max(np.abs(M2)))
    Vu_max = max(np.max(np.abs(V1)), np.max(np.abs(V2)))
    # Evaluar la tracción máxima. (Nuestra convención: Tracción es positiva).
    # Si todo el diagrama es negativo (compresión), max() tomará el 0.0
    Nu_traccion = max([0.0, np.max(N1), np.max(N2)])
    
    # Parámetros de Diseño
    d_m = h - 0.04 # Peralte efectivo en metros
    fy = 420 # MPa
    phi_f = 0.90
    phi_v = 0.75
    
    # Cortante del Concreto (NSR-10)
    # Eq C.11-3 básica
    Vc1 = 0.17 * np.sqrt(fc) * b * d_m * 1000 # en kN 
    
    # Eq C.11-8 tracción axial. 
    # El término (Nu/Ag) debe estar en MPa. Nu [kN] / (b*h [m2] * 1000) = [MPa]
    # Se usa -Nu_traccion porque la NSR-10 asume tracción como valor negativo en la fórmula.
    Vc2 = 0.17 * np.sqrt(fc) * b * d_m * 1000 * (1 + (0.29 * (-Nu_traccion) / (b * h * 1000)))
    
    # El concreto no puede aportar resistencia negativa al cortante si está muy agrietado
    Vc2 = max(0.0, Vc2)
    phi_Vc = phi_v * min(Vc1, Vc2)
    
    # Acero de Flexión (Ecuación Cuadrática Exacta de rho)
    # Mu = phi * rho * b * d^2 * fy * (1 - 0.588235 * rho * fy / fc)
    coef_A = 0.588235 * fy / fc
    coef_B = -1.0
    coef_C = (Mu_max) / (phi_f * b * d_m**2 * fy * 1000) # Mu en kNm convertido
    
    # Resolver ecuación cuadrática para rho
    discriminante = coef_B**2 - 4 * coef_A * coef_C
    if discriminante < 0:
        texto_As = "¡Sección Insuficiente! Aumente el espesor (h)."
        As_req_cm2 = 0
    else:
        rho_req = (-coef_B - np.sqrt(discriminante)) / (2 * coef_A)
        As_req_cm2 = rho_req * b * d_m * 10000 # cm2
        texto_As = f"{As_req_cm2:.2f} cm²"
        
    As_min_cm2 = 0.0018 * b * h * 10000
    
    col_flex, col_cort = st.columns(2)
    with col_flex:
        st.markdown('<div class="caja-resultados">', unsafe_allow_html=True)
        st.markdown("#### 📏 Diseño a Flexión")
        st.write(f"**Demanda Crítica $|M_u|$:** {Mu_max:.2f} kN·m")
        st.write(f"**$A_s$ requerido:** {texto_As}")
        st.write(f"**$A_s$ mínimo (NSR-10):** {As_min_cm2:.2f} cm²")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_cort:
        st.markdown('<div class="caja-resultados">', unsafe_allow_html=True)
        st.markdown("#### ✂️ Diseño a Cortante")
        st.write(f"**Demanda Crítica $|V_u|$:** {Vu_max:.2f} kN; **$|N_u|$:** {Nu_max:.2f} kN")
        st.write(f"**Capacidad del concreto $\phi V_c$:** {phi_Vc:.2f} kN, acá se usa el menor valor obtenido entre EQ C.11-3 y C.11-8")
        if Vu_max <= phi_Vc:
            st.write("✅ **Chequeo:** $V_u \le \phi V_c$ (No requiere refuerzo transversal)")
        else:
            st.write("❌ **Chequeo:** $V_u > \phi V_c$ (Requiere aumentar espesor o colocar estribos)")
        st.markdown('</div>', unsafe_allow_html=True)

    # ==========================================
    # CAJA NEGRA (REFERENCIA TÉCNICA)
    # ==========================================
    st.markdown("---")
    with st.expander("🔧 Información Técnica del Modelo (Motor Matricial)"):
        st.caption("Euler-Bernoulli: Matriz ensamblada de 9x9 (3 Nodos x 3 GDL). F_eq son las cargas distribuidas proyectadas como momentos/cortantes de empotramiento perfecto.")
        st.write("**Matriz de Rigidez del Sistema [K]:**")
        st.dataframe(K_sis)
        st.write("**Vector de Cargas [F]:**")
        st.dataframe(F_sis)
