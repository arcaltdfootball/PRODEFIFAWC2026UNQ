"""
03_Fixture.py — Prode Liga Profesional Argentina
Cambios:
  - Boleta usa marcador exacto (goles local / goles visitante); el signo
    (1/X/2) se deriva automáticamente a partir del marcador cargado.
  - Sistema de puntaje: 1 punto por acertar el signo (Local/Empate/Visitante),
    3 puntos en total si se acierta el marcador exacto.
  - Admin puede eliminar participantes con confirmación
  - Admin puede resetear (borrar) la lista completa de participantes
  - Resultado se guarda como goles y se refleja en 01_Resultados.py

IMPORTANTE: la tabla `pronosticos` en Supabase necesita las columnas
`goles_local_pred` (int, nullable) y `goles_visitante_pred` (int, nullable)
además de las existentes `signo_pred` y `puntos`. Si no existen, correr:

    ALTER TABLE pronosticos ADD COLUMN goles_local_pred integer;
    ALTER TABLE pronosticos ADD COLUMN goles_visitante_pred integer;

También necesita la columna `sin_marcador` (boolean), que indica si el
pronóstico se guardó eligiendo solo el signo (Local/Empate/Visitante) sin
cargar un marcador exacto a mano, para que la boleta siga mostrando "–" en
los goles aunque se recargue la página o se vuelva a entrar otro día. Si no
existe, correr:

    ALTER TABLE pronosticos ADD COLUMN sin_marcador boolean DEFAULT false;

También, para que el admin pueda VER la contraseña actual de cada jugador
(no solo resetearla), la tabla `jugadores` necesita guardar la contraseña
en texto plano además del hash. Si no existe, correr:

    ALTER TABLE jugadores ADD COLUMN password_plano text;

Nota de seguridad: guardar la contraseña en texto plano permite que el
admin la vea, pero es menos seguro que solo guardar el hash. Se usa acá
porque es un prode privado entre amigos/familia, no una app con datos
sensibles. Los jugadores creados o con contraseña reseteada ANTES de este
cambio no van a tener `password_plano` cargado hasta que se les resetee
o modifique la contraseña una vez.

También, para poder transferirle el premio a cada jugador en caso de que
gane, la tabla `jugadores` necesita guardar su Alias o CBU. Si no existe,
correr:

    ALTER TABLE jugadores ADD COLUMN alias_cbu text;

También, para que el admin le pueda cargar una foto de perfil a cada
participante desde la card (en vez del círculo de iniciales), la tabla
`jugadores` necesita una columna para guardarla. Se guarda como JPEG
comprimido en base64 (no requiere crear un bucket de Storage aparte). Si
no existe, correr:

    ALTER TABLE jugadores ADD COLUMN foto_base64 text;
"""
import base64
import hashlib
import json
import os
import secrets
import string
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutureTimeoutError
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components
import mercadopago
from PIL import Image  # ya es dependencia de Streamlit, no hace falta instalar nada nuevo
from database import conectar
from escudos_map import url_escudo

# ══════════════════════════════════════════════════════════════════════════
# MERCADO PAGO — SDK y helpers de cobro de inscripción
# ══════════════════════════════════════════════════════════════════════════
sdk = mercadopago.SDK(st.secrets["MP_ACCESS_TOKEN"])

# Pool chico y liviano solo para poder ponerle un límite de tiempo duro a
# las llamadas a la API de Mercado Pago (ver `_con_timeout` más abajo).
_mp_executor = ThreadPoolExecutor(max_workers=4)


def _con_timeout(func, *args, timeout=8, **kwargs):
    """Ejecuta `func(*args, **kwargs)` con un límite de tiempo duro.

    El SDK de Mercado Pago (y la librería `requests` que usa por debajo)
    no tiene un timeout configurado por defecto: si la API de MP tarda
    en responder, se demora, o la conexión se cuelga por lo que sea, la
    llamada puede quedar esperando indefinidamente. Eso freezaba toda la
    página (el jugador volvía de pagar y se quedaba con el spinner de
    Streamlit girando para siempre, sin loguearlo ni mostrar ningún
    error).

    Acá corremos la llamada en un thread aparte y, si no contesta en
    `timeout` segundos, la abandonamos y seguimos con la ejecución del
    resto de la página en vez de quedarnos colgados esperándola. El
    thread de la llamada lenta puede seguir corriendo en segundo plano
    (Python no lo puede matar a la fuerza), pero ya no bloquea al
    usuario ni a Streamlit.
    """
    future = _mp_executor.submit(func, *args, **kwargs)
    try:
        return future.result(timeout=timeout)
    except _FutureTimeoutError:
        raise TimeoutError(
            f"La API de Mercado Pago no respondió en {timeout}s (se abandonó "
            "la espera para no colgar la página)."
        )


def crear_preferencia_pago(jugador_id, nombre: str) -> str:
    """Crea una preferencia de pago (Checkout Pro) para un jugador y
    devuelve el link (init_point) al que hay que redirigirlo para pagar."""
    base_url = st.secrets["MP_BASE_URL"].rstrip("/")
    # IMPORTANTE: el back_url tiene que apuntar puntualmente a esta página
    # (Boleta_digital), no a la raíz del sitio. La lógica que re-loguea al
    # jugador y verifica el pago al volver de Mercado Pago vive acá, en
    # 03_Boleta_digital.py, que Streamlit sirve en la ruta "/Boleta_digital"
    # (nombre de archivo sin el prefijo numérico "03_" ni la extensión).
    # Si el back_url apunta a "/", el usuario cae en el Home al volver, ese
    # código nunca se ejecuta, y por eso queda deslogueado y sin la boleta
    # marcada como paga.
    pagina_boleta = f"{base_url}/Boleta_digital"

    # ── SIN PUENTE ESTÁTICO ────────────────────────────────────────────
    # Antes volvíamos primero a un archivo bridge_pago.html (servido como
    # estático por Streamlit) para "despertar" la app antes de navegar a
    # la página real. Se descartó: el servido de archivos estáticos de
    # Streamlit Community Cloud resultó poco confiable en este proyecto
    # (con enableStaticServing=true correctamente configurado, los
    # pedidos a /app/static/... igual caían en el catch-all genérico de
    # la plataforma en vez de servir el archivo real — confirmado
    # inspeccionando el HTML crudo devuelto). Un click real del navegador
    # de Mercado Pago hacia el dominio de la app ya la despierta sola, sin
    # necesitar ese paso intermedio. Volvemos entonces directo a
    # "/Boleta_digital" con los mismos parámetros (pago, jid) que antes
    # le pasábamos al puente, para que el bloque de verificación de pago
    # + re-login de más abajo siga funcionando exactamente igual.
    preference_data = {
        "items": [{
            "title": f"Inscripción Prode - {nombre}",
            "quantity": 1,
            "unit_price": float(st.secrets["MP_MONTO"]),
            "currency_id": "ARS",
        }],
        "external_reference": str(jugador_id),
        "back_urls": {
            "success": f"{pagina_boleta}?pago=ok&jid={jugador_id}",
            "pending": f"{pagina_boleta}?pago=pendiente&jid={jugador_id}",
            "failure": f"{pagina_boleta}?pago=fallo&jid={jugador_id}",
        },
        "auto_return": "approved",
    }
    result = _con_timeout(sdk.preference().create, preference_data)
    pref = result["response"]
    sb.table("jugadores").update({"mp_preference_id": pref["id"]}).eq("id", jugador_id).execute()
    return pref["init_point"]


def verificar_pago(jugador_id, payment_id: str) -> bool:
    """Consulta el estado real del pago contra la API de Mercado Pago
    (nunca confiar solo en los parámetros que vienen en la URL de retorno)."""
    try:
        resultado = _con_timeout(sdk.payment().get, payment_id)
        pago = resultado["response"]
    except Exception:
        return False
    if (
        pago.get("status") == "approved"
        and str(pago.get("external_reference")) == str(jugador_id)
    ):
        try:
            _con_timeout(
                lambda: sb.table("jugadores").update({
                    "pagado": True,
                    "mp_payment_id": payment_id,
                }).eq("id", jugador_id).execute(),
                timeout=8,
            )
        except Exception:
            pass  # el pago SÍ está confirmado en MP; si Supabase falla acá,
            # igual devolvemos True — la auto-cura de más abajo lo va a
            # volver a intentar marcar en el próximo ingreso.
        return True
    return False


def verificar_pago_por_referencia(jugador_id) -> bool:
    """Verificación de RESPALDO que no depende de que el navegador haya
    vuelto limpio desde Mercado Pago con los parámetros en la URL.

    El flujo normal (`verificar_pago`) necesita el `payment_id` que viaja
    en el query string del back_url. En el celular eso se pierde seguido
    (el navegador in-app de WhatsApp/Instagram, Safari, o la app del banco
    a veces no vuelven bien, o el usuario cierra la pestaña de MP a mano
    antes de que redirija) y ahí el jugador pagó de verdad pero el sistema
    nunca se entera.

    Esta función no necesita ningún dato de la URL: le pregunta directo a
    la API de Mercado Pago "¿hay algún pago aprobado con este
    external_reference (= id del jugador)?". Si lo encuentra, marca
    `pagado = True` igual que el flujo normal. Se puede llamar tanto
    automáticamente (auto-cura al cargar la página) como a mano (botón
    "Ya pagué, verificar ahora")."""
    try:
        resultado = _con_timeout(
            sdk.payment().search,
            {
                "external_reference": str(jugador_id),
                "sort": "date_created",
                "criteria": "desc",
            },
        )
        pagos = (resultado.get("response") or {}).get("results", [])
    except Exception:
        return False

    for pago in pagos:
        if (
            pago.get("status") == "approved"
            and str(pago.get("external_reference")) == str(jugador_id)
        ):
            try:
                _con_timeout(
                    lambda: sb.table("jugadores").update({
                        "pagado": True,
                        "mp_payment_id": pago.get("id"),
                    }).eq("id", jugador_id).execute(),
                    timeout=8,
                )
            except Exception:
                pass
            return True
    return False


@st.cache_data(show_spinner=False)
def _fondo_pagina_datauri():
    """
    Busca AFA2026.png junto a este script (o en subcarpetas 'assets'/'static'
    del proyecto) y la devuelve como data URI en base64, para usarla de fondo
    sin depender de un link externo. Si no la encuentra, devuelve None y se
    usa una URL de respaldo.
    """
    candidatos = [
        Path(__file__).parent / "AFA2026.png",
        Path(__file__).parent / "assets" / "AFA2026.png",
        Path(__file__).parent / "static" / "AFA2026.png",
        Path(__file__).parent.parent / "AFA2026.png",
    ]
    for ruta in candidatos:
        try:
            if ruta.is_file():
                b64 = base64.b64encode(ruta.read_bytes()).decode()
                return f"data:image/png;base64,{b64}"
        except Exception:
            pass
    return None


_FONDO_AFA2026 = _fondo_pagina_datauri() or (
    "https://raw.githubusercontent.com/arcaltdfootball/PRODEFIFAWC2026UNQ/"
    "main/prode_supabase/AFA2026.png"
)


def _rol_de_supabase_key():
    """Decodifica el JWT de SUPABASE_KEY (sin validar firma) solo para
    mostrar el campo 'role' (anon / service_role) y así diagnosticar
    a simple vista qué key está usando realmente la app en este momento."""
    key = os.environ.get("SUPABASE_KEY", "")
    if not key:
        try:
            key = st.secrets.get("SUPABASE_KEY", "")
        except Exception:
            key = ""
    if not key or key.count(".") != 2:
        return None, None
    try:
        payload_b64 = key.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)  # padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("role"), key[-6:]
    except Exception:
        return None, key[-6:] if key else None

