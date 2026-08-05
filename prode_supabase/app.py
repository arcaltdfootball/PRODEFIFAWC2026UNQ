import streamlit as st

st.set_page_config(
    page_title="PRODE FUTBOL ARGENTINO 2026",
    page_icon="icon2026fwc.png",
    layout="wide"
)

# Imagen de fondo cargada desde archivo (ya no va embebida en base64 en el código).
# Para cambiar el fondo: subí al repositorio una imagen con el mismo nombre
# "fondo.png" (reemplazando el archivo actual) y listo, no hace falta tocar el código.
import base64

BG_IMAGE_PATH = "fondo.png"
try:
    with open(BG_IMAGE_PATH, "rb") as _f:
        BG_IMAGE_BASE64 = base64.b64encode(_f.read()).decode()
except FileNotFoundError:
    BG_IMAGE_BASE64 = ""
# Logo cargado desde archivo (mismo patrón que el fondo) (cabecera de la tarjeta del pozo)
LOGO_PATH = "LOGO.png"
try:
    with open(LOGO_PATH, "rb") as _f:
        LOGO_BASE64 = base64.b64encode(_f.read()).decode()
except FileNotFoundError:
    LOGO_BASE64 = ""

st.markdown(
    "<style>"
    ".stApp {"
    "background-image: url('data:image/png;base64," + BG_IMAGE_BASE64 + "');"
    "background-size: cover;"
    "background-position: center;"
    "background-repeat: no-repeat;"
    "background-attachment: fixed;"
    "}"
    "</style>",
    unsafe_allow_html=True
)

st.title("PRODE FUTBOL ARGENTINO 2026")

st.info("Despliegue el menú lateral.")

# ── AVISOS IMPORTANTES ──────────────────────────────────────────────────────
# 👇 Editá esta lista para publicar avisos a los jugadores.
# Cada elemento de la lista es un aviso distinto (podés agregar o quitar los que quieras).
AVISOS_IMPORTANTES = [
    "En la Boleta Digital de AGOSTO se juegan las fechas: 3 / 4 / 5 / 6 / 7.",
    "FECHA 5 (Cinco) SE JUEGA FECHA EXTRAORDINARIA con MARCADOR EXACTO. Sistema de puntaje: 1 punto por acertar el resultado (Local / Empate / Visitante) · 3 puntos en total si acertás el resultado exacto.",
]

