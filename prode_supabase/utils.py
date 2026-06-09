from flags import FLAGS


def get_flag_url(equipo: str) -> str:
    """Devuelve la URL de la bandera o cadena vacía si no existe."""
    return FLAGS.get(equipo, "")


def equipo_con_bandera_html(equipo: str, tamaño: int = 28) -> str:
    """
    Devuelve un string HTML con la bandera circular y el nombre del equipo,
    listo para usar con st.markdown(..., unsafe_allow_html=True).
    """
    url = get_flag_url(equipo)
    if url:
        return (
            f'<img src="{url}" width="{tamaño}" height="{tamaño}" '
            f'style="border-radius:50%; vertical-align:middle; margin-right:6px;">'
            f'<span style="vertical-align:middle;">{equipo}</span>'
        )
    return equipo


def partido_html(local: str, visitante: str, resultado: str = "") -> str:
    """
    Devuelve un bloque HTML con el enfrentamiento completo.
    El resultado usa el formato 1/X/2.
    """
    bandera_local     = get_flag_url(local)
    bandera_visitante = get_flag_url(visitante)

    img_local = (
        f'<img src="{bandera_local}" width="32" height="32" '
        f'style="border-radius:50%; vertical-align:middle; margin-right:8px;">'
        if bandera_local else ""
    )
    img_visitante = (
        f'<img src="{bandera_visitante}" width="32" height="32" '
        f'style="border-radius:50%; vertical-align:middle; margin-left:8px;">'
        if bandera_visitante else ""
    )

    labels = {"1": f"Gana {local}", "X": "Empate", "2": f"Gana {visitante}"}
    if resultado:
        label_res = labels.get(resultado, resultado)
        centro = f'<strong style="font-size:1.1em; margin:0 16px;">{label_res}</strong>'
    else:
        centro = '<span style="margin:0 16px; color:gray;">VS</span>'

    return (
        f'<div style="display:flex; align-items:center; justify-content:center;">'
        f'  {img_local}<span>{local}</span>'
        f'  {centro}'
        f'  <span>{visitante}</span>{img_visitante}'
        f'</div>'
    )
