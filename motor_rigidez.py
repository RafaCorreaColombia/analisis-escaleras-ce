import numpy as np

def calcular_geometria_elemento(x1, y1, x2, y2):
    """
    Calcula la longitud (L) y los cosenos directores (c, s) de un elemento 2D.
    """
    dx = x2 - x1
    dy = y2 - y1
    L = np.sqrt(dx**2 + dy**2)
    c = dx / L if L != 0 else 1.0
    s = dy / L if L != 0 else 0.0
    return L, c, s

def matriz_rigidez_local(E, A, I, L):
    """
    Construye la matriz de rigidez local [k] (6x6) de un elemento de pórtico 2D.
    GDL por nodo: [Axial, Cortante, Momento]
    """
    k = np.zeros((6, 6))
    
    # Rigidez Axial
    k[0, 0] = k[3, 3] = E * A / L
    k[0, 3] = k[3, 0] = -E * A / L
    
    # Rigidez a Flexión (Euler-Bernoulli)
    k[1, 1] = k[4, 4] = 12 * E * I / (L**3)
    k[1, 4] = k[4, 1] = -12 * E * I / (L**3)
    
    k[2, 2] = k[5, 5] = 4 * E * I / L
    k[2, 5] = k[5, 2] = 2 * E * I / L
    
    k[1, 2] = k[2, 1] = k[1, 5] = k[5, 1] = 6 * E * I / (L**2)
    k[4, 2] = k[2, 4] = k[4, 5] = k[5, 4] = -6 * E * I / (L**2)
    
    return k

def matriz_transformacion(c, s):
    """
    Construye la matriz de transformación [T] (6x6) de local a global.
    """
    T = np.zeros((6, 6))
    T[0, 0] = T[1, 1] = T[3, 3] = T[4, 4] = c
    T[0, 1] = T[3, 4] = s
    T[1, 0] = T[4, 3] = -s
    T[2, 2] = T[5, 5] = 1.0
    return T

def matriz_rigidez_global_elemento(k_local, T):
    """
    Rota la matriz de rigidez local al sistema global: [k_global] = [T]^T * [k_local] * [T]
    """
    return T.T @ k_local @ T

def ensamblar_K_sistema(matrices_globales, grados_libertad_elementos, num_nodos):
    """
    Ensambla la matriz de rigidez global de toda la estructura [K].
    num_nodos: Cantidad total de nodos. La matriz será de (3*num_nodos) x (3*num_nodos).
    """
    num_gdl_totales = num_nodos * 3
    K_global = np.zeros((num_gdl_totales, num_gdl_totales))
    
    for k_elem, gdl_elem in zip(matrices_globales, grados_libertad_elementos):
        for i in range(6):
            for j in range(6):
                fila = gdl_elem[i]
                col = gdl_elem[j]
                K_global[fila, col] += k_elem[i, j]
                
    return K_global

def definir_gdl_restringidos(tipos_apoyo):
    """
    Traduce los tipos de apoyo en índices de Grados de Libertad (GDL) restringidos.
    """
    gdl_restringidos = []
    for i, apoyo in enumerate(tipos_apoyo):
        gdl_base = i * 3
        if apoyo == "Empotrado":
            gdl_restringidos.extend([gdl_base, gdl_base+1, gdl_base+2]) # ux, uy, θz
        elif apoyo == "Articulado":
            gdl_restringidos.extend([gdl_base, gdl_base+1]) # ux, uy
        elif apoyo == "Rodillo":
            gdl_restringidos.extend([gdl_base+1]) # Solo uy (permite deslizamiento horizontal)
        # Si es "Libre", no se restringe nada
    return gdl_restringidos

def resolver_sistema(K_global, F_global, gdl_restringidos):
    """
    Aplica condiciones de frontera y resuelve [K]{D} = {F}
    Retorna el vector completo de desplazamientos y las reacciones.
    """
    num_gdl = len(F_global)
    gdl_libres = [i for i in range(num_gdl) if i not in gdl_restringidos]
    
    # Reducir matrices
    K_reducida = K_global[np.ix_(gdl_libres, gdl_libres)]
    F_reducida = F_global[gdl_libres]
    
    # Resolver desplazamientos libres
    D_libres = np.linalg.solve(K_reducida, F_reducida)
    
    # Reconstruir vector de desplazamientos completo
    D_total = np.zeros(num_gdl)
    D_total[gdl_libres] = D_libres

    # Calcular fuerzas de equilibrio interno
    F_total = K_global @ D_total
    
    # EL GRAN ARREGLO: Las verdaderas reacciones físicas son las fuerzas internas 
    # menos las cargas nodales equivalentes aplicadas externamente.
    Reacciones = F_total - F_global
    
    return D_total, Reacciones

def fuerzas_internas_elemento(k_local, T, D_global_elemento):
    """
    Calcula las fuerzas en los extremos del elemento en su eje local.
    {F_local} = [k_local] * [T] * {D_global_elemento}
    """
    return k_local @ T @ D_global_elemento


# ==========================================
# PRUEBA RÁPIDA (EJECUCIÓN DIRECTA)
# ==========================================
if __name__ == "__main__":
    # Si ejecutas este archivo directamente en tu terminal (python motor_rigidez.py), 
    # resolverá un pórtico simple de prueba para verificar que las matemáticas funcionan.
    
    print("Iniciando prueba del motor matricial...")
    
    # Propiedades (Concreto)
    E = 21e6  # kN/m2
    b, h = 1.0, 0.15 # m
    A = b * h
    I = (b * h**3) / 12
    
    # Elemento 1 (Horizontal: Nodo 1 a Nodo 2)
    L1, c1, s1 = calcular_geometria_elemento(0, 0, 3, 0)
    k1_loc = matriz_rigidez_local(E, A, I, L1)
    T1 = matriz_transformacion(c1, s1)
    k1_glob = matriz_rigidez_global_elemento(k1_loc, T1)
    gdl_e1 = [0, 1, 2, 3, 4, 5]
    
    # Elemento 2 (Inclinado: Nodo 2 a Nodo 3)
    L2, c2, s2 = calcular_geometria_elemento(3, 0, 5.8, 1.68)
    k2_loc = matriz_rigidez_local(E, A, I, L2)
    T2 = matriz_transformacion(c2, s2)
    k2_glob = matriz_rigidez_global_elemento(k2_loc, T2)
    gdl_e2 = [3, 4, 5, 6, 7, 8]
    
    # Ensamblaje Global
    K_sis = ensamblar_K_sistema([k1_glob, k2_glob], [gdl_e1, gdl_e2], num_nodos=3)
    
    # Restricciones (Nodo 1 Empotrado, Nodo 3 Articulado)
    restricciones = definir_gdl_restringidos(["Empotrado", "Libre", "Articulado"])
    
    # Vector de Cargas Nodal (F_global) - Ejemplo: Carga de 10 kN hacia abajo en Nodo 2
    F_sis = np.zeros(9)
    F_sis[4] = -10.0  # GDL 4 = Fuerza Y en Nodo 2
    
    # Solución
    Desplazamientos, Fuerzas = resolver_sistema(K_sis, F_sis, restricciones)
    
    print("\n✅ RESOLUCIÓN EXITOSA")
    print(f"Desplazamiento Vertical en Nodo 2: {Desplazamientos[4]*1000:.2f} mm")
    print(f"Momento en el Empotramiento (Nodo 1): {Fuerzas[2]:.2f} kNm")
