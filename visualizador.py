import plotly.graph_objects as go
import numpy as np

# Colores de la marca Criterio Estructural
C_AZUL = "#1A2530"
C_NARANJA = "#E67E22"
C_GRIS = "#64748b"
C_GRIS_CLARO = "#F4F5F7"
C_AZUL_SUAVE = "rgba(26, 37, 48, 0.1)"
C_NARANJA_SUAVE = "rgba(230, 126, 34, 0.2)"

def graficar_modelo_basico(nodos, elementos, titulo="Geometría del Modelo"):
    """
    Dibuja los nodos y las líneas que representan los elementos estructurales.
    nodos: lista de coordenadas [[x1, y1], [x2, y2], [x3, y3]]
    elementos: lista de tuplas con los índices de los nodos [(0, 1), (1, 2)]
    """
    fig = go.Figure()
    
    # Dibujar elementos (líneas gruesas)
    for (n1, n2) in elementos:
        x_coords = [nodos[n1][0], nodos[n2][0]]
        y_coords = [nodos[n1][1], nodos[n2][1]]
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords, 
            mode='lines', line=dict(color=C_AZUL, width=5),
            hoverinfo='none', showlegend=False
        ))
        
    # Dibujar nodos (puntos grandes)
    nx = [n[0] for n in nodos]
    ny = [n[1] for n in nodos]
    text_nodos = [f"Nodo {i+1}<br>({x:.2f}, {y:.2f})" for i, (x, y) in enumerate(nodos)]
    
    fig.add_trace(go.Scatter(
        x=nx, y=ny, mode='markers+text',
        marker=dict(size=12, color=C_NARANJA, line=dict(width=2, color='white')),
        text=[f"N{i+1}" for i in range(len(nodos))],
        textposition="top center",
        textfont=dict(color=C_AZUL, size=14, family="Arial Black"),
        hovertext=text_nodos, hoverinfo="text", showlegend=False
    ))
    
    fig.update_layout(
        title=dict(text=titulo, font=dict(color=C_AZUL, size=18)),
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False),
        margin=dict(l=20, r=20, t=50, b=20),
        height=400
    )
    return fig

def graficar_diagrama(nodos, elementos, x_locales, valores, titulo, color_linea, color_relleno, invertir_signo=False):
    """
    Grafica diagramas (N, V, M) perpendiculares al eje de cada elemento.
    
    x_locales: lista de arrays (uno por elemento) con las distancias locales (0 a L)
    valores: lista de arrays (uno por elemento) con las magnitudes del diagrama
    invertir_signo: Útil para diagramas de Momento (dibujar tracciones abajo)
    """
    fig = go.Figure()
    
    # 1. Encontrar el valor máximo absoluto para calcular un factor de escala visual
    max_val = max([np.max(np.abs(v)) for v in valores if len(v) > 0] + [1e-6])
    
    # Calcular tamaño de la pantalla (L mayor del proyecto) para escalar el diagrama al 15% del tamaño total
    xs = [n[0] for n in nodos]
    ys = [n[1] for n in nodos]
    rango_espacial = max(max(xs)-min(xs), max(ys)-min(ys), 1.0)
    factor_escala = (0.15 * rango_espacial) / max_val
    
    # 2. Dibujar la línea base de la escalera
    for (n1, n2) in elementos:
        fig.add_trace(go.Scatter(
            x=[nodos[n1][0], nodos[n2][0]], y=[nodos[n1][1], nodos[n2][1]], 
            mode='lines', line=dict(color=C_AZUL, width=3), hoverinfo='none', showlegend=False
        ))

    # 3. Dibujar los diagramas proyectados
    for i, (n1, n2) in enumerate(elementos):
        x0, y0 = nodos[n1]
        x1, y1 = nodos[n2]
        
        L = np.hypot(x1 - x0, y1 - y0)
        if L == 0: continue
        c = (x1 - x0) / L
        s = (y1 - y0) / L
        
        # Extraer datos locales
        xl = x_locales[i]
        val = valores[i]
        
        if invertir_signo:
            val = -val
            
        # Calcular coordenadas globales del diagrama (perpendiculares al eje)
        # Vector director: (c, s). Vector normal perpendicular: (-s, c)
        xd = x0 + xl * c - (val * factor_escala) * s
        yd = y0 + xl * s + (val * factor_escala) * c
        
        # Para hacer el polígono relleno (fill), cerramos la forma volviendo a la línea base
        x_poligono = np.concatenate([xd, [x1, x0]])
        y_poligono = np.concatenate([yd, [y1, y0]])
        
        # Textos para el tooltip (hover) devolviendo el signo original a la pantalla
        textos_hover = [f"Pos: {xl[j]:.2f}m<br>Valor: {valores[i][j]:.2f}" for j in range(len(xl))]
        
        fig.add_trace(go.Scatter(
            x=x_poligono, y=y_poligono, 
            fill='toself', fillcolor=color_relleno, 
            mode='lines', line=dict(color=color_linea, width=2),
            hoverinfo='text', hovertext=textos_hover + ["", ""],
            name=f"Tramo {i+1}"
        ))

    fig.update_layout(
        title=dict(text=titulo, font=dict(color=C_AZUL, size=18)),
        plot_bgcolor='white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10, r=10, t=40, b=10),
        height=350,
        showlegend=False
    )
    return fig

