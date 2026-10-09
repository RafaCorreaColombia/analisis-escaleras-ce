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
    .titulo-principal { color: var(--azul-profundo); font-weight: bold; border-bottom: 3px solid var(--naranja-estructural); padding-bottom: 10px; }
    .stButton>button { background-color: var(--azul-profundo); color: white; border-radius: 5px; width: 100%; font-weight: bold; }
    .stButton>button:hover { background-color: var(--naranja-estructural); color: white; border: none; }
    
    /* Estética Criterio Estructural */
    .caja-resultados { 
        background-color: #fdf6f0; 
        padding: 15px 20px; 
        border-left: 6px solid var(--naranja-estructural); 
        border-radius: 8px; 
        margin-bottom: 15px;
        color: var(--azul-profundo);
    }
    .caja-resultados h4 { margin-top: 0; color: var(--azul-profundo); font-weight: bold; border-bottom: 1px solid #ddd; padding-bottom: 8px; }
    .caja-resultados p { margin: 8px 0; font-size: 1.05em; }
    .highlight { color: var(--naranja-estructural); font-weight: bold; }
    
    /* Enlaces del Sidebar */
    .link-ce { text-decoration: none; color: var(--azul-profundo); font-weight: bold; display: block; padding: 8px 0; border-bottom: 1px solid #ddd; }
    .link-ce:hover { color: var(--naranja-estructural); }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="titulo-principal">Análisis Rápido de Escaleras</h1>', unsafe_allow_html=True)
st.markdown("**Criterio Estructural** | Herramienta didáctica para idealizar, analizar y verificar rápidamente modelos de escaleras de un tramo.")

# ==========================================
# BARRA LATERAL: ENTRADA DE DATOS
# ==========================================
with st.sidebar:
    st.image("assets/IsotipoFClaroT.png", use_container_width=True)
    
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
    st.header("3. Cargas Gravitacionales (kN/m)")
    st.caption("Ingresa la carga distribuida vertical por unidad de longitud del elemento. La aplicación la transforma automáticamente a los ejes locales del elemento.")
    
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
    
    # ENLACES INSTITUCIONALES EN EL SIDEBAR
    st.markdown("---")
    # st.image("assets/IsotipoFClaroT.png", use_container_width=True)
    # st.markdown("Repositorio de Laboratorios Virtuales")
    st.markdown('<a href="https://rafacorreacolombia.github.io/Hormigon-armado/losas/escaleras.html" target="_blank" class="link-ce">📈 Presentación de la Clase</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://rafacorreacolombia.github.io/Hormigon-armado/" target="_blank" class="link-ce">🏠 Inicio del Repositorio</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://rafacorreacolombia.github.io/Hormigon-armado/vigas/deflexiones.html" target="_blank" class="link-ce">📉 Análisis de Deflexiones</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://rafacorreacolombia.github.io/Hormigon-armado/losas/losa1dir.html" target="_blank" class="link-ce">🏗️ Losas en Una Dirección</a>', unsafe_allow_html=True)
    st.markdown('<a href="https://rafacorreacolombia.github.io/Hormigon-armado/herramientas/traslapos.html" target="_blank" class="link-ce">🔗 Longitud de Traslapos</a>', unsafe_allow_html=True)


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
    
    # --- CANDADO 1: Conteo de reacciones mínimas para estabilidad ---
    if len(restricciones) < 3:
        st.error("""
        🚨 **Error de Estática: Estructura inestable (Mecanismo).** 
        
        Tienes menos de 3 reacciones en total. La escalera actúa como un cuerpo rígido sin suficiente restricción para mantenerse en equilibrio.
        * **Articulado + Libre:** La escalera gira como un péndulo.
        * **Rodillo + Rodillo:** Faltan restricciones para estabilizar la geometría.
        
        👉 **Solución:** Cambia los apoyos para asegurar al menos 3 restricciones (ej. usar un apoyo 'Empotrado', o un 'Articulado' junto a un 'Rodillo').
        """)
        st.stop()

    # Solución matricial (con captura de error residual)
    try:
        Desp, Reacciones = mr.resolver_sistema(K_sis, F_sis, restricciones)
        
        # --- CANDADO 2: Fugas numéricas (Mecanismos por geometría paralela) ---
        if np.max(np.abs(Desp)) > 5.0: # Si se deforma más de 5 m, es inestable
            st.error("🚨 **Error de Estática: Desplazamiento irreal detectado.** La estructura es inestable y se comporta como un mecanismo (fuerzas no controladas). Revisa tus apoyos.")
            st.stop()
            
    except np.linalg.LinAlgError:
        st.error("🚨 **Error de Estática:** La estructura es inestable (matriz singular). Cambia los apoyos a opciones más rígidas.")
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
        # Calcular componentes y resultantes nodales para cada nodo (i = 0, 3, 6)
        # GDL: Nodo 0 -> [0:ux, 1:uy, 2:rz], Nodo 1 -> [3:ux, 4:uy, 5:rz], Nodo 2 -> [6:ux, 7:uy, 8:rz]
        desplazamientos_detalle = []
        for idx, nodo_num in enumerate([1, 2, 3]):
            i = idx * 3
            u_horiz = Desp[i] * 1000     # mm
            v_vert = Desp[i+1] * 1000    # mm
            resultante = np.hypot(u_horiz, v_vert) # mm
            desplazamientos_detalle.append((nodo_num, resultante, v_vert, u_horiz))

        # Encontrar el nodo con mayor desplazamiento resultante
        nodo_critico, max_res, v_crit, u_crit = max(desplazamientos_detalle, key=lambda x: x[1])

        # Gráfica de la deformada
        fig_def = vi.graficar_deformada(nodos, elementos, Desp)
        st.plotly_chart(fig_def, use_container_width=True)
        
        # Caja de resultados detallada con HTML puro (sin LaTeX conflictivo)
        html_desp = f"""
        <div class="caja-resultados" style="margin-top: 15px;">
            <b>Desplazamiento Nodal Máximo (Nodo Crítico N{nodo_critico}):</b><br>
            • <b>Magnitud del desplazamiento (&delta;<sub>max</sub>):</b> <span class="highlight">{max_res:.2f} mm</span><br>
            • <b>Componente vertical (<i>v</i>):</b> {v_crit:.2f} mm &nbsp;|&nbsp; 
            • <b>Componente horizontal (<i>u</i>):</b> {u_crit:.2f} mm
            <p style="font-size: 0.85em; color: #64748b; margin: 5px 0 0 0;">
                <i>Nota: La resultante corresponde a la magnitud del vector de desplazamiento traslacional del nodo. Combina sus componentes horizontal y vertical: (&delta; = &radic;(<i>u</i><sup>2</sup> + <i>v</i><sup>2</sup>)).</i>
            </p>
        </div>
        """
        st.markdown(html_desp, unsafe_allow_html=True)
        
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
    st.write("Comprobación de la máxima demanda. *Asume acero fy = 420 MPa y distancia al centroide de 4 cm.*")
    
    # Encontrar máximos absolutos
    Mu_max = max(np.max(np.abs(M1)), np.max(np.abs(M2)))
    Vu_max = max(np.max(np.abs(V1)), np.max(np.abs(V2)))
    
    # Evaluar la tracción máxima
    Nu_traccion = max([0.0, np.max(N1), np.max(N2)])
    
    # Parámetros de Diseño
    d_m = h - 0.04 # Peralte efectivo en metros
    fy = 420 # MPa
    phi_f = 0.90
    phi_v = 0.75
    
    # Cortante del Concreto (NSR-10)
    Vc1 = 0.17 * np.sqrt(fc) * b * d_m * 1000 # en kN 
    Vc2 = 0.17 * np.sqrt(fc) * b * d_m * 1000 * (1 + (0.29 * (-Nu_traccion) / (b * h * 1000)))
    Vc2 = max(0.0, Vc2)
    phi_Vc = phi_v * min(Vc1, Vc2)
    
    # Acero de Flexión (Ecuación Cuadrática Exacta de rho)
    coef_A = 0.588235 * fy / fc
    coef_B = -1.0
    coef_C = (Mu_max) / (phi_f * b * d_m**2 * fy * 1000) 
    
    discriminante = coef_B**2 - 4 * coef_A * coef_C
    if discriminante < 0:
        texto_As = "¡Sección Insuficiente! Aumente el espesor (h)."
        As_req_cm2 = 0
    else:
        rho_req = (-coef_B - np.sqrt(discriminante)) / (2 * coef_A)
        As_req_cm2 = rho_req * b * d_m * 10000 
        texto_As = f"{As_req_cm2:.2f} cm²"
        
    As_min_cm2 = 0.0018 * b * h * 10000
    
    # RENDERIZADO DE DISEÑO (F-STRINGS PARA EVITAR FRANJAS GRISES)
    col_flex, col_cort = st.columns(2)
    
    with col_flex:
        html_flexion = f"""
        <div class="caja-resultados">
            <h4>📏 Diseño a Flexión</h4>
            <p><b>Demanda Crítica |M<sub>u</sub>|:</b> <span class="highlight">{Mu_max:.2f} kN·m</span></p>
            <p><b>A<sub>s</sub> requerido:</b> {texto_As}</p>
            <p><b>A<sub>s</sub> mínimo (NSR-10):</b> {As_min_cm2:.2f} cm²</p>
        </div>
        """
        st.markdown(html_flexion, unsafe_allow_html=True)
        
    with col_cort:
        if Vu_max <= phi_Vc:
            texto_chequeo = "✅ <b>Chequeo:</b> V<sub>u</sub> ≤ φV<sub>c</sub> (No requiere refuerzo transversal)"
        else:
            texto_chequeo = "❌ <b style='color:red;'>Chequeo:</b> V<sub>u</sub> > φV<sub>c</sub> (Requiere aumentar espesor o colocar estribos)"

        html_cortante = f"""
        <div class="caja-resultados">
            <h4>✂️ Diseño a Cortante</h4>
            <p><b>Demanda |V<sub>u</sub>|:</b> {Vu_max:.2f} kN &nbsp;|&nbsp; <b>Tracción |N<sub>u</sub>|:</b> {Nu_traccion:.2f} kN</p>
            <p><b>Capacidad φV<sub>c</sub>:</b> <span class="highlight">{phi_Vc:.2f} kN</span> <span style="font-size:0.85em; color:#666;">(mínimo entre EQ C.11-3 y C.11-8)</span></p>
            <p>{texto_chequeo}</p>
        </div>
        """
        st.markdown(html_cortante, unsafe_allow_html=True)

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

# ==========================================
# FOOTER INSTITUCIONAL CRITERIO ESTRUCTURAL
# ==========================================
st.markdown("---")
st.markdown(
    """
    <link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    <div style="text-align: center; color: #1A2530; padding: 10px 0;">
        <img src="https://raw.githubusercontent.com/rafacorreacolombia/Hormigon-armado/main/assets/IsotipoFClaroT.png" alt="Criterio Estructural" style="max-width: 180px; height: auto; margin-bottom: 10px;">
        <h4 style="margin:0;"><b>Ing. Rafael Antonio Correa Melano</b></h4>
        <div class="w3-xlarge w3-padding-16">
            <a href="https://www.instagram.com/rafacestructural" target="_blank" class="w3-hover-text-red w3-margin-right" style="text-decoration: none; color: inherit;"><i class="fa fa-instagram"></i></a>
            <a href="https://wa.me/573151600480" target="_blank" class="w3-hover-text-green w3-margin-right" style="text-decoration: none; color: inherit;"><i class="fa fa-whatsapp"></i></a>
            <a href="mailto:rafael.correa.ing@gmail.com" class="w3-hover-text-red" style="text-decoration: none; color: inherit;"><i class="fa fa-envelope-o"></i></a>
        </div>
        <p style="font-size: 0.9em; margin: 5px 0;">Ingeniero Civil • M.IE. <br> Universidad Industrial de Santander</p>
        <p style="font-size: 0.8em; color: #64748b; margin-top: 15px;">
            <b>Criterio Estructural</b><br>
            © 2026 Rafael Antonio Correa Melano. Todos los derechos reservados.<br>
            <span style="display: inline-block; margin-top: 5px; border: 1px solid #E67E22; color: #E67E22; padding: 2px 8px; border-radius: 4px; font-size: 0.9em;">
                Bucaramanga, Colombia 🇨🇴
            </span>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
