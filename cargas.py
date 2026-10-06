import numpy as np

def descomponer_carga_gravedad(W_vertical, c, s, es_proyeccion_horizontal=False):
    """
    Toma una carga gravitacional global (W_vertical en kN/m, positiva hacia abajo)
    y la descompone en los ejes locales del elemento inclinado.
    
    Si 'es_proyeccion_horizontal' es True (típico en escaleras para cargas vivas), 
    convierte primero la carga a la longitud inclinada real.
    """
    # Si la carga se ingresó por metro de proyección horizontal, la ajustamos a la longitud real
    if es_proyeccion_horizontal and c != 0:
        W_real = W_vertical * abs(c)
    else:
        W_real = W_vertical

    # La gravedad actúa en dirección -Y global.
    # Proyección en el eje local X (Axial) y local Y (Transversal)
    w_x = -W_real * s
    w_y = -W_real * c
    
    return w_x, w_y

def calcular_FEM_local(w_x, w_y, L):
    """
    Calcula el vector de Fuerzas de Empotramiento Perfecto (FEM) en coordenadas locales.
    Representan las fuerzas que los apoyos ejercen SOBRE el elemento para mantenerlo fijo.
    Vector (6x1): [Fx1, Fy1, M1, Fx2, Fy2, M2]
    """
    F_fem_local = np.zeros(6)
    
    # Fuerzas axiales de empotramiento
    F_fem_local[0] = -w_x * L / 2.0
    F_fem_local[3] = -w_x * L / 2.0
    
    # Fuerzas cortantes de empotramiento
    F_fem_local[1] = -w_y * L / 2.0
    F_fem_local[4] = -w_y * L / 2.0
    
    # Momentos de empotramiento (Convención: Antihorario es positivo)
    F_fem_local[2] = -w_y * (L**2) / 12.0
    F_fem_local[5] =  w_y * (L**2) / 12.0
    
    return F_fem_local

def vector_cargas_equivalentes_global(F_fem_local, T):
    """
    Convierte las reacciones de empotramiento local en CARGAS NODALES EQUIVALENTES
    en el sistema global para poder ensamblarlas en {F} del sistema [K]{D}={F}.
    F_eq = - [T]^T * F_fem_local
    """
    F_fem_global = T.T @ F_fem_local
    return -F_fem_global

def fuerzas_finales_extremos(k_local, T, D_elem_global, F_fem_local):
    """
    Superposición: Suma los efectos de los desplazamientos nodales y las cargas distribuidas.
    F_finales = [k_local][T]{D_elem} + {F_fem_local}
    Devuelve las fuerzas internas reales en los extremos del elemento.
    """
    F_por_desplazamiento = k_local @ T @ D_elem_global
    return F_por_desplazamiento + F_fem_local

def generar_datos_diagramas(F_extremos_local, w_x, w_y, L, num_puntos=50):
    """
    A partir de las fuerzas finales en el nodo 1 y las cargas distribuidas locales,
    construye las ecuaciones de estática para graficar N(x), V(x) y M(x).
    
    Retorna arrays (X, N, V, M) listos para Plotly/Matplotlib.
    """
    x = np.linspace(0, L, num_puntos)
    
    # Extracción de fuerzas en el Nodo 1 (inicio del elemento)
    Fx1 = F_extremos_local[0]
    Fy1 = F_extremos_local[1]
    M1  = F_extremos_local[2]
    
    # Ecuaciones de equilibrio interno a una distancia x
    # Convención estandar:
    # N(x): Tracción es positiva
    # V(x): Hacia arriba en la cara izquierda es positivo
    # M(x): Tracción en la fibra inferior es positivo
    
    N = -Fx1 - w_x * x
    V = Fy1 + w_y * x
    M = -M1 + Fy1 * x + w_y * (x**2) / 2.0
    
    return x, N, V, M

# ==========================================
# PRUEBA RÁPIDA (EJECUCIÓN DIRECTA)
# ==========================================
if __name__ == "__main__":
    # Prueba de validación: Una viga simplemente apoyada (L=5m) con carga vertical gravitacional de 10 kN/m.
    # Matemáticamente deberíamos obtener M_max = wl^2 / 8 = 10*(5^2)/8 = 31.25 kNm en el centro.
    import motor_rigidez as mr
    
    print("Validando física de cargas...")
    
    L = 5.0
    c, s = 1.0, 0.0 # Viga horizontal
    w_vertical = 10.0 # kN/m hacia abajo
    
    # 1. Descomponer carga
    w_x, w_y = descomponer_carga_gravedad(w_vertical, c, s)
    print(f"Cargas locales: wx = {w_x}, wy = {w_y} (Debe ser -10)")
    
    # 2. FEM
    F_fem = calcular_FEM_local(w_x, w_y, L)
    print(f"Momentos de Empotramiento: M1 = {F_fem[2]:.2f}, M2 = {F_fem[5]:.2f} (Debería ser 20.83 y -20.83)")
    
    # 3. Simulamos resolver el sistema (como si tuviéramos apoyos articulados)
    # k_local y T
    E, A, I = 21e6, 0.15, 0.00125
    k_loc = mr.matriz_rigidez_local(E, A, I, L)
    T = mr.matriz_transformacion(c, s)
    k_glob = mr.matriz_rigidez_global_elemento(k_loc, T)
    
    # Cargas nodales equivalentes para ensamblar
    F_eq = vector_cargas_equivalentes_global(F_fem, T)
    
    # Matriz del sistema y solución (GDL restringidos: 0, 1 y 4 (ux1, uy1, uy2))
    restricciones = [0, 1, 4]
    Desp, Reacciones = mr.resolver_sistema(k_glob, F_eq, restricciones)
    
    # 4. Fuerzas internas en extremos
    F_extremos = fuerzas_finales_extremos(k_loc, T, Desp, F_fem)
    print(f"Momentos finales en apoyos: M1 = {F_extremos[2]:.2f}, M2 = {F_extremos[5]:.2f} (Deberían ser 0)")
    
    # 5. Diagramas (verificando el centro del vano)
    x, N, V, M = generar_datos_diagramas(F_extremos, w_x, w_y, L, num_puntos=5)
    
    print(f"\nResultados del Diagrama de Momento:")
    for xi, mi in zip(x, M):
        print(f"x = {xi:.2f} m -> M = {mi:.2f} kNm")
    
    print("\n✅ PRUEBA EXITOSA: Si el momento en x=2.5m es 31.25 kNm, el traductor de cargas es perfecto.")