def graficar_deformada(nodos, elementos, desplazamientos_globales, factor_amplificacion=100):
    """
    Dibuja la estructura original (gris, tenue) y la estructura deformada (naranja, gruesa).
    """
    fig = go.Figure()
    
    # Estructura Original
    for (n1, n2) in elementos:
        fig.add_trace(go.Scatter(
            x=[nodos[n1][0], nodos[n2][0]], y=[nodos[n1][1], nodos[n2][1]], 
            mode='lines', line=dict(color=C_GRIS, width=2, dash='dash'), 
            hoverinfo='none', name="Original"
        ))
        
    # Calcular nodos deformados
    nodos_def = []
    for i, (x, y) in enumerate(nodos):
        ux = desplazamientos_globales[i*3]
        uy = desplazamientos_globales[i*3 + 1]
        nodos_def.append([
            x + ux * factor_amplificacion, 
            y + uy * factor_amplificacion
        ])
        
    # Estructura Deformada
    for (n1, n2) in elementos:
        fig.add_trace(go.Scatter(
            x=[nodos_def[n1][0], nodos_def[n2][0]], y=[nodos_def[n1][1], nodos_def[n2][1]], 
            mode='lines+markers', line=dict(color=C_NARANJA, width=4),
            marker=dict(size=8, color=C_AZUL),
            hoverinfo='text', hovertext=f"Elemento de N{n1+1} a N{n2+1} (Deformado)",
            name="Deformada"
        ))

    fig.update_layout(
        title=dict(text=f"Deformada (Amplificada {factor_amplificacion}x)", font=dict(color=C_AZUL, size=18)),
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False),
        margin=dict(l=20, r=20, t=50, b=20),
        height=350,
        showlegend=False
    )
    return fig

# ==========================================
# PRUEBA RÁPIDA (EJECUCIÓN DIRECTA)
# ==========================================
if __name__ == "__main__":
    # Prueba del visualizador con datos ficticios simulando una escalera
    print("Iniciando prueba gráfica...")
    
    nodos = [[0, 0], [3, 0], [5.8, 1.68]]
    elementos = [(0, 1), (1, 2)]
    
    # Simulamos arrays de estática del módulo cargas.py
    # Elemento 1 (L=3m)
    x1 = np.linspace(0, 3, 50)
    M1 = -15 + 10*x1 - 3*x1**2 # Parabólico
    
    # Elemento 2 (L=3.28m)
    x2 = np.linspace(0, 3.28, 50)
    M2 = 12 - 5*x2 - 1.5*x2**2 # Parabólico
    
    x_locales = [x1, x2]
    valores_M = [M1, M2]
    
    # Graficar y mostrar en el navegador
    fig_geom = graficar_modelo_basico(nodos, elementos)
    fig_geom.show()
    
    # Nota: invertir_signo=True para que el momento positivo se dibuje hacia abajo (tracciones)
    fig_momento = graficar_diagrama(
        nodos, elementos, x_locales, valores_M, 
        titulo="Diagrama de Momento (kN·m)", 
        color_linea=C_NARANJA, color_relleno=C_NARANJA_SUAVE, 
        invertir_signo=True
    )
    fig_momento.show()
    
    print("✅ PRUEBA EXITOSA: Si se abrieron las pestañas en tu navegador con gráficas interactivas, el visualizador está listo.")