if AVISOS_IMPORTANTES:
    avisos_html = "".join(
        f'<div class="aviso-item">{aviso}</div>' for aviso in AVISOS_IMPORTANTES
    )
    aviso_box_html = (
        '<div class="aviso-wrapper">'
        '<div class="aviso-card">'
        '<div class="aviso-titulo">⚠️ Aviso Importante</div>'
        f'{avisos_html}'
        '</div>'
        '</div>'
    )
    st.markdown(
        """
        <style>
        .aviso-wrapper {
            max-width: 560px;
            margin: 0 auto 24px;
        }
        .aviso-card {
            background: rgba(120,20,20,0.35);
            border: 1px solid rgba(255,90,90,0.45);
            border-radius: 18px;
            padding: 18px 22px;
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            box-shadow: 0 4px 20px rgba(255,60,60,0.10);
        }
        .aviso-titulo {
            font-family: 'Inter', sans-serif;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: #FF6B6B;
            text-transform: uppercase;
            margin-bottom: 10px;
            text-align: center;
        }
        .aviso-item {
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            color: rgba(255,255,255,0.85);
            line-height: 1.5;
            padding: 4px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(aviso_box_html, unsafe_allow_html=True)

# ── CARD DE POZO Y GANADORES ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;600;700&display=swap');

.pozo-wrapper {
    max-width: 560px;
    margin: 32px auto 24px;
}
.pozo-card {
    background: rgba(10,15,35,0.82);
    border: 1px solid rgba(255,215,0,0.35);
    border-radius: 24px;
    padding: 32px 28px 28px;
    box-shadow: 0 8px 40px rgba(255,215,0,0.12), 0 2px 16px rgba(0,0,0,0.5);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
}
.pozo-logo-header {
    display: flex;
    justify-content: center;
    margin-bottom: 18px;
}
.pozo-logo-header img {
    max-width: 200px;
    width: 100%;
    height: auto;
    filter: drop-shadow(0 4px 18px rgba(0,0,0,0.6));
}
.pozo-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: rgba(255,215,0,0.65);
    text-align: center;
    margin-bottom: 6px;
}
.pozo-monto {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(3rem, 10vw, 5.5rem);
    line-height: 1;
    text-align: center;
    color: #FFD700;
    text-shadow: 0 0 40px rgba(255,215,0,0.5), 0 4px 20px rgba(0,0,0,0.8);
    letter-spacing: 0.04em;
    margin-bottom: 4px;
}
.pozo-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    color: rgba(255,255,255,0.35);
    text-align: center;
    margin-bottom: 28px;
}
.pozo-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,215,0,0.25), transparent);
    margin: 0 0 22px;
}
.ganadores-titulo {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1rem;
    letter-spacing: 0.2em;
    color: rgba(255,255,255,0.5);
    text-align: center;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.empate-nota {
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    color: rgba(255,215,0,0.75);
    text-align: center;
    margin: -6px 0 14px;
    letter-spacing: 0.02em;
}
.ganador-row {
    position: relative;
    display: flex;
    align-items: center;
    gap: 14px;
    background: linear-gradient(135deg, rgba(255,215,0,0.10), rgba(255,215,0,0.03));
    border: 1px solid rgba(255,215,0,0.35);
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 10px;
    overflow: hidden;
}
.ganador-row::before {
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, #FFD700, #FFA500);
}
.ganador-medalla {
    font-size: 1.7rem;
    line-height: 1;
    filter: drop-shadow(0 2px 6px rgba(255,215,0,0.5));
}
.ganador-nombre {
    font-family: 'Inter', sans-serif;
    font-size: 1.02rem;
    font-weight: 700;
    color: #fff;
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.ganador-datos {
    display: flex;
    align-items: center;
    gap: 16px;
}
.ganador-pts-box { text-align: center; }
.ganador-pts {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.7rem;
    color: #FFD700;
    line-height: 1;
}
.ganador-pts-label {
    font-size: 0.58rem;
    color: rgba(255,210,0,0.5);
    text-transform: uppercase;
    letter-spacing: 0.15em;
}
.ganador-premio-box {
    text-align: center;
    background: rgba(0,0,0,0.28);
    border: 1px solid rgba(255,215,0,0.25);
    border-radius: 10px;
    padding: 4px 12px;
}
.ganador-premio {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.15rem;
    color: #4ADE80;
    line-height: 1.1;
}
.ganador-premio-label {
    font-size: 0.55rem;
    color: rgba(74,222,128,0.6);
    text-transform: uppercase;
    letter-spacing: 0.12em;
}
.sin-ganador {
    text-align: center;
    color: rgba(255,255,255,0.3);
    font-size: 0.85rem;
    padding: 12px 0;
    font-family: 'Inter', sans-serif;
}
.pozo-formula {
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    color: rgba(255,255,255,0.35);
    text-align: center;
    margin-top: 18px;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)

try:
    from database import conectar
    from ranking import obtener_ranking

    sb = conectar()
    resp_part = sb.table("jugadores").select("id, pagado, activo").execute()
    # El pozo solo debe sumar jugadores que pagaron la inscripción Y que no
    # estén pausados/ocultos por el admin. Si "activo" no existiera todavía
    # en algún registro viejo, se lo trata como True por defecto.
    _jugadores_habilitados = [
        j for j in (resp_part.data or [])
        if j.get("pagado") and j.get("activo", True)
    ]
    total_participantes = len(_jugadores_habilitados)
    pozo = total_participantes * 10_000

    ranking = obtener_ranking()

    if ranking:
        max_puntos = ranking[0]["puntos"]
        ganadores = [r for r in ranking if r["puntos"] == max_puntos]
    else:
        max_puntos = 0
        ganadores = []

    pozo_fmt = f"${pozo:,.0f}".replace(",", ".")

    cant_ganadores = len(ganadores)
    premio_individual = pozo / cant_ganadores if cant_ganadores > 0 else 0
    premio_individual_fmt = f"${premio_individual:,.0f}".replace(",", ".")

    if ganadores and max_puntos > 0:
        filas = []
        for g in ganadores:
            fila = (
                '<div class="ganador-row">'
                '<div class="ganador-medalla"></div>'
                f'<div class="ganador-nombre">{g["nombre"]}</div>'
                '<div class="ganador-datos">'
                '<div class="ganador-pts-box">'
                f'<div class="ganador-pts">{g["puntos"]}</div>'
                '<div class="ganador-pts-label">puntos</div>'
                '</div>'
                '<div class="ganador-premio-box">'
                f'<div class="ganador-premio">{premio_individual_fmt}</div>'
                '<div class="ganador-premio-label">le toca</div>'
                '</div>'
                '</div>'
                '</div>'
            )
            filas.append(fila)
        ganadores_html = "".join(filas)
    else:
        ganadores_html = '<div class="sin-ganador">— Aún no hay puntos registrados —</div>'

    if cant_ganadores > 1:
        empate_html = f'<div class="empate-nota">⚡ Empate entre {cant_ganadores} participantes — el pozo se reparte en partes iguales</div>'
        formula_texto = f"El pozo se divide en partes iguales entre los {cant_ganadores} líderes del 1° puesto"
    elif cant_ganadores == 1:
        empate_html = ""
        formula_texto = "El ganador del 1° puesto se lleva el pozo completo"
    else:
        empate_html = ""
        formula_texto = "El ganador del 1° puesto se lleva el pozo completo"

    titulo_ganadores = f" Líder{'es' if cant_ganadores > 1 else ''} del ranking"

    logo_header_html = (
        f'<div class="pozo-logo-header"><img src="data:image/png;base64,{LOGO_BASE64}"></div>'
        if LOGO_BASE64 else ""
    )

    card_html = (
        '<div class="pozo-wrapper">'
        '<div class="pozo-card">'
        f'{logo_header_html}'
        '<div class="pozo-label">Premio total acumulado</div>'
        f'<div class="pozo-monto">{pozo_fmt}</div>'
        f'<div class="pozo-sub">{total_participantes} participantes · $10.000 c/u</div>'
        '<div class="pozo-divider"></div>'
        f'<div class="ganadores-titulo">{titulo_ganadores}</div>'
        f'{empate_html}'
        f'{ganadores_html}'
        f'<div class="pozo-formula">{formula_texto}</div>'
        '</div>'
        '</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

except Exception as e:
    st.warning(f"No se pudo cargar el pozo: {e}")
