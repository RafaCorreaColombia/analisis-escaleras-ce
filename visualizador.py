import plotly.graph_objects as go
import numpy as np

# Colores de la marca Criterio Estructural
C_AZUL = "#1A2530"
C_NARANJA = "#E67E22"
C_GRIS = "#64748b"
C_GRIS_CLARO = "#F4F5F7"
C_AZUL_SUAVE = "rgba(26, 37, 48, 0.1)"
C_NARANJA_SUAVE = "rgba(230, 126, 34, 0.2)"

def obtener_limites_fijos(nodos):
    """
    Calcula una ventana de visualización fija con márgenes ajustados 
    para que la escalera se vea grande y mantenga la misma escala.
    """
    xs = [n[0] for n in nodos]
    ys = [n[1] for n in nodos]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    
    # Usamos la longitud en X como referencia (las escaleras suelen ser más largas que altas)
    longitud_x = max(x_max - x_min, 1.0)
    altura_y = max(y_max - y_min, 1.0)
    
    # Márgenes asimétricos: apretados a los lados, más espacio arriba/abajo para los diagramas
    margen_x = 0.10 * longitud_x
    margen_y = 0.20 * max(longitud_x, altura_y)
    
    rango_x = [x_min - margen_x, x_max + margen_x]
    rango_y = [y_min - margen_y, y_max + margen_y]
    
    return rango_x, rango_y, longitud_x

def graficar_modelo_basico(nodos, elementos, titulo="Geometría del Modelo", apoyos=["Libre", "Libre", "Libre"]):
    fig = go.Figure()
    rango_x, rango_y, _ = obtener_limites_fijos(nodos)
    
    # Dibujar elementos
    for (n1, n2) in elementos:
        x_coords = [nodos[n1][0], nodos[n2][0]]
        y_coords = [nodos[n1][1], nodos[n2][1]]
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords, 
            mode='lines', line=dict(color=C_AZUL, width=5), hoverinfo='none', showlegend=False
        ))
        
    # Dibujar Símbolos de Apoyo
    for i, apoyo in enumerate(apoyos):
        if apoyo != "Libre":
            x, y = nodos[i]
            simbolo = 'square' if apoyo == "Empotrado" else ('triangle-up' if apoyo == "Articulado" else 'circle-cross')
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode='markers', 
                marker=dict(symbol=simbolo, size=22, color=C_GRIS), 
                hovertext=f"Apoyo {apoyo}", hoverinfo="text", showlegend=False
            ))
            
    # Dibujar nodos
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
        title=dict(text=titulo, font=dict(color=C_AZUL, size=18)), plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False, range=rango_x, scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False, range=rango_y),
        margin=dict(l=20, r=20, t=50, b=20), height=400
    )
    return fig

def graficar_diagrama(nodos, elementos, x_locales, valores, titulo, color_linea, color_relleno, invertir_signo=False):
    fig = go.Figure()
    rango_x, rango_y, rango_espacial = obtener_limites_fijos(nodos)
    
    max_val = max([np.max(np.abs(v)) for v in valores if len(v) > 0] + [1e-6])
    
    # Reducimos el factor a 0.15 para que el diagrama no se salga del nuevo margen en Y
    factor_escala = (0.15 * rango_espacial) / max_val
    
    # Dibujar línea base
    for (n1, n2) in elementos:
        fig.add_trace(go.Scatter(
            x=[nodos[n1][0], nodos[n2][0]], y=[nodos[n1][1], nodos[n2][1]], 
            mode='lines', line=dict(color=C_AZUL, width=3), hoverinfo='none', showlegend=False
        ))

    # Dibujar diagramas proyectados
    for i, (n1, n2) in enumerate(elementos):
        x0, y0 = nodos[n1]
        x1, y1 = nodos[n2]
        
        L = np.hypot(x1 - x0, y1 - y0)
        if L == 0: continue
        c = (x1 - x0) / L
        s = (y1 - y0) / L
        
        xl = x_locales[i]
        val = -valores[i] if invertir_signo else valores[i]
            
        xd = x0 + xl * c - (val * factor_escala) * s
        yd = y0 + xl * s + (val * factor_escala) * c
        
        x_poligono = np.concatenate([xd, [x1, x0]])
        y_poligono = np.concatenate([yd, [y1, y0]])
        
        textos_hover = [f"Pos: {xl[j]:.2f}m<br>Valor: {valores[i][j]:.2f}" for j in range(len(xl))]
        
        fig.add_trace(go.Scatter(
            x=x_poligono, y=y_poligono, fill='toself', fillcolor=color_relleno, 
            mode='lines', line=dict(color=color_linea, width=2),
            hoverinfo='text', hovertext=textos_hover + ["", ""], name=f"Tramo {i+1}"
        ))
        
        # Anotar valores críticos
        idx_criticos = set([0, len(xl)-1, np.argmax(valores[i]), np.argmin(valores[i])])
        for idx in idx_criticos:
            v_real = valores[i][idx]
            if abs(v_real) > 0.1: 
                fig.add_annotation(
                    x=xd[idx], y=yd[idx], text=f"<b>{v_real:.1f}</b>", showarrow=False,
                    font=dict(size=11, color=color_linea), bgcolor="rgba(255,255,255,0.8)", borderpad=2
                )

    fig.update_layout(
        title=dict(text=titulo, font=dict(color=C_AZUL, size=18)), plot_bgcolor='white',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=rango_x, scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=rango_y),
        margin=dict(l=10, r=10, t=40, b=10), height=350, showlegend=False
    )
    return fig

def graficar_deformada(nodos, elementos, desplazamientos_globales):
    fig = go.Figure()
    rango_x, rango_y, rango_espacial = obtener_limites_fijos(nodos)
    
    desp_max = max(np.max(np.abs(desplazamientos_globales)), 1e-9)
    # 10% para que la deformada sea visible pero sutil
    factor_amplificacion = (rango_espacial * 0.10) / desp_max 
    
    # Estructura Original
    for (n1, n2) in elementos:
        fig.add_trace(go.Scatter(
            x=[nodos[n1][0], nodos[n2][0]], y=[nodos[n1][1], nodos[n2][1]], 
            mode='lines', line=dict(color=C_GRIS, width=2, dash='dash'), hoverinfo='none', name="Original"
        ))
        
    # Calcular nodos deformados
    nodos_def = []
    for i, (x, y) in enumerate(nodos):
        ux = desplazamientos_globales[i*3]
        uy = desplazamientos_globales[i*3 + 1]
        nodos_def.append([x + ux * factor_amplificacion, y + uy * factor_amplificacion])
        
    # Estructura Deformada
    for (n1, n2) in elementos:
        fig.add_trace(go.Scatter(
            x=[nodos_def[n1][0], nodos_def[n2][0]], y=[nodos_def[n1][1], nodos_def[n2][1]], 
            mode='lines+markers', line=dict(color=C_NARANJA, width=4),
            marker=dict(size=8, color=C_AZUL), hoverinfo='text', 
            hovertext=f"Elemento de N{n1+1} a N{n2+1} (Deformado)", name="Deformada", showlegend=False
        ))

    fig.update_layout(
        title=dict(text=f"Deformada (Auto-amplificada {factor_amplificacion:.0f}x)", font=dict(color=C_AZUL, size=18)),
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False, range=rango_x, scaleanchor="y", scaleratio=1),
        yaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False, range=rango_y),
        margin=dict(l=20, r=20, t=50, b=20), height=350, showlegend=False
    )
    return fig

if __name__ == "__main__":
    print("Iniciando prueba gráfica con límites asimétricos ajustados...")