st.set_page_config(page_title="Fixture - Mi Boleta", page_icon="📝", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600&display=swap');

    [data-testid="stAppViewContainer"] {
        background-image:
            linear-gradient(160deg, rgba(9,12,22,0.87) 0%, rgba(13,17,32,0.84) 45%, rgba(7,9,16,0.90) 100%),
            url('__FONDO_AFA2026__');
        background-size: cover, cover;
        background-position: center, center;
        background-repeat: no-repeat, no-repeat;
        background-attachment: fixed, fixed;
        background-color: #0b0f19;
    }
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stVerticalBlock"] { position: relative; z-index: 1; }

    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 1px; }

    /* ═══════════ TABS DE ZONA — estilo glass / blur 2026 ═══════════ */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        display: inline-flex;
        gap: 6px;
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 999px;
        padding: 6px;
        backdrop-filter: blur(22px) saturate(180%);
        -webkit-backdrop-filter: blur(22px) saturate(180%);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.06);
        margin-bottom: 18px;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }
    [data-testid="stTabs"] button[data-baseweb="tab"],
    [data-testid="stTabs"] [data-testid="stTab"] {
        font-family: 'Bebas Neue', sans-serif !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.06em !important;
        color: rgba(255,255,255,0.55) !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 999px !important;
        padding: 9px 24px !important;
        margin: 0 !important;
        transition: all .22s ease !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"]:hover,
    [data-testid="stTabs"] [data-testid="stTab"]:hover {
        color: #fff !important;
        background: rgba(255,255,255,0.07) !important;
    }
    [data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
    [data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {
        color: #e8c96b !important;
        background: linear-gradient(135deg, rgba(232,201,107,0.28) 0%, rgba(232,201,107,0.08) 100%) !important;
        border: 1px solid rgba(232,201,107,0.45) !important;
        box-shadow: 0 4px 18px rgba(232,201,107,0.22), inset 0 1px 0 rgba(255,255,255,0.12) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-panel"] { padding-top: 4px; }

    .titulo-pagina {
        font-family: 'Bebas Neue', sans-serif;
        font-size: 40px; color: #e8c96b; text-align: center;
        letter-spacing: 3px; margin-bottom: 4px;
    }
    .subtitulo-pagina {
        text-align: center; color: #94a3b8; font-size: 0.9rem;
        margin-bottom: 24px; font-family: 'Inter', sans-serif;
    }
    .fila-equipo {
        display: flex; align-items: center; gap: 8px;
        flex: 1; font-size: 0.9rem; font-family: 'Inter', sans-serif;
    }
    .fila-equipo.derecha { justify-content: flex-end; text-align: right; }
    .fila-escudo { width: 40px; height: 40px; object-fit: contain; }
    .fila-meta {
        font-size: 0.7rem; color: #64748b; text-align: center;
        margin-bottom: 2px; font-family: 'Inter', sans-serif;
    }

    /* Badges */
    .badge-1   { background:rgba(59,130,246,0.18); color:#60a5fa;   border-radius:10px; padding:3px 12px; font-size:0.78rem; font-weight:700; }
    .badge-x   { background:rgba(148,163,184,0.18); color:#94a3b8;  border-radius:10px; padding:3px 12px; font-size:0.78rem; font-weight:700; }
    .badge-2   { background:rgba(239,68,68,0.18);  color:#f87171;   border-radius:10px; padding:3px 12px; font-size:0.78rem; font-weight:700; }
    .badge-ok  { background:rgba(74,222,128,0.15); color:#4ade80;   border-radius:10px; padding:3px 10px; font-size:0.72rem; }
    .badge-pts { background:rgba(232,201,107,0.18);color:#e8c96b;   border-radius:10px; padding:3px 10px; font-size:0.72rem; margin-left:6px; }
    .badge-sin { background:rgba(148,163,184,0.15);color:#94a3b8;   border-radius:10px; padding:3px 10px; font-size:0.72rem; }
    .badge-admin { background:rgba(239,68,68,0.15);color:#f87171;   border-radius:10px; padding:2px 10px; font-size:0.72rem; }

    /* ═══════════ CARD DE PARTICIPANTE (panel admin → Jugadores) ═══════════ */
    .tp-avatar-admin {
        flex-shrink: 0;
        width: 72px; height: 72px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Bebas Neue', sans-serif; font-size: 1.9rem; color: #0b0f19;
        background: linear-gradient(135deg, #e8c96b 0%, #c9a54a 100%);
        background-size: cover; background-position: center;
        box-shadow: 0 4px 14px rgba(232,201,107,0.35);
        border: 2px solid rgba(232,201,107,0.4);
        margin: 0 auto 6px auto;
    }
    .tp-rank-box {
        text-align: center; padding: 10px 8px; border-radius: 14px;
        background: linear-gradient(135deg, rgba(232,201,107,0.14) 0%, rgba(232,201,107,0.03) 100%);
        border: 1px solid rgba(232,201,107,0.3);
    }
    .tp-rank-num {
        font-family: 'Bebas Neue', sans-serif; font-size: 2.4rem; line-height: 1;
        color: #e8c96b; letter-spacing: 1px;
    }
    .tp-rank-label {
        font-family: 'Inter', sans-serif; font-size: 0.68rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.06em; color: #94a3b8;
        margin-top: 2px;
    }
    .tp-rank-pts {
        font-family: 'Inter', sans-serif; font-size: 0.78rem; color: #cbd5e1;
        margin-top: 4px;
    }
    .tp-aciertos-wrap {
        display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;
    }
    .tp-acierto-chip {
        font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 600;
        border-radius: 8px; padding: 4px 9px;
        background: rgba(148,163,184,0.12); color: #cbd5e1;
        border: 1px solid rgba(148,163,184,0.18);
        white-space: nowrap;
    }
    .tp-acierto-chip.tp-buena { background: rgba(74,222,128,0.13); color: #4ade80; border-color: rgba(74,222,128,0.25); }
    .tp-acierto-chip.tp-mala  { background: rgba(239,68,68,0.12);  color: #f87171; border-color: rgba(239,68,68,0.22); }

    /* ═══════════ TARJETA DE PERFIL — usuario + Alias/CBU (glass) ═══════════ */
    .tarjeta-perfil {
        position: relative;
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 18px 24px;
        margin-bottom: 22px;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(255,255,255,0.075) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(232,201,107,0.25);
        backdrop-filter: blur(22px) saturate(180%);
        -webkit-backdrop-filter: blur(22px) saturate(180%);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
        overflow: hidden;
    }
    .tarjeta-perfil::before {
        content: "";
        position: absolute; inset: 0;
        background: radial-gradient(circle at 0% 0%, rgba(232,201,107,0.16), transparent 55%);
        pointer-events: none;
    }
    .tp-avatar {
        flex-shrink: 0;
        width: 54px; height: 54px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Bebas Neue', sans-serif; font-size: 1.5rem; color: #0b0f19;
        background: linear-gradient(135deg, #e8c96b 0%, #c9a54a 100%);
        box-shadow: 0 4px 14px rgba(232,201,107,0.35);
        position: relative; z-index: 1;
    }
    .tp-texto { position: relative; z-index: 1; }
    .tp-saludo {
        font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8;
        margin: 0 0 2px 0;
    }
    .tp-nombre {
        font-family: 'Bebas Neue', sans-serif; font-size: 1.5rem; color: #f1f5f9;
        letter-spacing: 0.5px; line-height: 1.1; margin: 0;
    }
    .tp-username {
        font-family: 'Inter', sans-serif; font-size: 0.82rem; color: #e8c96b;
        margin: 2px 0 0 0;
    }
    .tp-chips {
        margin-left: auto; flex-shrink: 0; position: relative; z-index: 1;
        display: flex; flex-direction: column; gap: 6px; align-items: flex-end;
    }
    .tp-premio-chip {
        display: flex; align-items: center; gap: 6px;
        font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 600;
        padding: 6px 14px; border-radius: 999px; white-space: nowrap;
    }
    .tp-premio-ok {
        background: rgba(74,222,128,0.15); color: #4ade80;
        border: 1px solid rgba(74,222,128,0.3);
    }
    .tp-premio-pendiente {
        background: rgba(232,201,107,0.14); color: #e8c96b;
        border: 1px solid rgba(232,201,107,0.3);
    }
    @media (max-width: 640px) {
        .tarjeta-perfil { flex-wrap: wrap; }
        .tp-chips { margin-left: 0; align-items: flex-start; }
    }

    /* Selector 1/X/2 */
    .opcion-1x2 {
        display: flex; gap: 6px; align-items: center; flex-wrap: wrap;
    }

    /* Cajas de selección rápida Local / Empate / Visitante */
    div.pick1x2-marker + div[data-testid="stHorizontalBlock"] {
        gap: 10px;
    }
    div.pick1x2-marker + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
        position: relative;
        backdrop-filter: blur(14px) saturate(160%);
        -webkit-backdrop-filter: blur(14px) saturate(160%);
        background: linear-gradient(150deg, rgba(255,255,255,0.07), rgba(255,255,255,0.015) 70%);
        border: 1.5px dashed rgba(148,163,184,0.35);
        border-radius: 18px;
        min-height: 64px;
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        white-space: normal;
        word-break: break-word;
        line-height: 1.15;
        padding: 6px 8px;
        font-size: 0.92rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        font-family: 'Inter', sans-serif;
        color: rgba(148,163,184,0.75);
        box-shadow: 0 4px 18px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: transform 0.18s cubic-bezier(.34,1.56,.64,1),
                    border-color 0.18s ease, box-shadow 0.22s ease,
                    background 0.18s ease, color 0.18s ease;
    }
    div.pick1x2-marker + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover {
        border-color: rgba(232,201,107,0.8);
        background: linear-gradient(150deg, rgba(232,201,107,0.14), rgba(232,201,107,0.02) 70%);
        color: #e8c96b;
        transform: translateY(-3px) scale(1.015);
        box-shadow: 0 10px 24px rgba(232,201,107,0.18), inset 0 1px 0 rgba(255,255,255,0.06);
    }
    div.pick1x2-marker + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:active {
        transform: translateY(0) scale(0.97);
    }
    div.pick1x2-marker + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="primary"] {
        border: 1.5px solid #4ade80;
        background: linear-gradient(150deg, rgba(74,222,128,0.24), rgba(74,222,128,0.04) 70%);
        color: #4ade80;
        text-shadow: 0 0 20px rgba(74,222,128,0.65);
        box-shadow: 0 0 0 3px rgba(74,222,128,0.12), 0 10px 26px rgba(74,222,128,0.28),
                    inset 0 1px 0 rgba(255,255,255,0.08);
        transform: scale(1.045);
        animation: pick1x2-pop 0.28s cubic-bezier(.34,1.56,.64,1);
    }
    div.pick1x2-marker + div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.06);
    }
    @keyframes pick1x2-pop {
        0%   { transform: scale(0.88); }
        65%  { transform: scale(1.09); }
        100% { transform: scale(1.045); }
    }
    </style>
    """.replace("__FONDO_AFA2026__", _FONDO_AFA2026),
    unsafe_allow_html=True,
)

try:
    sb = conectar()
except Exception as e:
    st.error(f"Error al conectar con la base de datos: {e}")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "aleotero")


def _hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def _generar_password(largo: int = 8) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(largo))


TZ_ARG = ZoneInfo("America/Argentina/Buenos_Aires")
MINUTOS_CIERRE_ANTES = 5


def _horario_confirmado(p) -> bool:
    """True si el partido tiene fecha Y hora cargadas (confirmadas)."""
    return bool(p.get("fecha_partido")) and bool(p.get("hora"))


# Formatos de fecha y hora aceptados, para bancar cómo sea que esté
# cargado el dato en la base (texto libre, date/time de Postgres, etc.)
_FORMATOS_FECHA = [
    "%Y-%m-%d",   # 2026-07-25 (ISO, lo que devuelve Postgres normalmente)
    "%d/%m/%Y",   # 25/07/2026 (formato argentino)
    "%d-%m-%Y",   # 25-07-2026
    "%Y/%m/%d",   # 2026/07/25
    "%d/%m/%y",   # 25/07/26
]
_FORMATOS_HORA = [
    "%H:%M:%S",   # 20:00:00 (time de Postgres)
    "%H:%M",      # 20:00
    "%H.%M",      # 20.00
    "%Hhs",       # 20hs
    "%H",         # 20
]


def _parsear_fecha(fecha_raw):
    fecha_str = str(fecha_raw).strip()
    # Si viene como timestamp ISO ("2026-07-25T00:00:00" o con espacio),
    # nos quedamos solo con la parte de fecha.
    fecha_str = fecha_str.split("T")[0].split(" ")[0]
    for fmt in _FORMATOS_FECHA:
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue
    return None


def _parsear_hora(hora_raw):
    hora_str = str(hora_raw).strip()
    for fmt in _FORMATOS_HORA:
        try:
            return datetime.strptime(hora_str, fmt).time()
        except ValueError:
            continue
    return None


def _momento_cierre(p):
    """
    Devuelve (datetime_cierre, error) donde datetime_cierre es el momento
    (con tz Argentina) a partir del cual se cierra el pronóstico para ese
    partido (kickoff - MINUTOS_CIERRE_ANTES minutos), o None si no se pudo
    calcular. `error` trae un mensaje si fecha/hora estaban cargadas pero no
    se pudieron interpretar (para poder mostrarlo y detectar el problema,
    en vez de fallar en silencio).
    """
    if not _horario_confirmado(p):
        return None, None

    fecha_obj = _parsear_fecha(p["fecha_partido"])
    hora_obj = _parsear_hora(p["hora"])

    if fecha_obj is None or hora_obj is None:
        return None, (
            f"No se pudo interpretar fecha/hora del partido "
            f"(fecha_partido={p.get('fecha_partido')!r}, hora={p.get('hora')!r})."
        )

    kickoff = datetime.combine(fecha_obj, hora_obj, tzinfo=TZ_ARG)
    return kickoff - timedelta(minutes=MINUTOS_CIERRE_ANTES), None


def _pronostico_cerrado(p) -> bool:
    """
    True si, con fecha/hora confirmada, ya estamos dentro de la ventana de
    cierre (a partir de MINUTOS_CIERRE_ANTES minutos antes del partido, hora
    de Argentina). Si no hay fecha/hora confirmada, nunca se cierra por esta
    vía (solo se cierra cuando el partido ya fue jugado).

    Si hay fecha/hora cargadas pero no se pudieron interpretar, se cierra
    igual por seguridad (mejor bloquear de más que dejar pronosticar un
    partido que ya empezó por un problema de formato).
    """
    cierre, error = _momento_cierre(p)
    if cierre is None:
        return error is not None  # confirmado pero ilegible -> cerrar por seguridad
    ahora = datetime.now(TZ_ARG)
    return ahora >= cierre


def _signo_a_texto(signo):
    """Convierte 1/X/2 a texto descriptivo."""
    return {"1": "Local (1)", "X": "Empate (X)", "2": "Visitante (2)"}.get(signo, signo or "—")


def _badge_signo(signo):
    """Devuelve HTML del badge según signo."""
    if signo == "1":
        return '<span class="badge-1">1 · LOCAL</span>'
    if signo == "X":
        return '<span class="badge-x">X · EMPATE</span>'
    if signo == "2":
        return '<span class="badge-2">2 · VISIT.</span>'
    return '<span class="badge-sin">Sin pronóstico</span>'


# ══════════════════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ══════════════════════════════════════════════════════════════════════════
# Marcador para saber si esta es la PRIMERA corrida del script en esta
# sesión de navegador (recién abrió/recargó la página) o si es un rerun
# interno posterior (por ejemplo, el que dispara "Cerrar sesión" con
# st.rerun(), que NO recarga el navegador). Lo necesitamos para que la
# red de seguridad de recuperación de pago (más abajo) solo intente
# redirigir en una carga de página realmente nueva, y no se "gaste" su
# único intento en un rerun interno donde el usuario ni se enteró.
_es_primera_carga_de_sesion = "_visita_inicial_procesada" not in st.session_state
st.session_state["_visita_inicial_procesada"] = True

for key, default in [
    ("es_admin", False),
    ("jugador_id", None),
    ("jugador_nombre", None),
    ("confirmar_eliminar_id", None),
    ("confirmar_reset_all", False),
    ("confirmar_reset_fecha", None),
    ("confirmar_reset_boleta_fecha", None),
    ("_recien_logueado", False),
    ("confirmar_marcar_no_pagado_todos", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def _cerrar_sesion():
    st.session_state.es_admin = False
    st.session_state.jugador_id = None
    st.session_state.jugador_nombre = None
    st.rerun()


def _cerrar_sidebar_automaticamente():
    """Colapsa la barra lateral vía JS justo después de loguearse (como
    jugador o admin) o de crear una cuenta nueva, para que no quede
    abierta confundiendo al usuario sobre en qué página está parado."""
    components.html(
        """
        <script>
        (function () {
            function intentarCerrar(intentos) {
                if (intentos <= 0) return;
                const doc = window.parent.document;
                let btn = doc.querySelector('[data-testid="stSidebarCollapseButton"] button');
                if (!btn) btn = doc.querySelector('[data-testid="stSidebarCollapseButton"]');
                if (!btn) {
                    const candidatos = doc.querySelectorAll('button[aria-label]');
                    for (const c of candidatos) {
                        const lbl = (c.getAttribute('aria-label') || '').toLowerCase();
                        if (lbl.includes('sidebar') || lbl.includes('collapse')) {
                            btn = c;
                            break;
                        }
                    }
                }
                if (btn) {
                    btn.click();
                } else {
                    setTimeout(function () { intentarCerrar(intentos - 1); }, 150);
                }
            }
            intentarCerrar(15);
        })();
        </script>
        """,
        height=0,
    )


# ══════════════════════════════════════════════════════════════════════════
# RETORNO DESDE MERCADO PAGO — verificar pago contra la API (no confiar
# solo en los parámetros de la URL) y RE-LOGUEAR automáticamente al
# jugador, porque el redirect de MP es una navegación nueva del
# navegador y Streamlit pierde el session_state (el login) al volver.
# ══════════════════════════════════════════════════════════════════════════
_params_mp = st.query_params
if "jid" in _params_mp and _params_mp.get("pago") in ("ok", "pendiente", "fallo", "recuperar"):
    # OJO: el id de `jugadores` en Supabase es un UUID (ej.
    # "90c5ba31-04e9-4dfe-8848-232ffdc563c0"), NO un entero. Antes acá se
    # forzaba `int(...)`, lo cual tira ValueError apenas MP vuelve con un
    # jid real y hace que la página quede colgada/rota — el usuario paga,
    # MP intenta redirigirlo solo, y esta excepción corta la ejecución
    # antes de que el resto del script (login, verificación de pago, UI)
    # llegue siquiera a correr. Por eso el "vuelve solo" nunca funcionaba
    # de verdad para nadie, aunque el link estuviera bien armado.
    _jid_mp = _params_mp["jid"]

    # Restauramos la sesión del jugador para que no tenga que volver a
    # loguearse a mano y pueda seguir jugando directo. Con timeout: si
    # Supabase no contesta rápido, no nos quedamos colgados acá tampoco.
    try:
        _jrow_mp = _con_timeout(
            lambda: sb.table("jugadores").select("id, nombre").eq("id", _jid_mp).execute().data,
            timeout=8,
        )
    except Exception:
        _jrow_mp = None

    if _jrow_mp:
        st.session_state.jugador_id = _jrow_mp[0]["id"]
        st.session_state.jugador_nombre = _jrow_mp[0]["nombre"]
        st.session_state.es_admin = False

    if _params_mp.get("pago") == "ok":
        _cid = _params_mp.get("collection_id") or _params_mp.get("payment_id")
        _pago_confirmado = False
        if _cid:
            try:
                _pago_confirmado = verificar_pago(_jid_mp, _cid)
            except Exception:
                _pago_confirmado = False
        if not _pago_confirmado:
            # Respaldo inmediato: si por lo que sea el chequeo por
            # payment_id falla (token vencido, demora de MP en propagar
            # el estado, etc.), probamos también por external_reference
            # antes de resignarnos a mostrarle el cartel de "no pudimos
            # confirmar" a alguien que sí pagó.
            try:
                _pago_confirmado = verificar_pago_por_referencia(_jid_mp)
            except Exception:
                _pago_confirmado = False

        if _pago_confirmado:
            st.session_state._recien_logueado = True
            st.success("✅ ¡Pago acreditado! Ya podés participar — bienvenido de nuevo.")
        else:
            st.warning(
                "No pudimos confirmar el pago todavía. Si ya pagaste, esperá "
                "unos segundos y volvé a entrar, o usá el botón "
                "'Ya pagué, verificar ahora' más abajo."
            )
    elif _params_mp.get("pago") == "pendiente":
        st.info("⏳ Tu pago está pendiente de acreditación. Volvé a entrar en unos minutos.")
    elif _params_mp.get("pago") == "fallo":
        st.error("❌ El pago no se pudo procesar. Podés intentarlo de nuevo desde acá abajo.")
    elif _params_mp.get("pago") == "recuperar":
        # Llegamos acá por la red de seguridad de localStorage (más abajo
        # en el script), NO por un back_url real de Mercado Pago: pasa
        # cuando el navegador/app que usó el jugador para "volver al
        # sitio" perdió los parámetros de la URL en el camino (frecuente
        # en algunos navegadores in-app de Android). No tenemos
        # payment_id acá, así que vamos directo a preguntarle a la API
        # de MP si hay un pago aprobado para este jugador.
        try:
            _pago_confirmado = verificar_pago_por_referencia(_jid_mp)
        except Exception:
            _pago_confirmado = False
        if _pago_confirmado:
            st.session_state._recien_logueado = True
            st.success("✅ ¡Pago acreditado! Ya podés participar — bienvenido de nuevo.")
        else:
            st.info(
                "Te volvimos a loguear automáticamente. Si ya pagaste, puede "
                "tardar unos segundos en acreditarse — usá el botón "
                "'Ya pagué, verificar ahora' más abajo si hace falta."
            )

    # Ya procesamos el retorno (con o sin pago confirmado): borramos el
    # aviso guardado en localStorage para que la red de seguridad de más
    # abajo no siga insistiendo en recargar la página en cada visita.
    components.html(
        """
        <script>
        try { localStorage.removeItem('prode_pago_pendiente'); } catch (e) {}
        </script>
        """,
        height=0,
    )

    st.query_params.clear()
elif (
    _es_primera_carga_de_sesion
    and not st.session_state.jugador_id
    and not st.session_state.es_admin
):
    # ── Red de seguridad extra ──────────────────────────────────────────
    # Nadie logueado, la URL actual no trae parámetros de Mercado Pago, Y
    # esta es la primera corrida del script en esta sesión de navegador
    # (recién se abrió/recargó la página — NO un rerun interno como el
    # que dispara "Cerrar sesión"). Puede ser simplemente alguien
    # entrando de cero, pero también puede ser un jugador que volvió de
    # pagar y cuyo navegador/app perdió el query string en el camino
    # (pasa en algunos navegadores in-app o apps bancarias en Android
    # antes de abrir el link externo).
    #
    # Como respaldo, si en ESTE MISMO navegador quedó guardado en
    # localStorage el jid de un pago iniciado hace poco (lo guardamos
    # nosotros mismos, más abajo, justo antes de mandarlo a pagar), lo
    # recuperamos y recargamos la página agregando ese jid a la URL para
    # que el bloque de arriba pueda re-loguearlo y verificar el pago
    # automáticamente, sin que tenga que volver a escribir usuario y
    # contraseña.
    components.html(
        """
        <script>
        (function () {
            try {
                var raw = localStorage.getItem('prode_pago_pendiente');
                if (!raw) return;
                var data = JSON.parse(raw);
                var unaHora = 60 * 60 * 1000;
                if (!data.jid || !data.ts || (Date.now() - data.ts) > unaHora) {
                    localStorage.removeItem('prode_pago_pendiente');
                    return;
                }
                // Evitamos loops: solo intentamos la recuperación una
                // vez por pestaña/sesión de navegador.
                if (sessionStorage.getItem('prode_recuperando_pago')) return;
                sessionStorage.setItem('prode_recuperando_pago', '1');

                var url = new URL(window.parent.location.href);
                url.searchParams.set('pago', 'recuperar');
                url.searchParams.set('jid', data.jid);
                var destino = url.toString();

                // El iframe de components.html está "sandboxeado" y el
                // navegador bloquea que navegue directamente a la página
                // padre (aunque tengamos allow-same-origin, no tenemos
                // allow-top-navigation). Como sí tenemos acceso al DOM
                // de la página padre por ser mismo origen, inyectamos un
                // <script> ahí: ese script pasa a correr COMO PARTE de
                // la página principal (ya no dentro del iframe
                // sandboxeado), y desde ahí sí puede redirigir sin que
                // el navegador lo bloquee.
                var s = window.parent.document.createElement("script");
                s.textContent = "window.location.href = " + JSON.stringify(destino) + ";";
                window.parent.document.head.appendChild(s);
            } catch (e) {}
        })();
        </script>
        """,
        height=0,
    )

sesion_activa = st.session_state.es_admin or st.session_state.jugador_id is not None

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR: LOGIN / REGISTRO
# ══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔐 Mi cuenta")

    if st.session_state.es_admin:
        st.markdown('<span class="badge-admin">✅ ADMIN ACTIVO</span>', unsafe_allow_html=True)
        _rol_key, _tail_key = _rol_de_supabase_key()
        if _rol_key == "service_role":
            st.caption(f"🔑 Supabase key activa: `service_role` (…{_tail_key})")
        elif _rol_key:
            st.caption(f"⚠️ Supabase key activa: `{_rol_key}` (…{_tail_key}) — NO es service_role")
        else:
            st.caption("⚠️ No se pudo leer/decodificar SUPABASE_KEY")
        if st.button("Cerrar sesión", use_container_width=True):
            _cerrar_sesion()

    elif st.session_state.jugador_id:
        st.success(f"Sesión iniciada como **{st.session_state.jugador_nombre}**")
        if st.button("Cerrar sesión", use_container_width=True):
            _cerrar_sesion()

    else:
        modo = st.radio("Ingresar como:", ["Jugador", "Admin"], key="modo_login", horizontal=True)

        if modo == "Admin":
            user_a = st.text_input("Usuario admin", key="admin_user")
            pwd_a  = st.text_input("Contraseña", type="password", key="admin_pwd")
            if st.button("Ingresar", use_container_width=True, key="btn_admin"):
                if user_a.strip() == ADMIN_USERNAME and pwd_a == ADMIN_PASSWORD:
                    st.session_state.es_admin = True
                    st.session_state._recien_logueado = True
                    st.rerun()
                else:
                    st.error("Usuario o contraseña de admin incorrectos.")

        else:
            tab_login, tab_registro = st.tabs(["Ingresar", "Crear cuenta"])

            with tab_login:
                user_in = st.text_input("Usuario", key="login_user")
                pwd_in  = st.text_input("Contraseña", type="password", key="login_pwd")
                if st.button("Ingresar", use_container_width=True, key="btn_ingresar"):
                    try:
                        res = (
                            sb.table("jugadores")
                            .select("id, nombre, username, password_hash")
                            .eq("username", user_in.strip().lower())
                            .execute()
                        )
                        if res.data and res.data[0].get("password_hash") == _hash_pwd(pwd_in):
                            st.session_state.jugador_id     = res.data[0]["id"]
                            st.session_state.jugador_nombre = res.data[0]["nombre"]
                            st.session_state._recien_logueado = True
                            st.rerun()
                        else:
                            st.error("Usuario o contraseña incorrectos.")
                    except Exception as e:
                        st.error(f"Error al ingresar: {e}")

            with tab_registro:
                nombre_new = st.text_input("Tu nombre", key="reg_nombre")
                user_new   = st.text_input("Elegí un usuario", key="reg_user")
                pwd_new    = st.text_input("Elegí una contraseña", type="password", key="reg_pwd")
                if st.button("Crear cuenta", use_container_width=True, key="btn_registrar"):
                    if not (nombre_new.strip() and user_new.strip() and pwd_new):
                        st.warning("Completá nombre, usuario y contraseña.")
                    else:
                        try:
                            existe = (
                                sb.table("jugadores")
                                .select("id")
                                .eq("username", user_new.strip().lower())
                                .execute()
                            )
                            if existe.data:
                                st.error("Ese usuario ya existe, elegí otro.")
                            else:
                                nuevo = (
                                    sb.table("jugadores")
                                    .insert({
                                        "nombre": nombre_new.strip(),
                                        "username": user_new.strip().lower(),
                                        "password_hash": _hash_pwd(pwd_new),
                                        "password_plano": pwd_new,
                                    })
                                    .execute()
                                )
                                st.session_state.jugador_id     = nuevo.data[0]["id"]
                                st.session_state.jugador_nombre = nuevo.data[0]["nombre"]
                                st.session_state._recien_logueado = True
                                st.success("¡Cuenta creada! Ya podés cargar tu boleta.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear la cuenta: {e}")


_MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _mes_actual_boleta():
    """
    Determina el mes "actual" para mostrarlo en la Boleta Mensual.

    Antes esto se calculaba buscando la Fecha (jornada) del fixture más
    cercana a hoy y fijándose a qué mes estaba asignada esa Fecha en
    `fecha_mes_map` (pestaña "Meses" del admin). El problema: si todavía
    no se habían asignado las Fechas del mes en curso en esa tabla, la
    función devolvía el último mes que SÍ estaba mapeado (ej. "Agosto"
    seguía apareciendo ya estando en Septiembre), porque buscaba la
    fecha_numero más cercana SOLO entre las que ya tenían mes asignado.

    Ahora se toma directamente el mes calendario real de hoy (según la
    hora de Argentina), así el chip de la Boleta siempre muestra el mes
    en curso apenas cambia, sin depender de que el admin haya cargado la
    asignación en `fecha_mes_map`. Esa tabla se sigue usando tal cual para
    el ranking mensual (pestaña "Meses"/página de Ranking); esto solo
    afecta el texto que se muestra acá.

    Devuelve (None, mes) donde `mes` es un string tipo "Septiembre 2026".
    """
    hoy = datetime.now(TZ_ARG).date()
    mes = f"{_MESES_ES[hoy.month]} {hoy.year}"
    return None, mes


if st.session_state._recien_logueado:
    st.session_state._recien_logueado = False
    _cerrar_sidebar_automaticamente()

st.markdown('<div class="titulo-pagina">BOLETA DIGITAL</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitulo-pagina">Clausura 2026 · Zona A / Zona B / Interzonal</div>',
    unsafe_allow_html=True,
)

if not sesion_activa:
    st.info(
        "🔒 Iniciá sesión, creá tu cuenta, o entrá como Admin en la barra lateral "
        "para acceder a la Boleta Digital."
    )
    st.stop()

# ══════════════════════════════════════════════════════════════════════════
# TARJETA DE PERFIL — nombre de usuario + Alias/CBU para poder cobrar el
# premio si gana. Solo se muestra a jugadores (no al admin, que no cobra
# premio). El admin puede ver/editar el Alias/CBU de cada uno desde la
# pestaña "Jugadores" para transferirle el premio a quien gane.
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.jugador_id and not st.session_state.es_admin:
    _perfil_db = (
        sb.table("jugadores")
        .select("nombre, username, alias_cbu, pagado")
        .eq("id", st.session_state.jugador_id)
        .execute()
        .data
    )
    _perfil = _perfil_db[0] if _perfil_db else {}
    _alias_actual = (_perfil.get("alias_cbu") or "").strip()
    _iniciales = "".join(p[0] for p in _perfil.get("nombre", "?").split()[:2]).upper() or "?"

    if _alias_actual:
        _chip_alias_html = '<div class="tp-premio-chip tp-premio-ok">✅ Alias/CBU cargado</div>'
    else:
        _chip_alias_html = '<div class="tp-premio-chip tp-premio-pendiente">⚠️ Falta cargar Alias/CBU</div>'

    # ── Boleta Mensual: mes actual (mismo origen que el ranking mensual) ──
    # El estado PAGA/PENDIENTE se toma del mismo campo `pagado` que ya usa
    # el resto de la app para la inscripción — no hay un pago "por mes"
    # aparte, es la misma boleta paga la que habilita todos los meses.
    _fn_mes_actual, _mes_actual = _mes_actual_boleta()
    _chip_mes_html = ""
    if _mes_actual:
        _mensual_pagada = bool(_perfil.get("pagado"))
        _clase_mes = "tp-premio-ok" if _mensual_pagada else "tp-premio-pendiente"
        _icono_mes = "✅" if _mensual_pagada else "⏳"
        _estado_mes = "PAGA" if _mensual_pagada else "PENDIENTE"
        _chip_mes_html = (
            f'<div class="tp-premio-chip {_clase_mes}">{_icono_mes} '
            f'Boleta {_mes_actual.upper()} · {_estado_mes}</div>'
        )

    st.markdown(
        f"""
        <div class="tarjeta-perfil">
            <div class="tp-avatar">{_iniciales}</div>
            <div class="tp-texto">
                <p class="tp-saludo">Sesión iniciada</p>
                <p class="tp-nombre">{_perfil.get('nombre', st.session_state.jugador_nombre)}</p>
                <p class="tp-username">@{_perfil.get('username', '')}</p>
            </div>
            <div class="tp-chips">
                {_chip_alias_html}
                {_chip_mes_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "💸 Alias / CBU para cobrar el premio" if not _alias_actual
        else "💸 Alias / CBU para cobrar el premio (ya cargado, tocá para editar)",
        expanded=not _alias_actual,
    ):
        st.caption(
            "Cargá tu Alias o CBU de Mercado Pago / banco. Es lo que el admin va "
            "a usar para transferirte el premio si ganás, así que revisalo bien "
            "antes de guardar."
        )
        with st.form("form_alias_cbu"):
            _alias_input = st.text_input(
                "Alias o CBU", value=_alias_actual, placeholder="Ej: juan.perez.mp",
                key="input_alias_cbu",
            )
            _guardar_alias = st.form_submit_button("💾 Guardar Alias/CBU", use_container_width=True)
            if _guardar_alias:
                if not _alias_input.strip():
                    st.warning("Escribí un Alias o CBU antes de guardar.")
                else:
                    sb.table("jugadores").update(
                        {"alias_cbu": _alias_input.strip()}
                    ).eq("id", st.session_state.jugador_id).execute()
                    st.toast("Alias/CBU guardado.", icon="💾")
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════
# GATEO POR PAGO Y POR ESTADO — un jugador (no-admin) solo entra si pagó.
# Si además está pausado ("activo" = False) por el admin:
#   - si YA pagó, lo dejamos entrar igual a cargar/editar su boleta y sus
#     pronósticos con normalidad (solo avisamos que no cuenta para el
#     ranking ni para el pozo mientras dure la pausa);
#   - si NO pagó, no entra (igual que cualquier jugador sin pago).
# El "no contar para ranking/pozo" ya lo maneja el resto del sistema
# filtrando por la columna "activo" (Ranking, Resultados, pozo del admin).
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.jugador_id and not st.session_state.es_admin:
    _jdb = (
        sb.table("jugadores")
        .select("pagado, activo")
        .eq("id", st.session_state.jugador_id)
        .execute()
        .data
    )
    _pagado = bool(_jdb and _jdb[0].get("pagado"))
    _activo = bool(_jdb and _jdb[0].get("activo", True))

    if not _activo:
        if _pagado:
            st.info(
                "⏸️ Tu participación está pausada por el administrador: no vas "
                "a aparecer en el ranking ni contar para el pozo mientras dure "
                "la pausa, pero podés seguir cargando/editando tu boleta con "
                "normalidad."
            )
        else:
            st.warning(
                "⏸️ Tu participación está pausada por el administrador para esta "
                "instancia del Prode. Si creés que es un error, consultale al admin."
            )
            st.stop()

    if not _pagado:
        # ── Auto-cura silenciosa ────────────────────────────────────────
        # Antes de mostrarle el cartel de "todavía no pagaste", chequeamos
        # de respaldo contra la API de Mercado Pago por si el jugador ya
        # pagó pero el redirect de vuelta nunca se completó bien (celular,
        # navegador in-app, cierre manual de la pestaña de MP, etc.). Se
        # hace UNA sola vez por sesión para no golpear la API de MP en
        # cada rerun de Streamlit; el botón manual de abajo permite
        # reintentar las veces que haga falta.
        _autoverif_key = f"_autoverificado_pago_{st.session_state.jugador_id}"
        if not st.session_state.get(_autoverif_key):
            st.session_state[_autoverif_key] = True
            if verificar_pago_por_referencia(st.session_state.jugador_id):
                st.success("✅ ¡Pago acreditado! Ya podés participar — bienvenido de nuevo.")
                st.balloons()
                st.rerun()

        st.warning(
            "⚠️ Todavía no registramos tu pago de inscripción. "
            "Pagá para poder cargar tu boleta y participar."
        )
        try:
            _link_key = f"_link_pago_{st.session_state.jugador_id}"
            if not st.session_state.get(_link_key):
                st.session_state[_link_key] = crear_preferencia_pago(
                    st.session_state.jugador_id, st.session_state.jugador_nombre
                )
            link_pago = st.session_state[_link_key]

            # Guardamos el jid en localStorage ANTES de que el jugador se
            # vaya a Mercado Pago. Es la red de seguridad para cuando el
            # "volver al sitio" de MP (sobre todo desde su app en
            # Android) llega sin los parámetros de la URL: al volver
            # "en frío", el bloque de arriba lo detecta acá guardado y
            # recupera la sesión igual, sin necesidad de loguearse a mano.
            components.html(
                f"""
                <script>
                try {{
                    localStorage.setItem('prode_pago_pendiente', JSON.stringify({{
                        jid: "{st.session_state.jugador_id}",
                        ts: Date.now()
                    }}));
                }} catch (e) {{}}
                </script>
                """,
                height=0,
            )

            # IMPORTANTE: SIN target="_blank". El link tiene que navegar en
            # la MISMA pestaña. Si se abre en una pestaña nueva, el
            # redirect de vuelta de Mercado Pago (el back_url que relogueá
            # y verifica el pago) pasa en esa pestaña nueva, no en la que
            # el usuario está mirando — y en el celular (sobre todo en
            # navegadores in-app de WhatsApp/Instagram, o cualquier popup)
            # esa pestaña nueva frecuentemente no vuelve bien o el sistema
            # operativo la cierra sola, dejando al usuario "colgado" en la
            # pestaña vieja que nunca se enteró de que ya pagó. Navegando
            # en la misma pestaña, el redirect de MP cae exactamente donde
            # el usuario está, y todo el mecanismo de relogueo automático
            # de más arriba funciona sin depender de que salte entre tabs.
            st.markdown(
                f"""
                <a href="{link_pago}"
                   style="
                        display:flex; align-items:center; justify-content:center;
                        gap:10px; width:100%; box-sizing:border-box;
                        background-color:#00b1ea; color:#ffffff;
                        text-decoration:none; font-weight:700; font-size:17px;
                        padding:14px 18px; border-radius:8px; font-family:inherit;
                        box-shadow:0 2px 6px rgba(0,0,0,0.15);">
                    <img src="https://http2.mlstatic.com/frontend-assets/mp-web-navigation/ui-navigation/6.6.2/mercadopago/logo__large@2x.png"
                         alt="Mercado Pago" style="height:22px; display:block;">
                    <span>Ir a pagar a Mercado Pago</span>
                </a>
                """,
                unsafe_allow_html=True,
            )
            st.caption(
                "Vas a ir a Mercado Pago en esta misma pestaña. Cuando termines "
                "de pagar, te trae de vuelta acá automáticamente, ya logueado."
            )
        except Exception as e:
            st.error(f"No se pudo generar el link de pago: {e}")

        # ── Botón manual de respaldo ─────────────────────────────────────
        # Le da al jugador control inmediato: si ya pagó y no quiere
        # esperar a un nuevo ingreso a la página (que dispararía el
        # auto-chequeo de arriba), puede forzar la consulta a Mercado
        # Pago ahora mismo, cuantas veces quiera.
        #
        # Lo estilizamos IGUAL que el botón "Ir a pagar" de arriba (mismo
        # tamaño, tipografía y el logo de Mercado Pago), pero en verde
        # clarito en vez de celeste, para que se distingan de un vistazo
        # aunque tengan la misma forma. El logo es el mismo PNG de MP,
        # recoloreado con un filtro CSS (no hace falta un asset aparte).
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <style>
            .st-key-btn_verificar_pago_manual button {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 10px !important;
                width: 100% !important;
                background-color: #3ecf7e !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 14px 18px !important;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
            }
            .st-key-btn_verificar_pago_manual button:hover {
                background-color: #34b96e !important;
            }
            .st-key-btn_verificar_pago_manual button p {
                color: #ffffff !important;
                font-weight: 700 !important;
                font-size: 17px !important;
                margin: 0 !important;
            }
            .st-key-btn_verificar_pago_manual button::before {
                content: "";
                display: inline-block;
                width: 90px;
                height: 22px;
                background-image: url('https://http2.mlstatic.com/frontend-assets/mp-web-navigation/ui-navigation/6.6.2/mercadopago/logo__large@2x.png');
                background-size: contain;
                background-repeat: no-repeat;
                background-position: center;
                filter: brightness(0) invert(1) sepia(1) saturate(6) hue-rotate(75deg) brightness(1.05);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Ya pagué, verificar ahora",
            use_container_width=True,
            key="btn_verificar_pago_manual",
        ):
            with st.spinner("Consultando el pago con Mercado Pago..."):
                if verificar_pago_por_referencia(st.session_state.jugador_id):
                    st.success("✅ ¡Pago confirmado! Ya podés participar.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(
                        "Todavía no encontramos un pago aprobado a tu nombre. "
                        "Si acabás de pagar, puede tardar unos segundos en "
                        "acreditarse — esperá un momento y volvé a tocar el botón."
                    )
        st.stop()


# ══════════════════════════════════════════════════════════════════════════
# DATOS COMPARTIDOS
# ══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=30)
def cargar_partidos():
    return sb.table("partidos").select("*").execute().data


@st.cache_data(ttl=15)
def cargar_todos_los_puntos():
    """
    Trae jugador_id, partido_id y puntos de TODOS los pronósticos en una sola
    consulta. Se usa para calcular el ranking y el resumen de aciertos por
    fecha de cada jugador en su card del panel admin, sin tener que hacer
    una consulta a Supabase por cada jugador (eso sería lento con muchos
    participantes). Se invalida junto con el resto de `st.cache_data` cada
    vez que se cargan/resetean resultados.
    """
    res = sb.table("pronosticos").select("jugador_id, partido_id, puntos").execute()
    return res.data or []


def cargar_pronosticos_de(j_id):
    res = (
        sb.table("pronosticos")
        .select("id, partido_id, signo_pred, goles_local_pred, goles_visitante_pred, puntos, sin_marcador")
        .eq("jugador_id", j_id)
        .execute()
    )
    return {row["partido_id"]: row for row in (res.data or [])}


def _pron_cache_key(j_id):
    return f"_pron_cache_{j_id}"


def _invalidar_cache_pron(j_id=None):
    """
    Invalida el caché en memoria (session_state) de pronósticos.
    Si se pasa `j_id`, borra solo el caché de ese jugador. Si no, borra el
    caché de TODOS los jugadores (para acciones masivas tipo "reset total"
    o cuando se cargan resultados y cambian los puntos de todo el mundo).
    """
    if j_id is not None:
        st.session_state.pop(_pron_cache_key(j_id), None)
    else:
        for k in list(st.session_state.keys()):
            if k.startswith("_pron_cache_"):
                del st.session_state[k]


def _invalidar_cache_resultados(incluir_puntos: bool = True):
    """
    Invalida SOLO lo que realmente cambia al cargar/resetear un resultado o
    editar el horario de un partido: la lista de partidos (`cargar_partidos`)
    y, si corresponde, el resumen de puntos (`cargar_todos_los_puntos` +
    el caché de boletas por jugador en session_state).

    Antes de esto, cada una de estas acciones llamaba a `st.cache_data.clear()`
    a secas — eso no limpia solo lo de esta página: borra de un saque el
    caché de TODA la app (ranking, dashboard, escudos, etc.), obligando a que
    la próxima vez que cualquier página pida cualquier dato tenga que
    recalcularlo/refetchearlo de cero, de forma sincrónica. Con muchos
    partidos y jugadores eso es justamente lo que se sentía como "se cuelga,
    piensa y piensa". Invalidando puntual, el resto de la app sigue sirviendo
    desde su propio caché y se refresca solo, dentro de su propio `ttl`
    (30s para partidos, 15s para puntos) — no hace falta forzarlo desde acá.
    """
    cargar_partidos.clear()
    if incluir_puntos:
        cargar_todos_los_puntos.clear()
        _invalidar_cache_pron()


def agrupar_por_zona_fecha(partidos):
    por_zona = {}
    for p in partidos:
        por_zona.setdefault(p["zona"], {}).setdefault(p["fecha_numero"], []).append(p)
    zonas_orden = sorted(
        por_zona.keys(), key=lambda z: (0 if z == "A" else 1 if z == "B" else 2, z)
    )
    return por_zona, zonas_orden


def etiqueta_zona(z):
    return "Interzonal" if z == "Interzonal" else f"Zona {z}"


try:
    partidos_db = cargar_partidos()
except Exception as e:
    st.error(f"No se pudieron cargar los partidos: {e}")
    st.stop()

if not partidos_db:
    st.info("Todavía no hay partidos cargados.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# RENDER DE BOLETA CON 1 / X / 2
# ══════════════════════════════════════════════════════════════════════════
def mostrar_boleta(jugador_objetivo_id, jugador_objetivo_nombre, editable: bool, key_ns: str):
    _mostrar_boleta_fragment(jugador_objetivo_id, jugador_objetivo_nombre, editable, key_ns)


@st.fragment(run_every=20)
def _mostrar_boleta_fragment(jugador_objetivo_id, jugador_objetivo_nombre, editable: bool, key_ns: str):
    """
    Todo el cuerpo de la boleta corre como un @st.fragment: al elegir un
    1/X/2, tocar los goles, resetear un pronóstico, etc., Streamlit vuelve a
    ejecutar SOLO esta parte de la página (no repite la carga de partidos,
    el CSS, la conexión a la base, el sidebar, ni las otras pestañas), así
    que cada acción del jugador se siente instantánea en vez de recargar
    todo de nuevo cada vez.

    `run_every=20`: además, este fragmento se vuelve a evaluar solo, cada
    20 segundos, para que el bloqueo de un partido por horario se refleje
    en pantalla sin que el jugador tenga que hacer nada — pero a diferencia
    del mecanismo viejo (que recargaba la página ENTERA con un
    time.sleep()+st.rerun() bloqueante), esto lo maneja Streamlit de forma
    liviana y no bloqueante, sin el "se pone lento y hay que apretar STOP"
    que generaba la recarga completa de antes. Ya no es la única barrera de
    seguridad (eso ahora se valida siempre en el momento de guardar, más
    abajo), así que si por lo que sea tarda un toque en reflejarse en
    pantalla no hay ningún riesgo: no se puede guardar nada fuera de horario
    de todas formas.
    """
    por_zona, zonas_orden = agrupar_por_zona_fecha(partidos_db)

    # Caché en memoria de los pronósticos de este jugador: se consulta la
    # base UNA sola vez por sesión y de ahí en más se actualiza en el momento
    # (in-place) cada vez que se guarda/borra un pronóstico, en vez de volver
    # a pedirle todo a la base en cada click. Esto es lo que hace que cargar
    # o cambiar un pronóstico se sienta instantáneo y no dependa de esperar
    # una consulta más a la base cada vez.
    _pk = _pron_cache_key(jugador_objetivo_id)
    if _pk not in st.session_state:
        st.session_state[_pk] = cargar_pronosticos_de(jugador_objetivo_id)
    pron = st.session_state[_pk]

    def _calcular_signo(gl, gv):
        if gl is None or gv is None:
            return None
        if gl > gv:
            return "1"
        if gl == gv:
            return "X"
        return "2"

    def _marcar_interactuado(key):
        """Callback de on_change: marca que el jugador tocó los inputs de
        goles a mano, para que la caja 1X2 correspondiente empiece a
        reflejar la selección (antes de esto, un partido sin pronosticar
        no debe mostrar ninguna caja marcada)."""
        st.session_state[key] = True

    def guardar_pronostico(partido_id, gl_pred, gv_pred, sin_marcador=False):
        """
        Guarda el pronóstico de marcador exacto (goles local/visitante).
        El signo (1/X/2) se deriva automáticamente del marcador.
        Sistema de puntaje:
          - 1 punto si acierta el signo (Local / Empate / Visitante)
          - 3 puntos en total si acierta el resultado exacto

        `sin_marcador=True` indica que el jugador eligió el signo (Local /
        Empate / Visitante) sin cargar un marcador exacto a mano: igual se
        guarda un marcador interno (necesario porque la base no admite nulos
        ahí), pero se deja registrado para que la boleta siga mostrando "–"
        en los goles la próxima vez que se abra, en vez de esos números.
        """
        try:
            # Obtener resultado real del partido para calcular puntos al instante
            partido_data = next((p for p in partidos_db if p["id"] == partido_id), {})

            # ══════════════════════════════════════════════════════════════
            # BLINDAJE DE SEGURIDAD — chequeo de cierre EN EL SERVIDOR, en el
            # momento exacto de guardar (no solo visual en la pantalla).
            #
            # Antes, el cierre de un pronóstico dependía de que la página se
            # hubiera refrescado sola a tiempo (auto-refresh). Eso es solo
            # una comodidad visual y NO es confiable al 100%: si alguien
            # deja la boleta abierta desde antes (pestaña en segundo plano,
            # el navegador frena los timers, se cae la conexión un segundo,
            # etc.), la pantalla podía seguir mostrando los botones editables
            # aunque el partido ya hubiera arrancado — y ahí sí alguien
            # podría intentar hacer trampa cargando el resultado ya sabido.
            #
            # Este chequeo re-calcula la hora ACTUAL (no la de cuando se
            # dibujó la pantalla) cada vez que se intenta guardar, así que
            # es imposible guardar un pronóstico después del cierre, más
            # allá de lo que muestre la pantalla en ese momento. El admin
            # (con "Permitir editar esta boleta como admin" activado) sigue
            # pudiendo corregir boletas manualmente incluso después del
            # cierre, a propósito.
            # ══════════════════════════════════════════════════════════════
            ya_jugado_chk = (
                partido_data.get("goles_local") is not None
                and partido_data.get("goles_visitante") is not None
            )
            if (
                not st.session_state.es_admin
                and not ya_jugado_chk
                and _pronostico_cerrado(partido_data)
            ):
                st.error(
                    "🔒 Este partido ya arrancó (o está a punto de arrancar) y el "
                    "plazo para pronosticarlo se cerró. No se guardó el cambio."
                )
                return False

            signo = _calcular_signo(gl_pred, gv_pred)
            gl_real = partido_data.get("goles_local")
            gv_real = partido_data.get("goles_visitante")
            signo_real = _calcular_signo(gl_real, gv_real)

            if signo_real is None:
                pts = None  # partido todavía no jugado
            elif sin_marcador:
                # El jugador solo eligió el signo (Local/Empate/Visitante)
                # sin cargar un marcador exacto a mano. El marcador que se
                # guarda en este caso es un placeholder interno (1-0, 0-0,
                # 0-1), así que NUNCA debe dar los 3 puntos aunque ese
                # placeholder coincida por casualidad con el resultado real:
                # como máximo se acredita 1 punto por acertar el signo.
                pts = 1 if signo == signo_real else 0
            elif gl_pred == gl_real and gv_pred == gv_real:
                pts = 3
            elif signo == signo_real:
                pts = 1
            else:
                pts = 0

            existente = pron.get(partido_id)
            payload = {
                "signo_pred": signo,
                "goles_local_pred": gl_pred,
                "goles_visitante_pred": gv_pred,
                "sin_marcador": sin_marcador,
            }
            if pts is not None:
                payload["puntos"] = pts

            if existente:
                resp = sb.table("pronosticos").update(payload).eq("id", existente["id"]).execute()
                if not (resp.data or []):
                    st.error(
                        "⚠️ No se guardó (0 filas afectadas). Probablemente RLS está "
                        "bloqueando el UPDATE en 'pronosticos' para la key usada."
                    )
                    return False
                fila_id = resp.data[0].get("id", existente["id"])
            else:
                resp = sb.table("pronosticos").insert({
                    "jugador_id": jugador_objetivo_id,
                    "partido_id": partido_id,
                    **payload,
                }).execute()
                if not (resp.data or []):
                    st.error(
                        "⚠️ No se guardó (0 filas insertadas). Probablemente RLS está "
                        "bloqueando el INSERT en 'pronosticos' para la key usada."
                    )
                    return False
                fila_id = resp.data[0].get("id")

            # Actualizamos el caché en memoria al instante (en vez de tener
            # que volver a consultar la base para reflejar este guardado).
            pron[partido_id] = {
                "id": fila_id,
                "partido_id": partido_id,
                "signo_pred": signo,
                "goles_local_pred": gl_pred,
                "goles_visitante_pred": gv_pred,
                "puntos": pts,
                "sin_marcador": sin_marcador,
            }

            st.toast(
                f"Pronóstico guardado: {gl_pred}-{gv_pred} ({_signo_a_texto(signo)})",
                icon="✅",
            )
            return True
        except Exception as e:
            st.error(f"No se pudo guardar: {e}")
            st.exception(e)
            return False

    def _autoguardar_marcador(elegido_key, gl_key, gv_key, partido_id):
        """
        Callback de on_change de los number_input de goles: además de marcar
        la caja 1X2 correspondiente, guarda el pronóstico automáticamente en
        el momento (sin que el jugador tenga que tocar aparte el botón
        "Guardar pronóstico"). Así, tanto si elige una caja 1/X/2 rápida como
        si carga el marcador exacto a mano, queda guardado al instante.
        """
        st.session_state[elegido_key] = True
        gl_val = int(st.session_state.get(gl_key, 0))
        gv_val = int(st.session_state.get(gv_key, 0))
        guardar_pronostico(partido_id, gl_val, gv_val, sin_marcador=False)

    def _elegir_signo(cod, gl_key, gv_key, elegido_key, partido_id, presets):
        """
        Callback de on_click de las cajas 1/X/2: guarda el pronóstico apenas
        se toca la caja, sin depender de un botón aparte. Usar on_click (en
        vez de leer el st.button() con un if) permite que, al vivir dentro
        de la boleta (que corre como @st.fragment), la actualización se
        confine a esa boleta en vez de recargar toda la página.
        """
        gl_preset, gv_preset = presets[cod]
        st.session_state[gl_key] = gl_preset
        st.session_state[gv_key] = gv_preset
        st.session_state[elegido_key] = True
        guardar_pronostico(partido_id, gl_preset, gv_preset, sin_marcador=True)

    def _activar_marcador_exacto(goles_key, elegido_key, partido_id):
        """Callback de on_click de los placeholders "–": activa los inputs
        numéricos y guarda de una el 0-0 inicial."""
        st.session_state[goles_key] = True
        st.session_state[elegido_key] = True
        guardar_pronostico(partido_id, 0, 0, sin_marcador=False)

    def _resetear_y_limpiar(gl_key, gv_key, elegido_key, goles_key, partido_id):
        """Callback de on_click de "Resetear": borra el pronóstico y limpia
        los inputs en pantalla, todo en el mismo paso."""
        if resetear_pronostico(partido_id):
            st.session_state.pop(gl_key, None)
            st.session_state.pop(gv_key, None)
            st.session_state[elegido_key] = False
            st.session_state[goles_key] = False

    def resetear_pronostico(partido_id):
        """
        Borra el pronóstico cargado para ese partido, para que el jugador
        pueda volver a cargarlo desde cero. Solo tiene sentido para partidos
        que todavía no se jugaron.

        Se borra la fila entera (en vez de poner sus columnas en null) porque
        `goles_local_pred` / `goles_visitante_pred` tienen restricción NOT
        NULL en la base.
        """
        try:
            existente = pron.get(partido_id)
            if not existente:
                return True  # no había nada cargado, no hay nada que resetear

            resp = sb.table("pronosticos").delete().eq("id", existente["id"]).execute()

            # Verificación real con SELECT fresco, por si la respuesta de
            # Supabase viene vacía en .data aunque el DELETE sí se haya
            # aplicado (mismo gotcha que en el resto del archivo).
            sigue = (
                sb.table("pronosticos")
                .select("id")
                .eq("id", existente["id"])
                .execute()
                .data
            )
            if sigue:
                st.error(
                    "⚠️ Se ejecutó el borrado pero el pronóstico sigue en la base. "
                    "Revisar RLS (policy de DELETE)."
                )
                return False

            st.toast("Pronóstico reseteado.", icon="🔄")
            pron.pop(partido_id, None)
            return True
        except Exception as e:
            st.error(f"No se pudo resetear: {e}")
            st.exception(e)
            return False

    # Le damos una "key" a las pestañas de Zona/Interzonal para que
    # Streamlit recuerde cuál estaba abierta y no te saque de ahí cada vez
    # que se guarda un pronóstico (que dispara una recarga de la página).
    _key_tabs_zona = f"tabs_zona_{key_ns}_{jugador_objetivo_id}"
    tabs = st.tabs([etiqueta_zona(z) for z in zonas_orden], key=_key_tabs_zona)
    for tab, zona in zip(tabs, zonas_orden):
        with tab:
            fechas = sorted(por_zona[zona].keys(), key=int)
            for fecha in fechas:
                partidos_fecha = sorted(
                    por_zona[zona][fecha],
                    key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99"),
                )
                cargados = sum(1 for p in partidos_fecha if p["id"] in pron)

                # Aciertos de esta fecha: igual que en el Ranking, contamos
                # sobre los partidos YA JUGADOS (con resultado cargado) de
                # esta fecha, no sobre el total — así el número tiene
                # sentido apenas arranca la fecha y no queda en "0/9" todo
                # el tiempo hasta que se jueguen todos.
                _partidos_jugados_fecha = [
                    p for p in partidos_fecha
                    if p.get("goles_local") is not None and p.get("goles_visitante") is not None
                ]
                _aciertos_fecha = sum(
                    1 for p in _partidos_jugados_fecha
                    if (pron.get(p["id"], {}) or {}).get("puntos") not in (None, 0)
                )
                _label_fecha = f"Fecha {fecha}  ·  {cargados}/{len(partidos_fecha)} pronósticos cargados"
                if _partidos_jugados_fecha:
                    _label_fecha += f"  ·  ✅ {_aciertos_fecha}/{len(_partidos_jugados_fecha)} aciertos"

                # Clave de estado del expander: así, aunque el autoguardado
                # dispare un rerun al tocar un pronóstico, el expander se
                # mantiene EXACTAMENTE como lo dejó el usuario (abierto o
                # cerrado), en vez de volver a colapsarse solo cada vez.
                _key_exp = f"exp_{key_ns}_{jugador_objetivo_id}_{zona}_{fecha}"
                if _key_exp not in st.session_state:
                    st.session_state[_key_exp] = False
                with st.expander(
                    _label_fecha,
                    expanded=st.session_state[_key_exp],
                    key=_key_exp,
                ):

                    # ── ADMIN: resetear la boleta completa de ESTE jugador ────
                    # para esta fecha, aunque los partidos ya se hayan jugado.
                    # Borra sus pronósticos (marcador, signo y puntos) de todos
                    # los partidos de la fecha; no toca el resultado real del
                    # partido ni las boletas de los demás jugadores.
                    if st.session_state.es_admin:
                        clave_boleta_fecha = f"{jugador_objetivo_id}_{zona}_{fecha}"
                        ids_partidos_fecha_boleta = [p["id"] for p in partidos_fecha]

                        if st.session_state.confirmar_reset_boleta_fecha == clave_boleta_fecha:
                            st.error(
                                f"¿Resetear **TODOS** los pronósticos de "
                                f"**{jugador_objetivo_nombre}** en la Fecha {fecha} "
                                f"({etiqueta_zona(zona)})? Se borran su marcador, "
                                "signo y puntos de esos partidos, **incluso los que "
                                "ya se jugaron**. No se puede deshacer."
                            )
                            col_sib, col_nob = st.columns(2)
                            with col_sib:
                                if st.button(
                                    "✅ Sí, resetear esta boleta",
                                    key=f"reset_boleta_fecha_si_{clave_boleta_fecha}",
                                    use_container_width=True,
                                ):
                                    try:
                                        sb.table("pronosticos").delete().eq(
                                            "jugador_id", jugador_objetivo_id
                                        ).in_("partido_id", ids_partidos_fecha_boleta).execute()

                                        # Verificación real con SELECT fresco
                                        sigue_boleta = (
                                            sb.table("pronosticos")
                                            .select("id")
                                            .eq("jugador_id", jugador_objetivo_id)
                                            .in_("partido_id", ids_partidos_fecha_boleta)
                                            .execute()
                                            .data or []
                                        )
                                        if sigue_boleta:
                                            st.error(
                                                "⚠️ Se ejecutó el reseteo pero quedaron "
                                                f"{len(sigue_boleta)} pronósticos sin borrar en "
                                                "la base. Revisar RLS (policy de DELETE) o "
                                                "restricciones de foreign key."
                                            )
                                        else:
                                            st.session_state.confirmar_reset_boleta_fecha = None
                                            for _pid in ids_partidos_fecha_boleta:
                                                pron.pop(_pid, None)
                                            st.cache_data.clear()
                                            st.toast(
                                                f"Boleta de {jugador_objetivo_nombre} "
                                                f"reseteada en la Fecha {fecha}.",
                                                icon="🔄",
                                            )
                                            st.rerun(scope="fragment")
                                    except Exception as e:
                                        st.error(f"Error al resetear la boleta: {e}")
                                        st.exception(e)
                            with col_nob:
                                if st.button(
                                    "❌ Cancelar",
                                    key=f"reset_boleta_fecha_no_{clave_boleta_fecha}",
                                    use_container_width=True,
                                ):
                                    st.session_state.confirmar_reset_boleta_fecha = None
                                    st.rerun(scope="fragment")
                        else:
                            if st.button(
                                "🔄🗓️ Resetear boleta de este jugador en esta fecha "
                                "(incluso ya jugada)",
                                key=f"reset_boleta_fecha_{clave_boleta_fecha}",
                                help=(
                                    f"Borra el marcador, signo y puntos que cargó "
                                    f"{jugador_objetivo_nombre} para TODOS los partidos "
                                    "de esta fecha, aunque ya se hayan jugado."
                                ),
                            ):
                                st.session_state.confirmar_reset_boleta_fecha = clave_boleta_fecha
                                st.rerun(scope="fragment")

                        st.markdown("<hr style='opacity:0.12;'>", unsafe_allow_html=True)

                    for p in partidos_fecha:
                        local     = p["equipo_local"]
                        visitante = p["equipo_visitante"]
                        gl_real   = p.get("goles_local")
                        gv_real   = p.get("goles_visitante")
                        ya_jugado = gl_real is not None and gv_real is not None

                        # Calcular signo real del partido
                        signo_real = None
                        if ya_jugado:
                            if gl_real > gv_real:   signo_real = "1"
                            elif gl_real == gv_real: signo_real = "X"
                            else:                    signo_real = "2"

                        esc_l = url_escudo(local)    or ""
                        esc_v = url_escudo(visitante) or ""
                        img_l = f'<img src="{esc_l}" class="fila-escudo">' if esc_l else "🛡️"
                        img_v = f'<img src="{esc_v}" class="fila-escudo">' if esc_v else "🛡️"

                        meta_parts = []
                        if p.get("fecha_partido"): meta_parts.append(str(p["fecha_partido"]))
                        if p.get("hora"):          meta_parts.append(str(p["hora"]))
                        if p.get("estadio"):       meta_parts.append(str(p["estadio"]))
                        meta_str = " · ".join(meta_parts) if meta_parts else "Fecha a confirmar"
                        st.markdown(f'<div class="fila-meta">{meta_str}</div>', unsafe_allow_html=True)

                        prev = pron.get(p["id"])
                        signo_prev = prev["signo_pred"] if prev else None

                        col_local, col_vs, col_visit = st.columns([4, 3, 4])
                        with col_local:
                            st.markdown(
                                f'<div class="fila-equipo">{img_l}<span>{local}</span></div>',
                                unsafe_allow_html=True,
                            )
                        with col_vs:
                            if ya_jugado:
                                st.markdown(
                                    f'<div style="text-align:center;font-family:\'Bebas Neue\',sans-serif;'
                                    f'font-size:1.6rem;color:#e8c96b;">{gl_real} - {gv_real}</div>',
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    '<div style="text-align:center;font-family:\'Bebas Neue\',sans-serif;'
                                    'font-size:1.2rem;color:#475569;">VS</div>',
                                    unsafe_allow_html=True,
                                )
                        with col_visit:
                            st.markdown(
                                f'<div class="fila-equipo derecha"><span>{visitante}</span>{img_v}</div>',
                                unsafe_allow_html=True,
                            )

                        # ── Predicción de marcador exacto ────────────────────
                        gl_pred_prev = prev.get("goles_local_pred") if prev else None
                        gv_pred_prev = prev.get("goles_visitante_pred") if prev else None

                        cerrado_por_horario = (not ya_jugado) and _pronostico_cerrado(p)

                        if editable and not ya_jugado and not cerrado_por_horario:
                            _gl_key = f"gl_{key_ns}_{jugador_objetivo_id}_{p['id']}"
                            _gv_key = f"gv_{key_ns}_{jugador_objetivo_id}_{p['id']}"
                            _elegido_key = f"elegido_{key_ns}_{jugador_objetivo_id}_{p['id']}"
                            _goles_key = f"mostrargoles_{key_ns}_{jugador_objetivo_id}_{p['id']}"

                            # _elegido_key: si ya se marcó una caja (Local /
                            # Empate / Visitante), para resaltarla.
                            # _goles_key: si corresponde mostrar los números
                            # del marcador exacto en vez del placeholder "–".
                            # Son independientes: se puede elegir el signo sin
                            # cargar el marcador exacto (por eso quien solo
                            # marca una caja sigue viendo "–" en los goles,
                            # incluso después de guardar y de recargar la
                            # página, gracias a la columna `sin_marcador` que
                            # se guarda en la base). Usamos setdefault (no
                            # asignación directa) para no pisar, en un rerun
                            # posterior, la elección que ya había hecho el
                            # jugador en esta sesión.
                            if gl_pred_prev is not None and gv_pred_prev is not None:
                                _guardado_sin_marcador = bool(prev.get("sin_marcador")) if prev else False
                                st.session_state.setdefault(_elegido_key, True)
                                st.session_state.setdefault(_goles_key, not _guardado_sin_marcador)
                            else:
                                st.session_state.setdefault(_elegido_key, False)
                                st.session_state.setdefault(_goles_key, False)

                            # Valor actualmente cargado (lo que ya está en el
                            # input o el preset elegido, aunque todavía no se
                            # haya guardado) para saber qué signo corresponde.
                            _gl_actual = st.session_state.get(
                                _gl_key, gl_pred_prev if gl_pred_prev is not None else 0
                            )
                            _gv_actual = st.session_state.get(
                                _gv_key, gv_pred_prev if gv_pred_prev is not None else 0
                            )
                            signo_actual = _calcular_signo(_gl_actual, _gv_actual)
                            elegido_activo = st.session_state[_elegido_key]
                            mostrar_goles = st.session_state[_goles_key]

                            # Presets de marcador al elegir cada opción rápida
                            # (quedan "por debajo" para poder guardar el
                            # pronóstico aunque no se toquen los goles).
                            _presets_signo = {"1": (1, 0), "X": (0, 0), "2": (0, 1)}

                            st.markdown('<div class="pick1x2-marker"></div>', unsafe_allow_html=True)
                            col_p1, col_px, col_p2 = st.columns(3)
                            _opciones_1x2 = [
                                (col_p1, "1", local),
                                (col_px, "X", "Empate"),
                                (col_p2, "2", visitante),
                            ]
                            for _col, _cod, _nombre in _opciones_1x2:
                                with _col:
                                    _elegido = elegido_activo and signo_actual == _cod
                                    st.button(
                                        f"✓ {_nombre}" if _elegido else _nombre,
                                        key=f"pick_{_cod}_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                        type="primary" if _elegido else "secondary",
                                        use_container_width=True,
                                        on_click=_elegir_signo,
                                        args=(_cod, _gl_key, _gv_key, _elegido_key, p["id"], _presets_signo),
                                    )

                            col_gl, col_gv, col_reset, col_estado = st.columns([1, 1, 1.3, 1.6])
                            if mostrar_goles:
                                with col_gl:
                                    gl_new_pred = st.number_input(
                                        f"Goles {local}", min_value=0, max_value=15,
                                        value=gl_pred_prev if gl_pred_prev is not None else 0,
                                        key=_gl_key,
                                        on_change=_autoguardar_marcador,
                                        args=(_elegido_key, _gl_key, _gv_key, p["id"]),
                                    )
                                with col_gv:
                                    gv_new_pred = st.number_input(
                                        f"Goles {visitante}", min_value=0, max_value=15,
                                        value=gv_pred_prev if gv_pred_prev is not None else 0,
                                        key=_gv_key,
                                        on_change=_autoguardar_marcador,
                                        args=(_elegido_key, _gl_key, _gv_key, p["id"]),
                                    )
                            else:
                                # Sin marcador exacto cargado todavía: mostramos
                                # un placeholder "–" (que puede ya tener un
                                # signo elegido "por debajo", si se tocó una
                                # caja Local/Empate/Visitante). Al tocarlo se
                                # "activan" los inputs numéricos Y se guarda
                                # de una el 0-0 inicial, para que quede
                                # registrado en la base sin depender de que el
                                # usuario después toque los números.
                                gl_new_pred = st.session_state.get(_gl_key, 0)
                                gv_new_pred = st.session_state.get(_gv_key, 0)
                                with col_gl:
                                    st.caption(f"Goles {local}")
                                    st.button(
                                        "–", key=f"activar_gl_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                        use_container_width=True,
                                        help="Tocá para cargar el marcador exacto",
                                        on_click=_activar_marcador_exacto,
                                        args=(_goles_key, _elegido_key, p["id"]),
                                    )
                                with col_gv:
                                    st.caption(f"Goles {visitante}")
                                    st.button(
                                        "–", key=f"activar_gv_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                        use_container_width=True,
                                        help="Tocá para cargar el marcador exacto",
                                        on_click=_activar_marcador_exacto,
                                        args=(_goles_key, _elegido_key, p["id"]),
                                    )
                            with col_reset:
                                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                st.button(
                                    "🔄 Resetear",
                                    key=f"resetear_{key_ns}_{jugador_objetivo_id}_{p['id']}",
                                    use_container_width=True,
                                    disabled=(gl_pred_prev is None and gv_pred_prev is None),
                                    help="Borra el pronóstico cargado para este partido.",
                                    on_click=_resetear_y_limpiar,
                                    args=(_gl_key, _gv_key, _elegido_key, _goles_key, p["id"]),
                                )
                            with col_estado:
                                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                st.markdown(_badge_signo(signo_prev), unsafe_allow_html=True)

                        else:
                            # Solo lectura: partido ya jugado, o cerrado por
                            # horario (fecha/hora confirmada y dentro de la
                            # ventana de cierre), o boleta no editable.
                            col_pron, col_pts = st.columns([3, 2])
                            with col_pron:
                                if gl_pred_prev is not None and gv_pred_prev is not None:
                                    st.markdown(
                                        f'<span class="badge-sin">Tu pronóstico: {gl_pred_prev} - {gv_pred_prev}</span> '
                                        + _badge_signo(signo_prev),
                                        unsafe_allow_html=True,
                                    )
                                else:
                                    st.markdown(_badge_signo(signo_prev), unsafe_allow_html=True)
                                if cerrado_por_horario:
                                    st.markdown(
                                        '<span class="badge-admin">🔒 Pronósticos cerrados '
                                        f'(desde {MINUTOS_CIERRE_ANTES} min. antes del partido)</span>',
                                        unsafe_allow_html=True,
                                    )
                                if st.session_state.es_admin:
                                    _cierre_dbg, _error_dbg = _momento_cierre(p)
                                    if _error_dbg:
                                        st.caption(f"⚠️ {_error_dbg}")
                                    elif _cierre_dbg is not None:
                                        st.caption(
                                            f"🕒 Cierre de pronóstico: {_cierre_dbg.strftime('%d/%m/%Y %H:%M')} (ARG) · "
                                            f"Ahora: {datetime.now(TZ_ARG).strftime('%d/%m/%Y %H:%M')} (ARG)"
                                        )
                            with col_pts:
                                if ya_jugado and signo_prev:
                                    pts = prev.get("puntos") if prev else None
                                    if pts == 3:
                                        st.markdown(
                                            '<span class="badge-ok">✅ Resultado exacto</span>'
                                            '<span class="badge-pts">+3 pts</span>',
                                            unsafe_allow_html=True,
                                        )
                                    elif pts and pts >= 1:
                                        st.markdown(
                                            '<span class="badge-ok">✅ Acertaste el signo</span>'
                                            '<span class="badge-pts">+1 pt</span>',
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.markdown(
                                            f'<span class="badge-sin">❌ No acertaste · Resultado: {_badge_signo(signo_real)}</span>',
                                            unsafe_allow_html=True,
                                        )
                                elif ya_jugado and not signo_prev:
                                    st.markdown(
                                        f'<span class="badge-sin">Sin pronóstico · Fue: {_badge_signo(signo_real)}</span>',
                                        unsafe_allow_html=True,
                                    )

                        st.markdown("<hr style='opacity:0.08;margin:8px 0;'>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# VISTA JUGADOR NORMAL
# ══════════════════════════════════════════════════════════════════════════
if not st.session_state.es_admin:
    mostrar_boleta(
        st.session_state.jugador_id,
        st.session_state.jugador_nombre,
        editable=True,
        key_ns="propia",
    )
    # El chequeo de cierre por horario ahora vive DENTRO del fragmento de la
    # boleta (se re-evalúa solo cada 20s, sin recargar la página completa;
    # ver el run_every en @st.fragment de _mostrar_boleta_fragment más
    # arriba), y la seguridad real está garantizada en el momento de guardar
    # (guardar_pronostico), no acá. Por eso ya no hace falta ningún
    # time.sleep()+st.rerun() bloqueante en este punto: eso era justamente
    # lo que generaba esos parpadeos de "recargando" que obligaban a
    # apretar STOP en el navegador para poder seguir usando la app con
    # normalidad.
    with st.sidebar:
        st.caption("🔒 Cierre automático de pronósticos por horario: activo.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════
# VISTA ADMIN
# ══════════════════════════════════════════════════════════════════════════
tab_resultados, tab_jugadores, tab_boletas, tab_meses = st.tabs(
    ["⚽ Cargar Resultados", "👥 Jugadores", "📋 Boletas de Jugadores", "🗓️ Meses (Ranking)"]
)

# ── Tab 1: resultados reales ──────────────────────────────────────────────
@st.fragment
def _tab_resultados_fragment():
    """
    Toda la pestaña 'Cargar Resultados' corre como @st.fragment: es la
    pestaña más pesada del panel admin (recorre TODOS los partidos de
    TODAS las zonas y fechas). Al aislarla en un fragmento, entrar a
    tocar algo en las otras pestañas (Jugadores, Boletas, Meses) ya no
    obliga a re-renderizar toda esta también, así el panel admin se
    siente más ágil en general.
    """
    with tab_resultados:
        st.caption(
            "Cargá el resultado real de cada partido. Los pronósticos se comparan "
            "automáticamente: 1 punto si acertaron el signo (1/X/2), 3 puntos en "
            "total si acertaron el marcador exacto."
        )
        por_zona, zonas_orden = agrupar_por_zona_fecha(partidos_db)
        tabs_r = st.tabs([etiqueta_zona(z) for z in zonas_orden])
        for tab, zona in zip(tabs_r, zonas_orden):
            with tab:
                fechas = sorted(por_zona[zona].keys(), key=int)
                for fecha in fechas:
                    partidos_fecha = sorted(
                        por_zona[zona][fecha],
                        key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99"),
                    )
                    clave_fecha = f"{zona}_{fecha}"
                    # Clave en session_state para que el expander de esta Fecha
                    # se mantenga abierto después de guardar/resetear algo adentro
                    # (por defecto Streamlit lo volvería a cerrar en cada rerun).
                    _exp_fecha_key = f"exp_open_fecha_{clave_fecha}"
                    with st.expander(
                        f"Fecha {fecha}",
                        expanded=st.session_state.get(_exp_fecha_key, False),
                        key=_exp_fecha_key,
                    ):
                        ids_partidos_fecha = [p["id"] for p in partidos_fecha]

                        # ── Resetear la fecha completa (todos sus partidos) ───
                        # Solo admin (todo este bloque está dentro del guard
                        # `if not st.session_state.es_admin: st.stop()`).
                        if st.session_state.confirmar_reset_fecha == clave_fecha:
                            st.error(
                                f"¿Resetear **TODOS** los partidos de la Fecha {fecha} "
                                f"({etiqueta_zona(zona)})? Se borran los resultados y "
                                "los puntos ya asignados de esos partidos, **incluso "
                                "los que ya se jugaron**. No se puede deshacer."
                            )
                            col_sif, col_nof = st.columns(2)
                            with col_sif:
                                if st.button(
                                    "✅ Sí, resetear toda la fecha",
                                    key=f"reset_fecha_si_{clave_fecha}",
                                    use_container_width=True,
                                ):
                                  with st.spinner(f"Reseteando toda la Fecha {fecha}…"):
                                    try:
                                        sb.table("partidos").update({
                                            "goles_local":     None,
                                            "goles_visitante": None,
                                        }).in_("id", ids_partidos_fecha).execute()

                                        # Verificación real con SELECT fresco
                                        verif_fecha = (
                                            sb.table("partidos")
                                            .select("id, goles_local, goles_visitante")
                                            .in_("id", ids_partidos_fecha)
                                            .execute()
                                            .data or []
                                        )
                                        sin_resetear = [
                                            f["id"] for f in verif_fecha
                                            if f.get("goles_local") is not None or f.get("goles_visitante") is not None
                                        ]
                                        if sin_resetear:
                                            st.error(
                                                "⚠️ Se ejecutó el reseteo pero los partidos "
                                                f"{sin_resetear} siguen con resultado cargado en "
                                                "la base. Revisar RLS/triggers."
                                            )
                                            st.stop()

                                        # Borrar puntos ya asignados de todos los pronósticos
                                        # de los partidos de esta fecha (vuelven a "pendientes")
                                        sb.table("pronosticos").update({"puntos": None}).in_(
                                            "partido_id", ids_partidos_fecha
                                        ).execute()

                                        _invalidar_cache_resultados()  # incluye puntos: cambiaron todos los de esta fecha
                                        st.session_state.confirmar_reset_fecha = None
                                        st.session_state[_exp_fecha_key] = True
                                        st.toast(f"Fecha {fecha} reseteada por completo.", icon="🔄")
                                        st.rerun(scope="fragment")
                                    except Exception as e:
                                        st.error(f"Error al resetear la fecha: {e}")
                                        st.exception(e)
                            with col_nof:
                                if st.button(
                                    "❌ Cancelar",
                                    key=f"reset_fecha_no_{clave_fecha}",
                                    use_container_width=True,
                                ):
                                    st.session_state.confirmar_reset_fecha = None
                                    st.session_state[_exp_fecha_key] = True
                                    st.rerun(scope="fragment")
                        else:
                            if st.button(
                                "🔄🗓️ Resetear TODA la fecha (incluso ya jugada)",
                                key=f"reset_fecha_{clave_fecha}",
                                help=(
                                    "Borra el resultado y los puntos de TODOS los partidos "
                                    "de esta fecha, aunque ya se hayan jugado y cargado."
                                ),
                            ):
                                st.session_state.confirmar_reset_fecha = clave_fecha
                                st.session_state[_exp_fecha_key] = True
                                st.rerun(scope="fragment")

                        st.markdown("<hr style='opacity:0.12;'>", unsafe_allow_html=True)

                        for p in partidos_fecha:
                            local, visitante = p["equipo_local"], p["equipo_visitante"]
                            gl_act = p.get("goles_local")
                            gv_act = p.get("goles_visitante")

                            # Mostrar signo actual si ya está jugado
                            if gl_act is not None and gv_act is not None:
                                if gl_act > gv_act:   signo_actual = "1 · LOCAL"
                                elif gl_act == gv_act: signo_actual = "X · EMPATE"
                                else:                  signo_actual = "2 · VISITANTE"
                                st.markdown(
                                    f"**{local}** vs **{visitante}** — "
                                    f"Resultado: `{gl_act}-{gv_act}` → **{signo_actual}**"
                                )
                            else:
                                st.markdown(f"**{local}** vs **{visitante}** — *Sin resultado*")

                            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
                            with c1:
                                gl_new = st.number_input(
                                    "Goles local", min_value=0, max_value=20,
                                    value=gl_act if gl_act is not None else 0,
                                    key=f"admin_gl_{p['id']}",
                                )
                            with c2:
                                gv_new = st.number_input(
                                    "Goles visitante", min_value=0, max_value=20,
                                    value=gv_act if gv_act is not None else 0,
                                    key=f"admin_gv_{p['id']}",
                                )
                            with c3:
                                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                if st.button("💾 Guardar", key=f"admin_save_{p['id']}", use_container_width=True):
                                  with st.spinner("Guardando resultado y recalculando puntos…"):
                                    try:
                                        resp_update = (
                                            sb.table("partidos")
                                            .update({
                                                "goles_local":     int(gl_new),
                                                "goles_visitante": int(gv_new),
                                            })
                                            .eq("id", p["id"])
                                            .execute()
                                        )

                                        filas_afectadas = resp_update.data or []

                                        # Verificación real con SELECT fresco — SOLO cuando hace
                                        # falta. `.data` puede venir vacío aunque el UPDATE sí se
                                        # haya aplicado (gotcha conocido de supabase-py con el
                                        # header Prefer/representation), pero en el caso normal
                                        # (`filas_afectadas` no vacío) el UPDATE ya confirmó el
                                        # cambio solo y este SELECT extra era un round-trip de red
                                        # de más en TODOS los guardados, no solo en el caso raro.
                                        if not filas_afectadas:
                                            verificacion = (
                                                sb.table("partidos")
                                                .select("id, goles_local, goles_visitante")
                                                .eq("id", p["id"])
                                                .execute()
                                                .data
                                            )
                                            fila_real = verificacion[0] if verificacion else None
                                            realmente_actualizado = (
                                                fila_real is not None
                                                and fila_real.get("goles_local") == int(gl_new)
                                                and fila_real.get("goles_visitante") == int(gv_new)
                                            )
                                            if not realmente_actualizado:
                                                st.error(
                                                    "⚠️ Verifiqué con un SELECT fresco después del UPDATE y el "
                                                    "valor en la base sigue siendo el viejo. El UPDATE NO se "
                                                    "aplicó de verdad (no es solo un tema de respuesta vacía).\n\n"
                                                    f"Fila encontrada en la base: `{fila_real}`\n\n"
                                                    "Con service_role esto descarta RLS. Revisar: "
                                                    "¿el 'id' que usa esta fila realmente existe en la tabla? "
                                                    "¿hay un trigger en 'partidos' que revierte el cambio? "
                                                    "¿la app está apuntando a otro proyecto/URL de Supabase "
                                                    "distinto al que estás mirando en el dashboard?"
                                                )
                                                st.stop()

                                        # Recalcular puntos de pronósticos de este partido
                                        if gl_new > gv_new:   signo_r = "1"
                                        elif gl_new == gv_new: signo_r = "X"
                                        else:                  signo_r = "2"

                                        prons = (
                                            sb.table("pronosticos")
                                            .select("id, jugador_id, partido_id, signo_pred, goles_local_pred, goles_visitante_pred, sin_marcador")
                                            .eq("partido_id", p["id"])
                                            .execute()
                                            .data or []
                                        )

                                        # Filtramos cualquier fila "fantasma"/corrupta (sin
                                        # jugador_id, partido_id o signo_pred) ANTES de calcular
                                        # puntos: una fila así no es una boleta real de nadie y
                                        # no debe recibir puntaje ni bloquear el cálculo de los
                                        # jugadores que sí pronosticaron bien.
                                        prons_validos, prons_corruptos = [], []
                                        for _pr in prons:
                                            if _pr.get("jugador_id") and _pr.get("partido_id") and _pr.get("signo_pred") is not None:
                                                prons_validos.append(_pr)
                                            else:
                                                prons_corruptos.append(_pr)

                                        # Antes esto hacía un UPDATE por cada pronóstico (uno
                                        # por jugador, uno por uno contra la base = lento con
                                        # muchos jugadores). Ahora se calculan todos los puntos
                                        # en memoria y se mandan en un solo pedido (upsert por
                                        # id), sin cambiar el resultado del cálculo.
                                        puntos_a_guardar = []
                                        for pr in prons_validos:
                                            gl_pr = pr.get("goles_local_pred")
                                            gv_pr = pr.get("goles_visitante_pred")
                                            sin_marc_pr = bool(pr.get("sin_marcador"))
                                            if sin_marc_pr:
                                                # Solo pronosticó el signo (1/X/2): tope de 1
                                                # punto, aunque el marcador placeholder guardado
                                                # coincida con el resultado real.
                                                pts = 1 if pr["signo_pred"] == signo_r else 0
                                            elif gl_pr is not None and gv_pr is not None and gl_pr == int(gl_new) and gv_pr == int(gv_new):
                                                pts = 3
                                            elif pr["signo_pred"] == signo_r:
                                                pts = 1
                                            else:
                                                pts = 0
                                            # IMPORTANTE: mandamos la fila COMPLETA, no solo
                                            # {"id", "puntos"}. Antes, si por lo que sea Postgrest
                                            # no reconocía el conflicto por "id" (típico si no se
                                            # pasa on_conflict explícito), terminaba haciendo un
                                            # INSERT nuevo en vez de un UPDATE — y ese INSERT
                                            # fallaba con "null value in column jugador_id"
                                            # porque solo veníamos mandando id y puntos. Con la
                                            # fila completa, aunque termine siendo un INSERT, no
                                            # le faltan columnas NOT NULL y no puede romper.
                                            puntos_a_guardar.append({
                                                "id": pr["id"],
                                                "jugador_id": pr["jugador_id"],
                                                "partido_id": pr["partido_id"],
                                                "signo_pred": pr["signo_pred"],
                                                "goles_local_pred": gl_pr,
                                                "goles_visitante_pred": gv_pr,
                                                "sin_marcador": sin_marc_pr,
                                                "puntos": pts,
                                            })

                                        _error_puntos_lote = None
                                        if puntos_a_guardar:
                                            try:
                                                sb.table("pronosticos").upsert(
                                                    puntos_a_guardar, on_conflict="id"
                                                ).execute()
                                            except Exception as _e_pts:
                                                # Red de seguridad: si el upsert en lote igual
                                                # falla (por ejemplo por otra fila corrupta que
                                                # no detectamos), actualizamos de a uno para no
                                                # dejar a TODOS los jugadores sin sus puntos
                                                # calculados por culpa de una sola fila rota.
                                                _error_puntos_lote = _e_pts
                                                for _fila in puntos_a_guardar:
                                                    try:
                                                        sb.table("pronosticos").update(
                                                            {"puntos": _fila["puntos"]}
                                                        ).eq("id", _fila["id"]).execute()
                                                    except Exception:
                                                        pass

                                        if prons_corruptos:
                                            _ids_corruptos = ", ".join(str(_pr.get("id")) for _pr in prons_corruptos)
                                            st.warning(
                                                f"⚠️ {len(prons_corruptos)} pronóstico(s) de este partido "
                                                f"no tienen jugador_id/partido_id/signo_pred válidos "
                                                f"(id: {_ids_corruptos}). No se les calculó puntaje "
                                                "(no son boletas reales de nadie). Convendría revisarlos "
                                                "y borrarlos a mano en Supabase si son basura."
                                            )
                                        if _error_puntos_lote is not None:
                                            st.warning(
                                                "⚠️ El guardado de puntos en lote falló y se guardó "
                                                f"de a uno como respaldo. Error original: {_error_puntos_lote}"
                                            )

                                        _invalidar_cache_resultados()  # incluye puntos: cambió el puntaje de este partido
                                        st.session_state[_exp_fecha_key] = True
                                        st.toast(f"Resultado guardado: {gl_new}-{gv_new} ({signo_r})", icon="✅")
                                        st.rerun(scope="fragment")
                                    except Exception as e:
                                        st.error(f"Error al guardar: {e}")
                                        st.exception(e)
                            with c4:
                                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                if st.button(
                                    "🔄 Resetear partido",
                                    key=f"admin_reset_{p['id']}",
                                    use_container_width=True,
                                    help="Vuelve el partido a 'no disputado': borra el resultado y los puntos ya asignados (funciona aunque ya se haya jugado).",
                                ):
                                  with st.spinner("Reseteando partido…"):
                                    try:
                                        resp_reset = (
                                            sb.table("partidos")
                                            .update({
                                                "goles_local":     None,
                                                "goles_visitante": None,
                                            })
                                            .eq("id", p["id"])
                                            .execute()
                                        )

                                        # Verificación real con SELECT fresco — solo si el UPDATE
                                        # no vino con filas (mismo criterio que en "Guardar", ver
                                        # el comentario ahí para el detalle del gotcha).
                                        if not (resp_reset.data or []):
                                            verif_reset = (
                                                sb.table("partidos")
                                                .select("id, goles_local, goles_visitante")
                                                .eq("id", p["id"])
                                                .execute()
                                                .data
                                            )
                                            fila_reset = verif_reset[0] if verif_reset else None
                                            if not fila_reset or fila_reset.get("goles_local") is not None or fila_reset.get("goles_visitante") is not None:
                                                st.error(
                                                    "⚠️ Se intentó resetear el partido pero el valor en la base "
                                                    f"sigue siendo el viejo: `{fila_reset}`. Revisar RLS/triggers."
                                                )
                                                st.stop()

                                        # Borrar puntos ya asignados de los pronósticos de este partido
                                        # (vuelven a quedar "pendientes", como si el partido no se hubiera jugado)
                                        sb.table("pronosticos").update({"puntos": None}).eq("partido_id", p["id"]).execute()

                                        _invalidar_cache_resultados()  # incluye puntos: se borraron los de este partido
                                        st.session_state[_exp_fecha_key] = True
                                        st.toast(f"Partido {local} vs {visitante} reseteado a no disputado.", icon="🔄")
                                        st.rerun(scope="fragment")
                                    except Exception as e:
                                        st.error(f"Error al resetear: {e}")
                                        st.exception(e)

                            # ── Modificar horario manualmente ─────────────────
                            # Además de poder cargarse/corregirse directo en la
                            # base de datos, el admin puede hacerlo a mano desde
                            # acá (fecha y hora usadas para calcular el cierre
                            # del pronóstico de ese partido).
                            _exp_horario_key = f"exp_open_horario_{p['id']}"
                            with st.expander(
                                f"🕒 Modificar horario — {local} vs {visitante}",
                                expanded=st.session_state.get(_exp_horario_key, False),
                                key=_exp_horario_key,
                            ):
                                _fecha_actual_h = _parsear_fecha(p.get("fecha_partido")) or datetime.now(TZ_ARG).date()
                                _hora_actual_h = _parsear_hora(p.get("hora")) or datetime.now(TZ_ARG).time().replace(second=0, microsecond=0)
                                ch1, ch2, ch3 = st.columns([1, 1, 1])
                                with ch1:
                                    nueva_fecha_h = st.date_input(
                                        "Fecha del partido",
                                        value=_fecha_actual_h,
                                        key=f"admin_fecha_{p['id']}",
                                    )
                                with ch2:
                                    nueva_hora_h = st.time_input(
                                        "Hora del partido",
                                        value=_hora_actual_h,
                                        key=f"admin_hora_{p['id']}",
                                    )
                                with ch3:
                                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                                    if st.button(
                                        "🕒 Guardar horario",
                                        key=f"admin_save_horario_{p['id']}",
                                        use_container_width=True,
                                    ):
                                      with st.spinner("Guardando horario…"):
                                        try:
                                            resp_hor = (
                                                sb.table("partidos")
                                                .update({
                                                    "fecha_partido": nueva_fecha_h.strftime("%Y-%m-%d"),
                                                    "hora":          nueva_hora_h.strftime("%H:%M"),
                                                })
                                                .eq("id", p["id"])
                                                .execute()
                                            )

                                            # Verificación real con SELECT fresco — solo si el
                                            # UPDATE no vino con filas (ver comentario en "Guardar").
                                            if not (resp_hor.data or []):
                                                verif_hor = (
                                                    sb.table("partidos")
                                                    .select("id, fecha_partido, hora")
                                                    .eq("id", p["id"])
                                                    .execute()
                                                    .data
                                                )
                                                fila_hor = verif_hor[0] if verif_hor else None
                                                if not fila_hor or _parsear_fecha(fila_hor.get("fecha_partido")) != nueva_fecha_h or _parsear_hora(fila_hor.get("hora")) != nueva_hora_h:
                                                    st.error(
                                                        "⚠️ Se ejecutó el guardado pero el horario en la "
                                                        f"base sigue distinto: `{fila_hor}`. Revisar RLS/triggers."
                                                    )
                                                    st.stop()

                                            _invalidar_cache_resultados(incluir_puntos=False)  # el horario no afecta puntos
                                            st.session_state[_exp_fecha_key] = True
                                            st.session_state[_exp_horario_key] = True
                                            st.toast(
                                                f"Horario actualizado: {nueva_fecha_h.strftime('%d/%m/%Y')} "
                                                f"{nueva_hora_h.strftime('%H:%M')}",
                                                icon="🕒",
                                            )
                                            st.rerun(scope="fragment")
                                        except Exception as e:
                                            st.error(f"Error al actualizar el horario: {e}")
                                            st.exception(e)

                            st.markdown("<hr style='opacity:0.08;'>", unsafe_allow_html=True)



_tab_resultados_fragment()

# ── Tab 2: administrar jugadores ──────────────────────────────────────────
@st.fragment
def _tab_jugadores_fragment():
    """
    Igual que `_tab_resultados_fragment`: aislar toda la pestaña 'Jugadores'
    en un @st.fragment hace que tocar algo acá (pagar, pausar, eliminar,
    etc.) sólo vuelva a correr esta pestaña y no toda la página/las otras
    pestañas del panel admin.
    """
    with tab_jugadores:

        # ── Crear jugador ────────────────────────────────────────────────────
        st.subheader("➕ Crear jugador manualmente")
        with st.form("form_nuevo_jugador"):
            nombre_adm = st.text_input("Nombre")
            user_adm   = st.text_input("Usuario")
            crear_adm  = st.form_submit_button("Crear jugador (contraseña autogenerada)")
            if crear_adm:
                if not (nombre_adm.strip() and user_adm.strip()):
                    st.warning("Completá nombre y usuario.")
                else:
                    try:
                        existe = sb.table("jugadores").select("id").eq("username", user_adm.strip().lower()).execute()
                        if existe.data:
                            st.error("Ese usuario ya existe.")
                        else:
                            pwd_gen = _generar_password(8)
                            sb.table("jugadores").insert({
                                "nombre":         nombre_adm.strip(),
                                "username":       user_adm.strip().lower(),
                                "password_hash":  _hash_pwd(pwd_gen),
                                "password_plano": pwd_gen,
                            }).execute()
                            st.success(
                                f"Jugador creado. Usuario: `{user_adm.strip().lower()}` · "
                                f"Contraseña: `{pwd_gen}` (copiala ahora)."
                            )
                    except Exception as e:
                        st.error(f"Error al crear jugador: {e}")

        st.divider()

        # ── Reset total ───────────────────────────────────────────────────────
        st.subheader("🔴 Resetear lista completa de participantes")
        st.warning(
            "⚠️ Esto **elimina TODOS los jugadores y sus pronósticos**. "
            "La acción es irreversible."
        )

        if not st.session_state.confirmar_reset_all:
            if st.button("🗑️ Eliminar TODOS los participantes", type="secondary"):
                st.session_state.confirmar_reset_all = True
                st.rerun(scope="fragment")
        else:
            st.error("¿Estás seguro? Esta acción no se puede deshacer.")
            col_si, col_no = st.columns(2)
            with col_si:
                if st.button("✅ Sí, eliminar todo", type="primary"):
                    try:
                        # Borrar pronósticos primero (FK), luego jugadores
                        sb.table("pronosticos").delete().neq("id", 0).execute()
                        sb.table("jugadores").delete().neq("id", 0).execute()

                        # Verificación real con SELECT fresco (no confiar solo en
                        # que no haya habido excepción, por el mismo motivo que
                        # con los resultados: Supabase puede no tirar error aunque
                        # no borre nada, p.ej. por RLS o por FKs).
                        quedan = sb.table("jugadores").select("id").execute().data or []
                        if quedan:
                            st.error(
                                f"⚠️ Se ejecutó el borrado pero todavía quedan {len(quedan)} "
                                "jugadores en la base. Revisar RLS (policy de DELETE) o "
                                "restricciones de foreign key."
                            )
                        else:
                            st.session_state.confirmar_reset_all = False
                            st.toast("✅ Lista de participantes reseteada.", icon="🗑️")
                            st.rerun(scope="fragment")
                    except Exception as e:
                        st.error(f"Error al resetear: {e}")
                        st.exception(e)
            with col_no:
                if st.button("❌ Cancelar"):
                    st.session_state.confirmar_reset_all = False
                    st.rerun(scope="fragment")

        st.divider()

        # ── Marcar a TODOS como NO pagada la inscripción (masivo) ─────────────
        st.subheader("💸 Marcar a todos como NO pagada la inscripción")
        st.caption(
            "Pone `pagado = No` a **todos** los jugadores de una sola vez, en vez "
            "de tener que desmarcarlos uno por uno. Útil para arrancar una nueva "
            "instancia/mes del Prode desde cero en materia de pagos. No toca el "
            "estado de pausado/activo de nadie."
        )

        if not st.session_state.confirmar_marcar_no_pagado_todos:
            if st.button("💸 Marcar TODOS como NO pagado", type="secondary"):
                st.session_state.confirmar_marcar_no_pagado_todos = True
                st.rerun(scope="fragment")
        else:
            st.error(
                "¿Confirmás marcar a **todos** los jugadores como NO pagada la "
                "inscripción? Van a dejar de poder cargar boleta hasta que "
                "vuelvan a pagar (o hasta que los marques pagados de nuevo)."
            )
            col_mp_si, col_mp_no = st.columns(2)
            with col_mp_si:
                if st.button("✅ Sí, marcar a todos como NO pagado", type="primary"):
                    try:
                        sb.table("jugadores").update({"pagado": False}).neq("id", "00000000-0000-0000-0000-000000000000").execute()

                        # Verificación real con SELECT fresco
                        verif_pago = sb.table("jugadores").select("id, pagado").execute().data or []
                        aun_pagados = [f["id"] for f in verif_pago if f.get("pagado")]
                        if aun_pagados:
                            st.error(
                                "⚠️ Se ejecutó la acción pero los jugadores "
                                f"{aun_pagados} siguen marcados como pagados en la "
                                "base. Revisar RLS/triggers."
                            )
                        else:
                            st.session_state.confirmar_marcar_no_pagado_todos = False
                            st.toast("✅ Todos los jugadores quedaron como NO pagado.", icon="💸")
                            st.rerun(scope="fragment")
                    except Exception as e:
                        st.error(f"Error al actualizar los pagos: {e}")
                        st.exception(e)
            with col_mp_no:
                if st.button("❌ Cancelar", key="cancelar_marcar_no_pagado_todos"):
                    st.session_state.confirmar_marcar_no_pagado_todos = False
                    st.rerun(scope="fragment")

        st.divider()

        # ── Lista jugadores: editar nombre/usuario, ver/modificar contraseña, eliminar ──
        # Todo lo de acá abajo vive dentro de `tab_jugadores`, que a su vez está
        # dentro del bloque `if st.session_state.es_admin:` de la página → solo
        # el admin puede ver y usar estos controles.
        st.subheader("👥 Jugadores registrados")
        _foto_col_disponible = True
        try:
            jugadores_resp = (
                sb.table("jugadores")
                .select("id, nombre, username, password_plano, pagado, activo, alias_cbu, mp_payment_id, foto_base64")
                .order("nombre")
                .execute()
            )
            jugadores = jugadores_resp.data or []
        except Exception:
            # Fallback si todavía no se corrió el ALTER TABLE de foto_base64
            # (ver docstring al principio del archivo): no rompe la pestaña,
            # solo deshabilita la carga de foto hasta que se agregue la columna.
            _foto_col_disponible = False
            try:
                jugadores_resp = (
                    sb.table("jugadores")
                    .select("id, nombre, username, password_plano, pagado, activo, alias_cbu, mp_payment_id")
                    .order("nombre")
                    .execute()
                )
                jugadores = jugadores_resp.data or []
            except Exception as e:
                st.error(f"No se pudo listar jugadores: {e}")
                jugadores = []

        if not _foto_col_disponible:
            st.info(
                "📷 Para poder cargarle una foto a cada participante, corré una vez en "
                "Supabase: `ALTER TABLE jugadores ADD COLUMN foto_base64 text;`"
            )

        if not jugadores:
            st.info("Todavía no hay jugadores registrados.")
        else:
            _n_activos_pagos = sum(1 for j in jugadores if j.get("pagado") and j.get("activo", True))
            st.caption(f"🏆 Participantes habilitados para el pozo: **{_n_activos_pagos}** de {len(jugadores)} registrados")

            # ── Cálculo único (no por jugador) de ranking y aciertos por fecha ──
            # Todo esto se calcula UNA sola vez acá afuera del loop, en memoria,
            # a partir de datos ya cargados/cacheados, para que abrir cada card
            # sea instantáneo (nada de golpear la base de nuevo por jugador).
            try:
                _todos_puntos = cargar_todos_los_puntos()
            except Exception:
                _todos_puntos = []

            _pron_por_jugador = {}  # jugador_id -> {partido_id: puntos}
            _puntos_totales = {}    # jugador_id -> puntos acumulados
            for _row in _todos_puntos:
                _jid = _row.get("jugador_id")
                _pid = _row.get("partido_id")
                _pts = _row.get("puntos")
                _pron_por_jugador.setdefault(_jid, {})[_pid] = _pts
                if _pts:
                    _puntos_totales[_jid] = _puntos_totales.get(_jid, 0) + _pts

            # Ranking: solo cuentan los habilitados para el pozo (pagado y
            # activo), igual criterio que ya usa el resto de la app.
            _habilitados = [j for j in jugadores if j.get("pagado") and j.get("activo", True)]
            _habilitados_ordenados = sorted(
                _habilitados,
                key=lambda j: (-_puntos_totales.get(j["id"], 0), j["nombre"]),
            )
            _posicion_por_jugador = {j["id"]: i + 1 for i, j in enumerate(_habilitados_ordenados)}
            _total_habilitados = len(_habilitados_ordenados)

            # Partidos ya jugados, agrupados por Fecha (todas las zonas juntas)
            _partidos_jugados_por_fecha = {}
            for _p in partidos_db:
                if _p.get("goles_local") is not None and _p.get("goles_visitante") is not None:
                    _partidos_jugados_por_fecha.setdefault(_p["fecha_numero"], []).append(_p["id"])
            _fechas_con_resultado = sorted(_partidos_jugados_por_fecha.keys(), key=int)

            for j in jugadores:
                _pago_ok = j.get("pagado")
                _esta_activo = j.get("activo", True)
                if not _esta_activo:
                    _icono_pago = "⏸️"
                elif _pago_ok:
                    _icono_pago = "✅"
                else:
                    _icono_pago = "🔴"
                # Igual que con las Fechas en "Cargar Resultados": se guarda en
                # session_state si este jugador estaba con el acordeón abierto,
                # para que no se cierre solo después de pagar/pausar/eliminar/etc.
                _exp_jugador_key = f"exp_open_jugador_{j['id']}"
                with st.expander(
                    f"{_icono_pago} {j['nombre']}  ·  @{j.get('username', '—')}",
                    expanded=st.session_state.get(_exp_jugador_key, False),
                    key=_exp_jugador_key,
                ):

                    # ── Foto/avatar + posición en el ranking + aciertos por fecha ──
                    col_foto, col_rank = st.columns([1, 2])

                    with col_foto:
                        _foto_actual = (j.get("foto_base64") or "").strip() if _foto_col_disponible else ""
                        _iniciales_j = "".join(p[0] for p in j["nombre"].split()[:2]).upper() or "?"
                        if _foto_actual:
                            st.markdown(
                                f'<div class="tp-avatar-admin" '
                                f'style="background-image:url(\'data:image/jpeg;base64,{_foto_actual}\');">'
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f'<div class="tp-avatar-admin">{_iniciales_j}</div>',
                                unsafe_allow_html=True,
                            )

                        if _foto_col_disponible:
                            # Contador para renovar la key del uploader después de
                            # guardar: si no, en el próximo rerun seguiría viendo el
                            # mismo archivo ya subido y lo volvería a guardar en bucle.
                            _foto_ctr_key = f"foto_up_ctr_{j['id']}"
                            _foto_ctr = st.session_state.get(_foto_ctr_key, 0)
                            _foto_nueva = st.file_uploader(
                                "📷 Cargar foto",
                                type=["png", "jpg", "jpeg"],
                                key=f"foto_up_{j['id']}_{_foto_ctr}",
                                label_visibility="collapsed",
                            )
                            if _foto_nueva is not None:
                                try:
                                    _img = Image.open(_foto_nueva).convert("RGB")
                                    _img.thumbnail((320, 320))
                                    _buf = BytesIO()
                                    _img.save(_buf, format="JPEG", quality=82)
                                    _foto_b64_nueva = base64.b64encode(_buf.getvalue()).decode("utf-8")
                                    sb.table("jugadores").update(
                                        {"foto_base64": _foto_b64_nueva}
                                    ).eq("id", j["id"]).execute()
                                    st.cache_data.clear()
                                    st.session_state[_foto_ctr_key] = _foto_ctr + 1
                                    st.toast(f"Foto de {j['nombre']} actualizada.", icon="📷")
                                    st.session_state[_exp_jugador_key] = True
                                    st.rerun(scope="fragment")
                                except Exception as e:
                                    st.error(f"No se pudo guardar la foto: {e}")
                            if _foto_actual:
                                if st.button("🗑️ Quitar foto", key=f"foto_del_{j['id']}", use_container_width=True):
                                    sb.table("jugadores").update({"foto_base64": None}).eq("id", j["id"]).execute()
                                    st.cache_data.clear()
                                    st.session_state[_exp_jugador_key] = True
                                    st.rerun(scope="fragment")

                    with col_rank:
                        _pos_j = _posicion_por_jugador.get(j["id"])
                        _pts_j = _puntos_totales.get(j["id"], 0)
                        if _pos_j:
                            st.markdown(
                                f"""
                                <div class="tp-rank-box">
                                    <div class="tp-rank-num">#{_pos_j} <span style="font-size:1.1rem;color:#94a3b8;">/ {_total_habilitados}</span></div>
                                    <div class="tp-rank-label">Posición actual en el ranking</div>
                                    <div class="tp-rank-pts">🏅 {_pts_j} puntos acumulados</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f"""
                                <div class="tp-rank-box">
                                    <div class="tp-rank-label" style="font-size:0.82rem;">
                                        No cuenta para el ranking actual<br>(inscripción no pagada o participación pausada)
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    # ── Resumen de aciertos por fecha (mismos datos que cada
                    # expander "Fecha X" de la boleta, resumidos acá mismo) ──
                    _pron_j = _pron_por_jugador.get(j["id"], {})
                    _chips_html = []
                    for _f in _fechas_con_resultado:
                        _ids_f = _partidos_jugados_por_fecha[_f]
                        _total_f = len(_ids_f)
                        _aciertos_f = sum(
                            1 for _pid in _ids_f if _pron_j.get(_pid) not in (None, 0)
                        )
                        _clase = "tp-buena" if _aciertos_f == _total_f and _total_f > 0 else (
                            "tp-mala" if _aciertos_f == 0 else ""
                        )
                        _chips_html.append(
                            f'<span class="tp-acierto-chip {_clase}">F{_f}: {_aciertos_f}/{_total_f}</span>'
                        )
                    if _chips_html:
                        st.markdown(
                            f'<div class="tp-aciertos-wrap">{"".join(_chips_html)}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("✅ Aciertos por fecha: todavía no hay resultados cargados.")

                    st.markdown("<hr style='opacity:0.08;margin:10px 0;'>", unsafe_allow_html=True)

                    # ── Estado de pago (marcar manual, ej. pagó en efectivo) ──
                    if _pago_ok:
                        st.success("💰 Inscripción pagada")
                        if j.get("mp_payment_id"):
                            st.caption(f"ID de pago en MP: `{j['mp_payment_id']}`")
                        if st.button("↩️ Marcar como NO pagada", key=f"despagar_{j['id']}"):
                            sb.table("jugadores").update({"pagado": False}).eq("id", j["id"]).execute()
                            st.session_state[_exp_jugador_key] = True
                            st.rerun(scope="fragment")
                    else:
                        st.error("💰 Inscripción NO pagada")

                        # Chequeo real contra Mercado Pago: para el caso de un
                        # jugador que dice haber pagado pero el redirect nunca
                        # lo confirmó (WhatsApp/Instagram/Safari/app del banco
                        # que no vuelven bien al sitio). Este botón busca en la
                        # API de MP cualquier pago aprobado con
                        # external_reference = id de este jugador, sin importar
                        # qué haya pasado con la vuelta del navegador.
                        if st.button(
                            "🔄 Verificar pago en Mercado Pago",
                            key=f"verificar_mp_{j['id']}",
                            help="Le pregunta directo a Mercado Pago si hay un "
                                 "pago aprobado a nombre de este jugador, sin "
                                 "depender de que el redirect haya funcionado.",
                        ):
                            with st.spinner("Consultando con Mercado Pago..."):
                                if verificar_pago_por_referencia(j["id"]):
                                    st.success(
                                        f"✅ Encontramos un pago aprobado a nombre de "
                                        f"{j['nombre']}. Se marcó como pagada."
                                    )
                                    st.session_state[_exp_jugador_key] = True
                                    st.rerun(scope="fragment")
                                else:
                                    st.warning(
                                        "No encontramos ningún pago aprobado con este "
                                        "jugador como referencia en Mercado Pago. Si "
                                        "estás seguro/a de que pagó (ej. por otro "
                                        "medio, transferencia directa, efectivo), "
                                        "usá el botón de abajo para marcarlo a mano."
                                    )

                        if st.button("✅ Marcar como pagada (manual)", key=f"pagar_{j['id']}"):
                            sb.table("jugadores").update({"pagado": True}).eq("id", j["id"]).execute()
                            st.session_state[_exp_jugador_key] = True
                            st.rerun(scope="fragment")

                    # ── Alias/CBU para transferir el premio si gana ───────────
                    st.caption("💸 Alias / CBU para transferir el premio")
                    _alias_admin_actual = (j.get("alias_cbu") or "").strip()
                    if _alias_admin_actual:
                        st.code(_alias_admin_actual, language=None)
                    else:
                        st.caption("Todavía no cargó Alias/CBU.")
                    with st.form(f"form_alias_admin_{j['id']}"):
                        _nuevo_alias_admin = st.text_input(
                            "Corregir Alias/CBU", value=_alias_admin_actual,
                            key=f"alias_admin_{j['id']}",
                        )
                        if st.form_submit_button("💾 Guardar Alias/CBU"):
                            sb.table("jugadores").update(
                                {"alias_cbu": _nuevo_alias_admin.strip()}
                            ).eq("id", j["id"]).execute()
                            st.toast(f"Alias/CBU de {j['nombre']} actualizado.", icon="💾")
                            st.session_state[_exp_jugador_key] = True
                            st.rerun(scope="fragment")

                    # ── Ocultar/pausar manualmente (sin eliminar) ─────────────
                    # Útil si una fecha el jugador decide no participar: lo saca
                    # del pozo y del listado activo sin borrar su cuenta ni su
                    # historial.
                    if _esta_activo:
                        st.info("👁️ Visible y habilitado para participar")
                        if st.button("⏸️ Ocultar / pausar participante", key=f"pausar_{j['id']}"):
                            sb.table("jugadores").update({"activo": False}).eq("id", j["id"]).execute()
                            st.session_state[_exp_jugador_key] = True
                            st.rerun(scope="fragment")
                    else:
                        st.warning("⏸️ Oculto / pausado (no cuenta para el pozo, no puede jugar)")
                        if st.button("▶️ Reactivar participante", key=f"reactivar_{j['id']}"):
                            sb.table("jugadores").update({"activo": True}).eq("id", j["id"]).execute()
                            st.session_state[_exp_jugador_key] = True
                            st.rerun(scope="fragment")

                    st.markdown("<hr style='opacity:0.08;margin:10px 0;'>", unsafe_allow_html=True)

                    # ── Editar nombre y usuario ───────────────────────────────
                    with st.form(f"form_editar_{j['id']}"):
                        nuevo_nombre = st.text_input("Nombre", value=j["nombre"], key=f"nombre_{j['id']}")
                        nuevo_user   = st.text_input("Usuario", value=j.get("username", ""), key=f"user_{j['id']}")
                        guardar = st.form_submit_button("💾 Guardar cambios")
                        if guardar:
                            if not (nuevo_nombre.strip() and nuevo_user.strip()):
                                st.warning("Nombre y usuario no pueden quedar vacíos.")
                            else:
                                nuevo_user_norm = nuevo_user.strip().lower()
                                try:
                                    # Chequear que el usuario no esté en uso por OTRO jugador
                                    choque = (
                                        sb.table("jugadores")
                                        .select("id")
                                        .eq("username", nuevo_user_norm)
                                        .neq("id", j["id"])
                                        .execute()
                                    )
                                    if choque.data:
                                        st.error("Ese usuario ya lo está usando otro jugador.")
                                    else:
                                        sb.table("jugadores").update({
                                            "nombre":   nuevo_nombre.strip(),
                                            "username": nuevo_user_norm,
                                        }).eq("id", j["id"]).execute()
                                        st.cache_data.clear()
                                        st.toast("Datos actualizados.", icon="✅")
                                        st.session_state[_exp_jugador_key] = True
                                        st.rerun(scope="fragment")
                                except Exception as e:
                                    st.error(f"Error al actualizar: {e}")
                                    st.exception(e)

                    st.markdown("<hr style='opacity:0.08;margin:10px 0;'>", unsafe_allow_html=True)

                    # ── Ver contraseña actual ─────────────────────────────────
                    st.caption("🔑 Contraseña actual")
                    pwd_actual = j.get("password_plano")
                    if pwd_actual:
                        st.code(pwd_actual, language=None)
                    else:
                        st.caption(
                            "No disponible (se creó/reseteó antes de guardar la contraseña "
                            "en texto plano). Establecé una nueva abajo para poder verla."
                        )

                    # ── Modificar contraseña a una elegida por el admin ───────
                    with st.form(f"form_pwd_manual_{j['id']}"):
                        pwd_manual = st.text_input(
                            "Nueva contraseña (a elección)", key=f"pwd_manual_{j['id']}"
                        )
                        fijar = st.form_submit_button("✏️ Establecer esta contraseña")
                        if fijar:
                            if not pwd_manual.strip():
                                st.warning("Escribí una contraseña.")
                            else:
                                sb.table("jugadores").update({
                                    "password_hash":  _hash_pwd(pwd_manual.strip()),
                                    "password_plano": pwd_manual.strip(),
                                }).eq("id", j["id"]).execute()
                                st.toast(f"Contraseña de {j['nombre']} actualizada.", icon="🔑")
                                st.session_state[_exp_jugador_key] = True
                                st.rerun(scope="fragment")

                    # ── Resetear contraseña (autogenerada) ────────────────────
                    if st.button("🎲 Generar contraseña aleatoria", key=f"reset_{j['id']}"):
                        nueva_pwd = _generar_password(8)
                        sb.table("jugadores").update({
                            "password_hash":  _hash_pwd(nueva_pwd),
                            "password_plano": nueva_pwd,
                        }).eq("id", j["id"]).execute()
                        st.success(f"Nueva contraseña para **{j['nombre']}**: `{nueva_pwd}`")
                        st.session_state[_exp_jugador_key] = True
                        st.rerun(scope="fragment")

                    st.markdown("<hr style='opacity:0.08;margin:10px 0;'>", unsafe_allow_html=True)

                    # ── Eliminar jugador con confirmación inline ──────────────
                    if st.session_state.confirmar_eliminar_id == j["id"]:
                        st.markdown(f"**¿Eliminar {j['nombre']}?**")
                        col_si2, col_no2 = st.columns(2)
                        with col_si2:
                            if st.button("✅ Sí, eliminar", key=f"del_si_{j['id']}", use_container_width=True):
                                try:
                                    # Borrar pronósticos del jugador primero
                                    sb.table("pronosticos").delete().eq("jugador_id", j["id"]).execute()
                                    sb.table("jugadores").delete().eq("id", j["id"]).execute()

                                    # Verificación real con SELECT fresco
                                    sigue = (
                                        sb.table("jugadores")
                                        .select("id")
                                        .eq("id", j["id"])
                                        .execute()
                                        .data
                                    )
                                    if sigue:
                                        st.error(
                                            f"⚠️ Se ejecutó el borrado pero {j['nombre']} sigue "
                                            "en la base. Revisar RLS (policy de DELETE) o FKs."
                                        )
                                    else:
                                        st.session_state.confirmar_eliminar_id = None
                                        st.toast(f"Jugador {j['nombre']} eliminado.", icon="🗑️")
                                        st.session_state[_exp_jugador_key] = True
                                        st.rerun(scope="fragment")
                                except Exception as e:
                                    st.error(f"Error al eliminar: {e}")
                                    st.exception(e)
                        with col_no2:
                            if st.button("❌ No", key=f"del_no_{j['id']}", use_container_width=True):
                                st.session_state.confirmar_eliminar_id = None
                                st.session_state[_exp_jugador_key] = True
                                st.rerun(scope="fragment")
                    else:
                        if st.button("🗑️ Eliminar jugador", key=f"del_{j['id']}"):
                            st.session_state.confirmar_eliminar_id = j["id"]
                            st.session_state[_exp_jugador_key] = True
                            st.rerun(scope="fragment")


_tab_jugadores_fragment()

# ── Tab 3: ver/editar boleta de cualquier jugador ─────────────────────────
with tab_boletas:
    try:
        jugadores_resp2 = sb.table("jugadores").select("id, nombre").order("nombre").execute()
        jugadores2 = jugadores_resp2.data or []
    except Exception as e:
        st.error(f"No se pudo listar jugadores: {e}")
        jugadores2 = []

    if not jugadores2:
        st.info("Todavía no hay jugadores registrados.")
    else:
        nombres_map  = {j["nombre"]: j["id"] for j in jugadores2}
        nombre_sel   = st.selectbox("Ver boleta de:", list(nombres_map.keys()), key="sel_jugador_admin")
        jid_sel      = nombres_map[nombre_sel]
        editar_admin = st.checkbox("Permitir editar esta boleta como admin", value=False, key="chk_editar_admin")
        mostrar_boleta(jid_sel, nombre_sel, editable=editar_admin, key_ns=f"admin_{jid_sel}")


# ── Tab 4: asignar cada Fecha a un mes (para el ranking mensual) ───────────
with tab_meses:
    st.caption(
        "Asigná cada Fecha (jornada) al mes que corresponda. Esto se usa para "
        "mostrar un ranking separado por mes en la página de Ranking, además "
        "del ranking general."
    )

    _fechas_todas = sorted({p["fecha_numero"] for p in partidos_db if p.get("fecha_numero") is not None})

    if not _fechas_todas:
        st.info("Todavía no hay partidos/fechas cargados en el fixture.")
    else:
        try:
            _map_actual = sb.table("fecha_mes_map").select("fecha_numero, mes").execute().data or []
        except Exception as e:
            st.error(
                f"No se pudo leer la tabla `fecha_mes_map`: {e}\n\n"
                "¿Corriste el SQL que la crea? Revisá `supabase_mercadopago.sql`."
            )
            _map_actual = []

        _mes_por_fecha = {r["fecha_numero"]: r["mes"] for r in _map_actual}
        _meses_existentes = sorted({m for m in _mes_por_fecha.values() if m})

        st.write("**Meses ya usados:**", ", ".join(_meses_existentes) if _meses_existentes else "—")
        st.markdown("<hr style='opacity:0.08;margin:10px 0;'>", unsafe_allow_html=True)

        with st.form("form_asignar_meses"):
            _nuevas_asignaciones = {}
            for _f in _fechas_todas:
                _valor_actual = _mes_por_fecha.get(_f, "")
                _nuevas_asignaciones[_f] = st.text_input(
                    f"Fecha {_f} → mes",
                    value=_valor_actual,
                    placeholder="Ej: Agosto 2026",
                    key=f"mes_fecha_{_f}",
                )
            _guardar_meses = st.form_submit_button("💾 Guardar asignación de meses", use_container_width=True)

        if _guardar_meses:
            try:
                for _f, _mes_val in _nuevas_asignaciones.items():
                    _mes_val = (_mes_val or "").strip()
                    if _mes_val:
                        sb.table("fecha_mes_map").upsert(
                            {"fecha_numero": _f, "mes": _mes_val}, on_conflict="fecha_numero"
                        ).execute()
                    else:
                        sb.table("fecha_mes_map").delete().eq("fecha_numero", _f).execute()
                st.success("✅ Asignación de meses guardada.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo guardar: {e}")

