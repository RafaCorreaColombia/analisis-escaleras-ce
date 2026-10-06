import numpy as np

def descomponer_carga_gravedad(W_vertical, c, s, es_proyeccion_horizontal=False):
    """
    Toma una carga gravitacional global (W_vertical en kN/m, positiva hacia abajo)
    y la descompone en los ejes locales del elemento inclinado.
    
    Se eliminó la reducción por proyección horizontal para que W_vertical actúe 
    por metro de longitud inclinada, coincidiendo con la dirección "Gravity" de SAP2000.
    """
    # W_vertical se asume repartido sobre la longitud real del elemento
    W_real = W_vertical

    # La gravedad actúa en dirección -Y global.
    # Proyección en el eje local X (Axial) y local Y (Transversal)
    w_x = -W_real * s
    w_y = -W_real * c
    
    return w_x, w_y

def calcular_FEM_local(w_x, w_y, L):
    F_fem_local = np.zeros(6)
    F_fem_local[0] = -w_x * L / 2.0
    F_fem_local[3] = -w_x * L / 2.0
    F_fem_local[1] = -w_y * L / 2.0
    F_fem_local[4] = -w_y * L / 2.0
    F_fem_local[2] = -w_y * (L**2) / 12.0
    F_fem_local[5] =  w_y * (L**2) / 12.0
    return F_fem_local

def vector_cargas_equivalentes_global(F_fem_local, T):
    F_fem_global = T.T @ F_fem_local
    return -F_fem_global

def fuerzas_finales_extremos(k_local, T, D_elem_global, F_fem_local):
    F_por_desplazamiento = k_local @ T @ D_elem_global
    return F_por_desplazamiento + F_fem_local

def generar_datos_diagramas(F_extremos_local, w_x, w_y, L, num_puntos=50):
    x = np.linspace(0, L, num_puntos)
    Fx1 = F_extremos_local[0]
    Fy1 = F_extremos_local[1]
    M1  = F_extremos_local[2]
    
    N = -Fx1 - w_x * x
    V = Fy1 + w_y * x
    M = -M1 + Fy1 * x + w_y * (x**2) / 2.0
    return x, N, V, M
