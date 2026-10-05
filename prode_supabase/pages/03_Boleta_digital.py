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
  - Botón flotante redondo de WhatsApp (solo jugadores logueados): envía/comparte
    por WhatsApp el listado detallado de los pronósticos cargados hasta el momento

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

También, para que el admin pueda habilitar/deshabilitar con un botón que
los jugadores carguen/editen el marcador exacto (goles) de sus
pronósticos (los picks de 1/X/2 siguen funcionando igual), hace falta
una tabla chica de configuración de la app. Si no existe, correr:

    CREATE TABLE IF NOT EXISTS configuracion_app (
        id integer PRIMARY KEY DEFAULT 1,
        boleta_habilitada boolean NOT NULL DEFAULT true
    );
    INSERT INTO configuracion_app (id, boleta_habilitada)
    VALUES (1, true)
    ON CONFLICT (id) DO NOTHING;
"""
import base64
import hashlib
import html as _html
import json
import os
import secrets
import string
import unicodedata
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutureTimeoutError
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
import streamlit.components.v1 as components
import mercadopago
from PIL import Image, ImageOps  # ya es dependencia de Streamlit, no hace falta instalar nada nuevo
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


def _estado_pago_guardado(jugador_id):
    """Devuelve (pagado, mp_payment_id) tal como están HOY en la base, o None
    si no se pudo leer (en ese caso nunca se habilita a nadie: ante la duda,
    no se marca como pagado)."""
    try:
        data = _con_timeout(
            lambda: sb.table("jugadores")
            .select("pagado, mp_payment_id")
            .eq("id", jugador_id)
            .execute()
            .data,
            timeout=8,
        )
    except Exception:
        return None
    if not data:
        return None
    return bool(data[0].get("pagado")), data[0].get("mp_payment_id")


def verificar_pago(jugador_id, payment_id: str) -> bool:
    """Consulta el estado real del pago contra la API de Mercado Pago
    (nunca confiar solo en los parámetros que vienen en la URL de retorno).

    Un pago que ya se usó para habilitar al jugador en una instancia anterior
    (queda guardado en `mp_payment_id`) NO vuelve a habilitarlo si el admin
    después lo marcó como NO pagado: cada instancia requiere un pago nuevo."""
    try:
        resultado = _con_timeout(sdk.payment().get, payment_id)
        pago = resultado["response"]
    except Exception:
        return False
    if not (
        pago.get("status") == "approved"
        and str(pago.get("external_reference")) == str(jugador_id)
    ):
        return False

    estado = _estado_pago_guardado(jugador_id)
    if estado is None:
        return False
    ya_pagado, id_guardado = estado
    if id_guardado is not None and str(id_guardado) == str(payment_id) and not ya_pagado:
        return False  # pago viejo, ya consumido en una instancia anterior

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


def verificar_pago_por_referencia(jugador_id) -> bool:
    """Verificación de RESPALDO que no depende de que el navegador haya
    vuelto limpio desde Mercado Pago con los parámetros en la URL.

    Le pregunta directo a la API de Mercado Pago "¿hay algún pago aprobado
    con este external_reference (= id del jugador)?". Si lo encuentra, marca
    `pagado = True`.

    IMPORTANTE: solo cuenta un pago NUEVO. Se recorren los pagos del más
    reciente al más viejo y, apenas aparece el pago que ya está guardado en
    `mp_payment_id` (el que habilitó al jugador la vez anterior), se corta:
    ese y todos los anteriores ya se usaron. Antes se aceptaba cualquier pago
    aprobado de la historia, así que después de "Marcar TODOS como NO pagado"
    (o de desmarcar a un jugador) bastaba que el jugador entrara para que un
    pago viejo lo volviera a habilitar solo, sin haber pagado esta vez."""
    estado = _estado_pago_guardado(jugador_id)
    if estado is None:
        return False
    ya_pagado, id_guardado = estado

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

    # No dependemos de que la API respete el orden pedido: ordenamos acá.
    pagos = sorted(pagos, key=lambda x: x.get("date_created") or "", reverse=True)

    for pago in pagos:
        if id_guardado is not None and str(pago.get("id")) == str(id_guardado):
            return ya_pagado  # llegamos al pago ya usado: lo demás es más viejo
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


def _mostrar_detalle_pago(payment_id, jugador_id):
    """Muestra (para el admin) los datos reales de un pago guardado en
    `mp_payment_id`, consultados a Mercado Pago, para poder auditar si es
    legítimo: estado, monto, fecha, mail de quien pagó y a qué jugador
    corresponde."""
    try:
        pago = _con_timeout(sdk.payment().get, payment_id)["response"]
    except Exception as e:
        st.error(f"No se pudo consultar el pago en Mercado Pago: {e}")
        return
    if not pago or pago.get("message") or pago.get("status") is None:
        st.warning(f"Mercado Pago no devolvió datos para ese pago: {pago}")
        return
    payer = pago.get("payer") or {}
    coincide = str(pago.get("external_reference")) == str(jugador_id)
    st.markdown(
        f"- **Estado:** `{pago.get('status')}` ({pago.get('status_detail')})\n"
        f"- **Monto:** {pago.get('transaction_amount')} {pago.get('currency_id')}\n"
        f"- **Creado:** {pago.get('date_created')}\n"
        f"- **Acreditado:** {pago.get('date_approved')}\n"
        f"- **Mail de quien pagó:** {payer.get('email') or '—'}\n"
        f"- **Descripción:** {pago.get('description') or '—'}\n"
        f"- **Pertenece a este jugador:** {'✅ sí' if coincide else '❌ NO (external_reference distinto)'}"
    )


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
    .forma-dots {
        display: inline-flex; align-items: center; gap: 3px;
        flex-shrink: 0;
    }
    .forma-punto {
        width: 7px; height: 7px; border-radius: 50%;
        display: inline-block; box-shadow: 0 0 0 1px rgba(0,0,0,0.25);
    }
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

    /* ═══════════ CARD DE PARTICIPANTE v2 (admin + jugador) ═══════════ */
    .pc-card {
        position: relative; overflow: hidden;
        margin: 4px 0 16px 0; padding: 18px 20px; border-radius: 20px;
        background: linear-gradient(135deg, rgba(255,255,255,0.075) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(232,201,107,0.25);
        backdrop-filter: blur(22px) saturate(180%);
        -webkit-backdrop-filter: blur(22px) saturate(180%);
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08);
        font-family: 'Inter', sans-serif;
    }
    .pc-card::before {
        content: ""; position: absolute; inset: 0; pointer-events: none;
        background: radial-gradient(circle at 0% 0%, rgba(232,201,107,0.16), transparent 55%);
    }
    .pc-card > * { position: relative; z-index: 1; }
    .pc-head { display: flex; align-items: center; gap: 16px; }
    .pc-avatar {
        flex-shrink: 0; width: 78px; height: 78px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Bebas Neue', sans-serif; font-size: 2rem; color: #0b0f19;
        background: linear-gradient(135deg, #e8c96b 0%, #c9a54a 100%);
        background-size: cover; background-position: center;
        border: 2px solid rgba(232,201,107,0.6);
        box-shadow: 0 0 0 4px rgba(232,201,107,0.12), 0 6px 18px rgba(232,201,107,0.30);
    }
    .pc-id { min-width: 0; flex: 1; }
    .pc-saludo {
        font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
        text-transform: uppercase; color: #94a3b8; margin: 0 0 2px 0;
    }
    .pc-nombre {
        font-family: 'Bebas Neue', sans-serif; font-size: 1.75rem; color: #f1f5f9;
        letter-spacing: 0.5px; line-height: 1.05; margin: 0; overflow-wrap: anywhere;
    }
    .pc-user { font-size: 0.82rem; color: #e8c96b; margin: 2px 0 0 0; }
    .pc-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px; }
    .pc-tag {
        font-size: 0.7rem; font-weight: 600; padding: 4px 11px; border-radius: 999px;
        white-space: nowrap; background: rgba(148,163,184,0.14); color: #cbd5e1;
        border: 1px solid rgba(148,163,184,0.25);
    }
    .pc-tag.pc-ok   { background: rgba(74,222,128,0.14); color: #4ade80; border-color: rgba(74,222,128,0.3); }
    .pc-tag.pc-warn { background: rgba(232,201,107,0.14); color: #e8c96b; border-color: rgba(232,201,107,0.3); }
    .pc-tag.pc-bad  { background: rgba(239,68,68,0.12); color: #f87171; border-color: rgba(239,68,68,0.25); }

    .pc-rank {
        flex-shrink: 0; min-width: 104px; text-align: center; padding: 10px 14px;
        border-radius: 16px; background: rgba(232,201,107,0.10);
        border: 1px solid rgba(232,201,107,0.32);
    }
    .pc-rank-pos {
        font-family: 'Bebas Neue', sans-serif; font-size: 2.5rem; line-height: 1;
        color: #e8c96b; letter-spacing: 1px; white-space: nowrap;
    }
    .pc-rank-sub { font-size: 0.68rem; color: #94a3b8; margin-top: 3px; line-height: 1.3; }
    .pc-rank.pc-r1 { background: rgba(232,201,107,0.20); border-color: rgba(232,201,107,0.6); box-shadow: 0 0 22px rgba(232,201,107,0.25); }
    .pc-rank.pc-r2 { background: rgba(203,213,225,0.12); border-color: rgba(203,213,225,0.4); }
    .pc-rank.pc-r2 .pc-rank-pos { color: #e2e8f0; }
    .pc-rank.pc-r3 { background: rgba(214,149,91,0.13); border-color: rgba(214,149,91,0.42); }
    .pc-rank.pc-r3 .pc-rank-pos { color: #e0a56b; }
    .pc-rank.pc-rank-off { background: rgba(148,163,184,0.08); border-color: rgba(148,163,184,0.2); }

    .pc-stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 16px; }
    .pc-stat {
        padding: 10px 12px; border-radius: 14px;
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
    }
    .pc-stat-val { font-family: 'Bebas Neue', sans-serif; font-size: 1.8rem; line-height: 1; color: #f1f5f9; letter-spacing: 0.5px; }
    .pc-stat.pc-gold { border-color: rgba(232,201,107,0.3); background: rgba(232,201,107,0.08); }
    .pc-stat.pc-gold .pc-stat-val { color: #e8c96b; }
    .pc-stat-lab { font-size: 0.68rem; color: #94a3b8; margin-top: 4px; }

    .pc-sec { font-size: 0.74rem; font-weight: 600; color: #94a3b8; margin: 18px 0 2px 2px; }
    .pc-zona {
        margin-top: 10px; padding: 12px 14px; border-radius: 14px;
        background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.08);
        border-left: 3px solid var(--zc, #e8c96b);
    }
    .pc-zona-top { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; flex-wrap: wrap; }
    .pc-zona-nombre { font-family: 'Bebas Neue', sans-serif; font-size: 1.25rem; letter-spacing: 0.06em; color: var(--zc, #e8c96b); }
    .pc-zona-res { font-size: 0.75rem; color: #94a3b8; }
    .pc-zona-res b { color: #f1f5f9; }
    .pc-bar { height: 6px; border-radius: 999px; background: rgba(255,255,255,0.08); margin: 8px 0 10px 0; overflow: hidden; }
    .pc-bar > span { display: block; height: 100%; border-radius: 999px; background: var(--zc, #e8c96b); }
    .pc-fechas { display: flex; flex-wrap: wrap; gap: 6px; }
    .pc-fchip {
        font-size: 0.72rem; font-weight: 600; border-radius: 8px; padding: 4px 9px; white-space: nowrap;
        background: rgba(232,201,107,0.10); color: #e8c96b; border: 1px solid rgba(232,201,107,0.2);
    }
    .pc-fchip.pc-f-full { background: rgba(74,222,128,0.13); color: #4ade80; border-color: rgba(74,222,128,0.25); }
    .pc-fchip.pc-f-zero { background: rgba(239,68,68,0.12); color: #f87171; border-color: rgba(239,68,68,0.22); }
    .pc-vacio { font-size: 0.76rem; color: #64748b; }

    .pc-mes {
        display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap;
        margin-top: 16px; padding: 9px 14px; border-radius: 12px;
        background: linear-gradient(90deg, rgba(232,201,107,0.16) 0%, rgba(232,201,107,0.03) 100%);
        border: 1px solid rgba(232,201,107,0.28);
    }
    .pc-mes-nombre { font-family: 'Bebas Neue', sans-serif; font-size: 1.2rem; letter-spacing: 0.08em; color: #e8c96b; }
    .pc-mes-nota { font-size: 0.72rem; color: #94a3b8; }

    /* Foto: ícono de subir al lado del círculo (en vez de un uploader con botón) */
    [class*="st-key-cardbox_"] { position: relative; }
    [class*="st-key-fotoup_"] {
        position: absolute !important; left: 72px; top: 74px; width: 34px !important; z-index: 6;
    }
    [class*="st-key-fotoup_"] [data-testid="stFileUploader"] > label,
    [class*="st-key-fotoup_"] [data-testid="stFileUploaderDropzoneInstructions"],
    [class*="st-key-fotoup_"] [data-testid="stFileUploaderFile"],
    [class*="st-key-fotoup_"] [data-testid="stFileUploaderFileList"] { display: none !important; }
    [class*="st-key-fotoup_"] [data-testid="stFileUploaderDropzone"] {
        padding: 0 !important; min-height: 0 !important; background: transparent !important; border: 0 !important;
        width: 34px; height: 34px;
    }
    [class*="st-key-fotoup_"] button {
        width: 34px !important; height: 34px !important; min-height: 0 !important; padding: 0 !important;
        border-radius: 50% !important; font-size: 0 !important; color: transparent !important;
        background-color: #e8c96b !important; border: 3px solid #0b0f19 !important;
        background-repeat: no-repeat !important; background-position: center !important; background-size: 16px !important;
        background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%230b0f19' stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'><path d='M12 16V4M7 9l5-5 5 5M4 20h16'/></svg>") !important;
        box-shadow: 0 3px 10px rgba(0,0,0,0.45) !important; cursor: pointer;
    }
    [class*="st-key-fotoup_"] button * { font-size: 0 !important; }
    [class*="st-key-fotoup_"] button:hover { background-color: #f3d98a !important; }
    [class*="st-key-fotodel_"] { position: absolute !important; left: 84px; top: 14px; width: 24px !important; z-index: 6; }
    [class*="st-key-fotodel_"] button {
        width: 24px !important; height: 24px !important; min-height: 0 !important; padding: 0 !important;
        border-radius: 50% !important; background: rgba(15,23,42,0.92) !important;
        border: 1px solid rgba(248,113,113,0.5) !important;
    }
    [class*="st-key-fotodel_"] button p { font-size: 11px !important; line-height: 1 !important; margin: 0 !important; color: #f87171 !important; }
    @media (max-width: 640px) {
        .pc-head { flex-wrap: wrap; }
        .pc-rank { margin-left: auto; }
        .pc-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }

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


# ══════════════════════════════════════════════════════════════════════════
# CARD DE PARTICIPANTE — foto, ranking y resumen por zona
# Helpers compartidos entre el panel admin (pestaña Jugadores) y la tarjeta
# que ve cada jugador al loguearse.
# ══════════════════════════════════════════════════════════════════════════
_COLORES_ZONA = {"A": "#e8c96b", "B": "#60a5fa", "Interzonal": "#c4a1ff"}
_MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉"}


def _traer_todo(tabla, columnas, orden="id"):
    """Trae TODAS las filas de una tabla paginando de a tandas.

    Supabase/PostgREST devuelve como máximo ~1000 filas por consulta. La tabla
    `pronosticos` crece (jugadores × partidos), así que una consulta simple
    corta los datos en silencio y el ranking sale con puntos de menos. Acá se
    pide por páginas hasta que no vengan más filas."""
    filas, desde = [], 0
    for _ in range(100):  # tope de seguridad
        lote = (
            sb.table(tabla).select(columnas).order(orden)
            .range(desde, desde + 999).execute().data or []
        )
        if not lote:
            break
        filas.extend(lote)
        desde += len(lote)
    return filas


def _norm_mes(s) -> str:
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().split())


@st.cache_data(ttl=30)
def _fechas_del_mes(mes_label):
    """Números de Fecha asignados a un mes en la pestaña 'Meses' del admin
    (tabla `fecha_mes_map`), el mismo origen que usa el ranking mensual.
    Compara sin importar mayúsculas ni tildes, y acepta tanto "Octubre 2026"
    como solo "Octubre"."""
    try:
        filas = sb.table("fecha_mes_map").select("fecha_numero, mes").execute().data or []
    except Exception:
        return []
    objetivos = {_norm_mes(mes_label), _norm_mes(str(mes_label).split()[0] if mes_label else "")}
    return sorted({
        int(r["fecha_numero"]) for r in filas
        if r.get("fecha_numero") is not None and _norm_mes(r.get("mes")) in objetivos
    })


def _ids_partidos_de_fechas(partidos, fechas):
    fechas = set(fechas)
    return {
        p["id"] for p in partidos
        if p.get("fecha_numero") is not None and int(p["fecha_numero"]) in fechas
    }


def _calcular_ranking(jugadores, filas_puntos, partido_ids=None):
    """Ranking del prode (del MES si se pasa `partido_ids`).

    - Puntos de cada jugador = suma de `pronosticos.puntos` de los partidos
      incluidos (1 por acertar el signo, 3 por el marcador exacto).
    - Si `partido_ids` no es None, solo cuentan esos partidos (los de las
      fechas asignadas al mes actual).
    - Entran solo jugadores con inscripción paga y activos (como el pozo).
    - Orden: más puntos primero. Mismos puntos = misma posición (1°, 2°, 2°, 4°).
    """
    stats = {}
    for r in filas_puntos:
        if partido_ids is not None and r.get("partido_id") not in partido_ids:
            continue
        pts = r.get("puntos")
        if not pts:
            continue
        s = stats.setdefault(r.get("jugador_id"), {"puntos": 0, "exactos": 0, "signos": 0})
        s["puntos"] += pts
        if pts >= 3:
            s["exactos"] += 1
        else:
            s["signos"] += 1

    habilitados = [j for j in jugadores if j.get("pagado") and j.get("activo", True)]
    habilitados.sort(
        key=lambda j: (-stats.get(j["id"], {}).get("puntos", 0), (j.get("nombre") or "").lower())
    )
    posicion, pts_prev, pos_prev = {}, None, 0
    for i, j in enumerate(habilitados, start=1):
        p = stats.get(j["id"], {}).get("puntos", 0)
        if p != pts_prev:
            pos_prev, pts_prev = i, p
        posicion[j["id"]] = pos_prev
    lider = stats.get(habilitados[0]["id"], {}).get("puntos", 0) if habilitados else 0
    return {
        "stats": stats,
        "posicion": posicion,
        "total": len(habilitados),
        "lider_puntos": lider,
    }


@st.cache_data(ttl=15)
def _ranking_mes(mes_label):
    """Ranking del mes indicado (ej. "Octubre 2026") para la tarjeta del jugador."""
    jugadores = _traer_todo("jugadores", "id, nombre, pagado, activo")
    filas = _traer_todo("pronosticos", "jugador_id, partido_id, puntos")
    partidos = _traer_todo("partidos", "id, fecha_numero")
    fechas = _fechas_del_mes(mes_label)
    rk = _calcular_ranking(jugadores, filas, _ids_partidos_de_fechas(partidos, fechas))
    rk["mes"] = mes_label
    rk["sin_fechas"] = not fechas
    return rk


def _procesar_foto_subida(archivo) -> str:
    """Foto subida → JPEG cuadrado 320×320 en base64 (respeta la rotación del celular)."""
    img = Image.open(archivo)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img = ImageOps.fit(img, (320, 320), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=82, optimize=True)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _guardar_foto_jugador(jugador_id, foto_b64) -> bool:
    """Guarda (o borra, con None) la foto y verifica con un SELECT fresco que
    realmente quedó en la base (por si RLS descarta el UPDATE sin error)."""
    sb.table("jugadores").update({"foto_base64": foto_b64}).eq("id", jugador_id).execute()
    r = sb.table("jugadores").select("foto_base64").eq("id", jugador_id).execute().data
    return bool(r) and ((r[0].get("foto_base64") or None) == (foto_b64 or None))


def _resumen_zonas_html(pron_j, jugados_zf, zonas_orden, mes_label=""):
    """Aciertos del jugador por zona (A / B / Interzonal) y por fecha."""
    _sufijo = f" de {_html.escape(str(mes_label))}" if mes_label else ""
    bloques = [f'<div class="pc-sec">Aciertos por zona y fecha{_sufijo}</div>']
    for zona in zonas_orden:
        color = _COLORES_ZONA.get(zona, "#e8c96b")
        titulo = "Interzonal" if zona == "Interzonal" else f"Zona {zona}"
        fechas = jugados_zf.get(zona, {})
        if not fechas:
            bloques.append(
                f'<div class="pc-zona" style="--zc:{color};"><div class="pc-zona-top">'
                f'<span class="pc-zona-nombre">{_html.escape(str(titulo))}</span>'
                f'<span class="pc-vacio">Sin resultados de este mes todavía</span></div></div>'
            )
            continue
        tot_jug = tot_ac = tot_pts = 0
        chips = []
        for fecha in sorted(fechas, key=int):
            ids = fechas[fecha]
            ac = sum(1 for pid in ids if pron_j.get(pid) not in (None, 0))
            pts = sum((pron_j.get(pid) or 0) for pid in ids)
            tot_jug += len(ids)
            tot_ac += ac
            tot_pts += pts
            clase = "pc-f-full" if ac == len(ids) else ("pc-f-zero" if ac == 0 else "")
            chips.append(
                f'<span class="pc-fchip {clase}" title="{pts} pts">F{fecha} · {ac}/{len(ids)}</span>'
            )
        pct = round(100 * tot_ac / tot_jug) if tot_jug else 0
        bloques.append(
            f'<div class="pc-zona" style="--zc:{color};"><div class="pc-zona-top">'
            f'<span class="pc-zona-nombre">{_html.escape(str(titulo))}</span>'
            f'<span class="pc-zona-res"><b>{tot_ac}/{tot_jug}</b> aciertos · <b>{tot_pts}</b> pts</span></div>'
            f'<div class="pc-bar"><span style="width:{pct}%;"></span></div>'
            f'<div class="pc-fechas">{"".join(chips)}</div></div>'
        )
    return "".join(bloques)


@st.cache_data(ttl=15)
def _zonas_html_perfil(jugador_id, mes_label):
    """Mismo resumen de aciertos por Zona A / Zona B / Interzonal y por fecha
    que ve el admin en la card de cada participante, pero para UN jugador (el
    que está logueado). Se arma con `_resumen_zonas_html`, así que se ve y
    cuenta exactamente igual: solo partidos YA JUGADOS de las fechas asignadas
    al mes en curso.

    Está autocontenido (consulta sus propios datos) porque la card del perfil
    se dibuja más arriba en el archivo que `cargar_partidos` y
    `agrupar_por_zona_fecha`, que todavía no están definidas en ese punto.
    """
    fechas_mes = set(_fechas_del_mes(mes_label))
    partidos = _traer_todo("partidos", "id, zona, fecha_numero, goles_local, goles_visitante")
    filas = (
        sb.table("pronosticos")
        .select("partido_id, puntos")
        .eq("jugador_id", jugador_id)
        .execute()
        .data
        or []
    )
    pron_j = {r.get("partido_id"): r.get("puntos") for r in filas}

    por_zona = {}
    for p in partidos:
        if p.get("zona") is None or p.get("fecha_numero") is None:
            continue
        por_zona.setdefault(p["zona"], {}).setdefault(p["fecha_numero"], []).append(p)
    zonas_orden = sorted(
        por_zona.keys(), key=lambda z: (0 if z == "A" else 1 if z == "B" else 2, z)
    )

    jugados_zf = {}  # zona -> fecha -> [partido_id jugados]
    for z in zonas_orden:
        for f in sorted(por_zona[z].keys(), key=int):
            if int(f) not in fechas_mes:
                continue
            ids = [
                p["id"] for p in por_zona[z][f]
                if p.get("goles_local") is not None and p.get("goles_visitante") is not None
            ]
            if ids:
                jugados_zf.setdefault(z, {})[f] = ids

    return _resumen_zonas_html(pron_j, jugados_zf, zonas_orden, mes_label)


def _card_participante_html(nombre, username, foto, rk, jid, saludo=None, tags_html="", zonas_html=""):
    esc = _html.escape
    nombre = nombre or ""
    iniciales = "".join(p[0] for p in nombre.split()[:2]).upper() or "?"
    if foto:
        estilo = "background-image:url('data:image/jpeg;base64," + foto + "');"
        avatar = '<div class="pc-avatar" style="' + estilo + '"></div>'
    else:
        avatar = f'<div class="pc-avatar">{esc(iniciales)}</div>'

    mes = esc((rk.get("mes") or "").upper())
    sin_fechas = bool(rk.get("sin_fechas"))
    sin_puntos = not rk.get("lider_puntos")
    pos = rk["posicion"].get(jid)

    if pos and not sin_fechas and not sin_puntos:
        clase_rank = f"pc-r{pos}" if pos <= 3 else ""
        rank = (
            f'<div class="pc-rank {clase_rank}">'
            f'<div class="pc-rank-pos">{_MEDALLAS.get(pos, "")} {pos}°</div>'
            f'<div class="pc-rank-sub">de {rk["total"]}</div></div>'
        )
    else:
        if not pos:
            msg = "Fuera del<br>ranking"
        elif sin_fechas:
            msg = "Sin fechas<br>asignadas"
        else:
            msg = "Sin puntos<br>todavía"
        rank = f'<div class="pc-rank pc-rank-off"><div class="pc-rank-sub">{msg}</div></div>'

    s = rk["stats"].get(jid, {})
    pts = s.get("puntos", 0)
    if not pos or sin_puntos:
        dif = "—"
    elif pos == 1:
        dif = "¡Líder!"
    else:
        dif = f"-{max(rk['lider_puntos'] - pts, 0)}"
    items = [
        (pts, "Puntos del mes", True),
        (s.get("exactos", 0), "Marcador exacto (3 pts)", False),
        (s.get("signos", 0), "Solo signo (1 pt)", False),
        (dif, "Del líder", False),
    ]
    stats_html = '<div class="pc-stats">' + "".join(
        f'<div class="pc-stat{" pc-gold" if oro else ""}"><div class="pc-stat-val">{v}</div>'
        f'<div class="pc-stat-lab">{lab}</div></div>'
        for v, lab, oro in items
    ) + "</div>"

    nota_mes = "Todavía no hay fechas asignadas a este mes" if sin_fechas else "Ranking y puntos del mes"
    banner = (
        f'<div class="pc-mes"><span class="pc-mes-nombre">📅 {mes}</span>'
        f'<span class="pc-mes-nota">{nota_mes}</span></div>'
    )

    saludo_html = f'<p class="pc-saludo">{esc(saludo)}</p>' if saludo else ""
    tags = f'<div class="pc-tags">{tags_html}</div>' if tags_html else ""
    return (
        '<div class="pc-card"><div class="pc-head">' + avatar
        + '<div class="pc-id">' + saludo_html
        + f'<p class="pc-nombre">{esc(nombre)}</p><p class="pc-user">@{esc(username or "")}</p>'
        + tags + "</div>" + rank + "</div>" + banner + stats_html + zonas_html + "</div>"
    )


@st.cache_data(ttl=10)
def _cargar_config_app():
    """
    Trae la config global de la app (fila única, id=1) desde la tabla
    `configuracion_app`. Si la tabla todavía no existe (instalación vieja
    que no corrió el CREATE TABLE de más arriba) o la fila no está, no
    rompemos la página: devolvemos el default (boleta habilitada) para
    no bloquear a nadie por un problema de configuración.
    """
    try:
        res = sb.table("configuracion_app").select("*").eq("id", 1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        pass
    return {"id": 1, "boleta_habilitada": True}


def _set_boleta_habilitada(valor: bool):
    """Prende/apaga, desde el admin, si los jugadores pueden cargar/editar
    el marcador exacto (goles) de sus pronósticos. Los picks de 1/X/2 no
    se ven afectados. Hace upsert por si la fila id=1 todavía no existe."""
    sb.table("configuracion_app").upsert(
        {"id": 1, "boleta_habilitada": valor}
    ).execute()
    _cargar_config_app.clear()


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
# BOTÓN FLOTANTE DE WHATSAPP — enviarse / compartir los pronósticos
# ══════════════════════════════════════════════════════════════════════════
# Ícono oficial de WhatsApp (blanco) embebido como data-URI: así no depende
# de ningún recurso externo ni de que Streamlit deje pasar un <svg> inline.
_WA_ICONO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="#ffffff" '
    'd="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.3-.15-1.263-.465-2.403-1.485-.888-.795-1.484-1.77-1.66-2.07-.174-.3-.019-.465.13-.615.136-.135.301-.345.451-.52.146-.181.194-.301.297-.496.1-.21.049-.375-.025-.524-.075-.15-.672-1.62-.922-2.206-.24-.584-.487-.51-.672-.51-.172-.015-.371-.015-.571-.015-.2 0-.523.074-.797.359-.273.3-1.045 1.02-1.045 2.475s1.07 2.865 1.219 3.075c.149.18 2.095 3.195 5.076 4.483.709.3 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.696.248-1.289.173-1.414-.074-.127-.272-.202-.57-.347'
    'm-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884'
    'm8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>'
)
_WA_ICONO_URI = "data:image/svg+xml;base64," + base64.b64encode(_WA_ICONO_SVG.encode("utf-8")).decode("ascii")

# Largo máximo (ya url-encodeado) del link de WhatsApp. Los links wa.me con
# texto prearmado funcionan bien hasta varios miles de caracteres; con los
# ~15 pronósticos de una fecha el mensaje queda MUY por debajo de este tope,
# que existe solo como red de seguridad.
_WA_MAX_URL_CHARS = 6000


def _fecha_vigente(fechas_de_zona: dict):
    """Devuelve la fecha (jornada) \"en juego\" de una zona: la primera que
    todavía tiene algún partido sin resultado cargado. Si ya se jugaron
    todas, devuelve la última. `fechas_de_zona` es {fecha_numero: [partidos]}.
    """
    fechas = sorted(fechas_de_zona.keys(), key=int)
    for f in fechas:
        if any(
            p.get("goles_local") is None or p.get("goles_visitante") is None
            for p in fechas_de_zona[f]
        ):
            return f
    return fechas[-1] if fechas else None


def _texto_whatsapp_pronosticos(nombre, pron, por_zona, zonas_orden):
    """Arma el mensaje (con formato de WhatsApp: *negrita*) con el listado
    detallado de los pronósticos que el jugador tiene cargados AHORA en la
    fecha vigente de cada zona (Zona A / Zona B / Interzonal).

    Si el pronóstico se cargó eligiendo solo 1/X/2 (sin_marcador), se muestra
    el signo; si se cargó marcador exacto, se muestra el marcador.
    """
    ahora = datetime.now(TZ_ARG).strftime("%d/%m/%Y %H:%M")
    cabecera = [
        "🏆 *Mi boleta · Prode Liga Profesional*",
        f"👤 {nombre}",
        f"🕒 Enviada el {ahora} hs",
    ]

    bloques = []  # [(titulo, [linea, ...])]
    for zona in zonas_orden:
        fecha = _fecha_vigente(por_zona.get(zona, {}))
        if fecha is None:
            continue
        partidos = sorted(
            por_zona[zona][fecha],
            key=lambda p: (p.get("fecha_partido") or "9999-99-99", p.get("hora") or "99:99"),
        )
        lineas = []
        for p in partidos:
            pr = pron.get(p["id"])
            if not pr or pr.get("signo_pred") is None:
                continue
            local, visitante = p["equipo_local"], p["equipo_visitante"]
            if pr.get("sin_marcador"):
                texto_signo = {
                    "1": f"Gana {local}",
                    "X": "Empate",
                    "2": f"Gana {visitante}",
                }.get(pr["signo_pred"], "—")
                lineas.append(f"{local} vs {visitante} → *{texto_signo}*")
            else:
                gl, gv = pr.get("goles_local_pred"), pr.get("goles_visitante_pred")
                lineas.append(f"{local} *{gl} - {gv}* {visitante}")
        if lineas:
            titulo = f"*{etiqueta_zona(zona)} · Fecha {fecha}* ({len(lineas)}/{len(partidos)} cargados)"
            bloques.append((titulo, lineas))

    def _armar(bloques_):
        partes = list(cabecera)
        n = 0
        for titulo, lineas in bloques_:
            partes.append("")
            partes.append(titulo)
            for ln in lineas:
                n += 1
                partes.append(f"{n}. {ln}")
        if n == 0:
            partes += ["", "Todavía no cargué ningún pronóstico 😅"]
        else:
            partes += ["", f"✅ Total: {n} pronósticos cargados"]
        return "\n".join(partes), n

    texto, _ = _armar(bloques)

    # Red de seguridad por largo: si por algún motivo el mensaje no entra en
    # el link, se recortan las últimas líneas (en la práctica no pasa).
    while len(urllib.parse.quote(texto, safe="")) > _WA_MAX_URL_CHARS and bloques:
        titulo, lineas = bloques[-1]
        if len(lineas) > 1:
            bloques[-1] = (titulo, lineas[:-1])
        else:
            bloques.pop()
        texto, _ = _armar(bloques)
    return texto


def _boton_whatsapp_flotante(nombre, pron, por_zona, zonas_orden):
    """Dibuja el ícono redondo y flotante de WhatsApp (abajo a la derecha).

    Al tocarlo abre WhatsApp con el listado de pronósticos ya escrito, para
    que el jugador elija a quién mandarlo (incluido su propio chat, "Tú"/
    "Mensajes guardados") o lo comparta. Se usa un link `wa.me` normal, que
    funciona igual en celular (abre la app) y en computadora (WhatsApp Web).
    """
    texto = _texto_whatsapp_pronosticos(nombre, pron, por_zona, zonas_orden)
    url = "https://wa.me/?text=" + urllib.parse.quote(texto, safe="")
    # OJO: sin líneas en blanco ni sangría dentro de este HTML, para que el
    # parser de Markdown de Streamlit no lo interprete como bloque de código.
    html_boton = (
        "<style>"
        ".wa-float{position:fixed;right:18px;bottom:calc(120px + env(safe-area-inset-bottom,0px));"
        "width:60px;height:60px;border-radius:50%;background-color:#25D366;"
        f"background-image:url('{_WA_ICONO_URI}');background-repeat:no-repeat;"
        "background-position:center;background-size:34px 34px;"
        "box-shadow:0 6px 18px rgba(0,0,0,.4);z-index:999990;display:block;"
        "text-decoration:none;border:0;transition:transform .15s ease,box-shadow .15s ease;"
        "animation:wa-pulso 2.6s ease-out infinite;}"
        ".wa-float:hover{transform:scale(1.08);box-shadow:0 8px 22px rgba(0,0,0,.5);}"
        ".wa-float:active{transform:scale(.95);}"
        "@keyframes wa-pulso{0%{box-shadow:0 6px 18px rgba(0,0,0,.4),0 0 0 0 rgba(37,211,102,.55);}"
        "70%{box-shadow:0 6px 18px rgba(0,0,0,.4),0 0 0 16px rgba(37,211,102,0);}"
        "100%{box-shadow:0 6px 18px rgba(0,0,0,.4),0 0 0 0 rgba(37,211,102,0);}}"
        "@media (prefers-reduced-motion:reduce){.wa-float{animation:none;}}"
        "</style>"
        f'<a class="wa-float" href="{_html.escape(url, quote=True)}" target="_blank" '
        'rel="noopener noreferrer" title="Enviar mis pronósticos por WhatsApp" '
        'aria-label="Enviar mis pronósticos por WhatsApp"></a>'
    )
    st.markdown(html_boton, unsafe_allow_html=True)


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

        st.markdown("---")
        _config_app = _cargar_config_app()
        _boleta_on = bool(_config_app.get("boleta_habilitada", True))
        if _boleta_on:
            st.success("⚽ Marcador exacto habilitado")
            if st.button(
                "🔒 Deshabilitar carga de marcador exacto",
                use_container_width=True,
                help=(
                    "Los jugadores dejan de poder cargar/editar el marcador "
                    "exacto (goles). Los picks de 1/X/2 siguen funcionando "
                    "normal. Vos como admin no te ves afectado."
                ),
            ):
                _set_boleta_habilitada(False)
                st.rerun()
        else:
            st.warning("🔒 Marcador exacto DESHABILITADO")
            if st.button(
                "⚽ Habilitar carga de marcador exacto",
                use_container_width=True,
                help="Los jugadores vuelven a poder cargar/editar el marcador exacto normalmente.",
            ):
                _set_boleta_habilitada(True)
                st.rerun()
        st.markdown("---")

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
    _foto_ok = True
    try:
        _perfil_db = (
            sb.table("jugadores")
            .select("nombre, username, alias_cbu, pagado, foto_base64")
            .eq("id", st.session_state.jugador_id)
            .execute()
            .data
        )
    except Exception:
        # Todavía no existe la columna foto_base64 (ver docstring): la tarjeta
        # sigue funcionando con iniciales y se oculta la carga de foto.
        _foto_ok = False
        _perfil_db = (
            sb.table("jugadores")
            .select("nombre, username, alias_cbu, pagado")
            .eq("id", st.session_state.jugador_id)
            .execute()
            .data
        )
    _perfil = _perfil_db[0] if _perfil_db else {}
    _alias_actual = (_perfil.get("alias_cbu") or "").strip()
    _foto_perfil = (_perfil.get("foto_base64") or "").strip() if _foto_ok else ""

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

    _mes_lbl_perfil = _mes_actual_boleta()[1]
    try:
        _rk_perfil = _ranking_mes(_mes_lbl_perfil)
    except Exception:
        _rk_perfil = {
            "stats": {}, "posicion": {}, "total": 0, "lider_puntos": 0,
            "mes": _mes_lbl_perfil, "sin_fechas": True,
        }

    # Resumen de aciertos por Zona A / Zona B / Interzonal (igual que la card
    # del admin). Si algo falla, la card se muestra igual, sin el resumen.
    try:
        _zonas_html_perfil_seguro = _zonas_html_perfil(st.session_state.jugador_id, _mes_lbl_perfil)
    except Exception:
        _zonas_html_perfil_seguro = ""

    # El contenedor con key permite posicionar el ícono de subir foto justo
    # al lado del círculo del avatar (ver CSS "st-key-cardbox_/fotoup_/fotodel_").
    with st.container(key="cardbox_perfil"):
        st.markdown(
            _card_participante_html(
                nombre=_perfil.get("nombre", st.session_state.jugador_nombre),
                username=_perfil.get("username", ""),
                foto=_foto_perfil,
                rk=_rk_perfil,
                jid=st.session_state.jugador_id,
                saludo="Sesión iniciada",
                tags_html=_chip_alias_html + _chip_mes_html,
                zonas_html=_zonas_html_perfil_seguro,
            ),
            unsafe_allow_html=True,
        )
        if _foto_ok:
            # El contador renueva la key del uploader después de guardar para
            # que el próximo rerun no vuelva a procesar el mismo archivo.
            _ctr_key = "foto_perfil_ctr"
            _ctr = st.session_state.get(_ctr_key, 0)
            _archivo_foto = st.file_uploader(
                "Cambiar mi foto",
                type=["png", "jpg", "jpeg"],
                key=f"fotoup_perfil_{_ctr}",
                label_visibility="collapsed",
            )
            if _archivo_foto is not None:
                try:
                    if _guardar_foto_jugador(st.session_state.jugador_id, _procesar_foto_subida(_archivo_foto)):
                        st.session_state[_ctr_key] = _ctr + 1
                        st.toast("Foto actualizada.", icon="📷")
                        st.rerun()
                    else:
                        st.error("No se pudo guardar la foto. Probá de nuevo o avisale al admin.")
                except Exception as e:
                    st.error(f"No pudimos procesar esa imagen: {e}")
            if _foto_perfil and st.button("✕", key="fotodel_perfil", help="Quitar mi foto"):
                if _guardar_foto_jugador(st.session_state.jugador_id, None):
                    st.toast("Foto eliminada.", icon="🗑️")
                    st.rerun()
                else:
                    st.error("No se pudo quitar la foto. Probá de nuevo.")

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
    # Paginado: una consulta simple se corta en ~1000 filas y el ranking quedaría incompleto.
    return _traer_todo("pronosticos", "jugador_id, partido_id, puntos")


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


_COLOR_FORMA = {"V": "#22c55e", "E": "#9ca3af", "D": "#ef4444"}  # verde / gris / rojo


def calcular_forma_reciente(partidos):
    """
    Para cada equipo, calcula el resultado (V/E/D) de sus últimos 5
    partidos YA JUGADOS (con goles cargados), ordenados del más reciente
    al más antiguo. Se usa para pintar los puntitos de racha al lado de
    cada escudo en la boleta, así el jugador tiene una idea rápida de
    cómo viene cada equipo últimamente.
    """
    jugados = [
        p for p in partidos
        if p.get("goles_local") is not None and p.get("goles_visitante") is not None
    ]
    jugados_ordenados = sorted(
        jugados, key=lambda p: (p.get("fecha_partido") or "", p.get("hora") or "")
    )

    forma = {}
    for p in jugados_ordenados:
        gl, gv = p["goles_local"], p["goles_visitante"]
        local, visitante = p["equipo_local"], p["equipo_visitante"]
        if gl > gv:
            res_local, res_visit = "V", "D"
        elif gl < gv:
            res_local, res_visit = "D", "V"
        else:
            res_local, res_visit = "E", "E"
        forma.setdefault(local, []).append(res_local)
        forma.setdefault(visitante, []).append(res_visit)

    # Nos quedamos con los últimos 5 de cada equipo, del más reciente al
    # más antiguo (los agregamos en orden cronológico, así que invertimos).
    return {equipo: list(reversed(resultados[-5:])) for equipo, resultados in forma.items()}


def _puntos_forma_html(equipo, forma_equipos):
    """HTML de los puntitos de racha (verde/gris/rojo) para un equipo."""
    resultados = forma_equipos.get(equipo) or []
    if not resultados:
        return ""
    etiquetas = {"V": "Ganó", "E": "Empató", "D": "Perdió"}
    puntos = "".join(
        f'<span class="forma-punto" style="background:{_COLOR_FORMA.get(r, "#9ca3af")};" '
        f'title="{etiquetas.get(r, r)}"></span>'
        for r in resultados
    )
    return f'<span class="forma-dots">{puntos}</span>'


try:
    partidos_db = cargar_partidos()
except Exception as e:
    st.error(f"No se pudieron cargar los partidos: {e}")
    st.stop()

if not partidos_db:
    st.info("Todavía no hay partidos cargados.")
    st.stop()

# Racha de los últimos 5 partidos de cada equipo (para los puntitos de
# color al lado de cada escudo). Se recalcula en cada corrida del script
# a partir de `partidos_db` (que ya tiene su propio caché de 30s), así que
# siempre está en línea con los resultados que se ven en la boleta.
forma_equipos_reciente = calcular_forma_reciente(partidos_db)


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
                        forma_l = _puntos_forma_html(local, forma_equipos_reciente)
                        forma_v = _puntos_forma_html(visitante, forma_equipos_reciente)

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
                                f'<div class="fila-equipo">{img_l}{forma_l}<span>{local}</span></div>',
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
                                f'<div class="fila-equipo derecha"><span>{visitante}</span>{forma_v}{img_v}</div>',
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
                            _marcador_exacto_habilitado = (
                                st.session_state.es_admin
                                or bool(_cargar_config_app().get("boleta_habilitada", True))
                            )
                            if not _marcador_exacto_habilitado:
                                # El admin deshabilitó la carga de marcador
                                # exacto: se sigue pudiendo elegir 1/X/2
                                # arriba, pero los goles quedan bloqueados.
                                # Si el jugador ya tenía un marcador cargado
                                # de antes, se lo mostramos de solo lectura
                                # (no se pierde lo que ya había cargado).
                                gl_new_pred = st.session_state.get(
                                    _gl_key, gl_pred_prev if gl_pred_prev is not None else 0
                                )
                                gv_new_pred = st.session_state.get(
                                    _gv_key, gv_pred_prev if gv_pred_prev is not None else 0
                                )
                                with col_gl:
                                    st.caption(f"Goles {local}")
                                    if gl_pred_prev is not None:
                                        st.markdown(
                                            f"<div style='text-align:center;font-weight:600;'>{gl_pred_prev}</div>",
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.caption("🔒 Deshabilitado")
                                with col_gv:
                                    st.caption(f"Goles {visitante}")
                                    if gv_pred_prev is not None:
                                        st.markdown(
                                            f"<div style='text-align:center;font-weight:600;'>{gv_pred_prev}</div>",
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.caption("🔒 Deshabilitado")
                            elif mostrar_goles:
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

    # ── Botón flotante de WhatsApp (solo en la boleta propia del jugador) ──
    # Va al FINAL del fragmento a propósito: así, cada vez que el jugador
    # guarda o cambia un pronóstico (que re-ejecuta este fragmento), el link
    # se vuelve a armar con el listado actualizado, y nunca queda desfasado.
    if editable and not st.session_state.es_admin and key_ns == "propia":
        _boton_whatsapp_flotante(jugador_objetivo_nombre, pron, por_zona, zonas_orden)


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
            "estado de pausado/activo de nadie. Los pagos de Mercado Pago ya registrados "
            "quedan como \"usados\": no vuelven a habilitar a nadie automáticamente."
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

            # ── Cálculo único (no por jugador) de ranking y aciertos por zona/fecha ──
            # Todo esto se calcula UNA sola vez acá afuera del loop, en memoria,
            # a partir de datos ya cargados/cacheados, para que abrir cada card
            # sea instantáneo (nada de golpear la base de nuevo por jugador).
            try:
                _todos_puntos = cargar_todos_los_puntos()
            except Exception as e:
                st.warning(f"No se pudieron cargar los puntos para el ranking: {e}")
                _todos_puntos = []

            _mes_lbl_adm = _mes_actual_boleta()[1]
            _fechas_mes = set(_fechas_del_mes(_mes_lbl_adm))

            st.caption(
                f"📊 **Datos de {_mes_lbl_adm.upper()}** (no del ranking general). Puntos = suma de lo "
                "ganado en cada partido de las fechas asignadas a este mes en la pestaña «Meses» "
                "(1 por acertar el signo, 3 por el marcador exacto). Solo entran jugadores con "
                "inscripción paga y activos. Mismos puntos = misma posición (1°, 2°, 2°, 4°…)."
            )
            if not _fechas_mes:
                st.warning(
                    f"No hay fechas asignadas a {_mes_lbl_adm} en la pestaña «Meses (Ranking)». "
                    "Asignalas ahí para que las cards muestren datos del mes."
                )

            _rk = _calcular_ranking(jugadores, _todos_puntos, _ids_partidos_de_fechas(partidos_db, _fechas_mes))
            _rk["mes"] = _mes_lbl_adm
            _rk["sin_fechas"] = not _fechas_mes

            _pron_por_jugador = {}  # jugador_id -> {partido_id: puntos}
            for _row in _todos_puntos:
                _pron_por_jugador.setdefault(_row.get("jugador_id"), {})[_row.get("partido_id")] = _row.get("puntos")

            # Partidos ya jugados por ZONA y por Fecha. Antes se agrupaba solo por
            # número de fecha mezclando zonas; ahora cada zona (A, B, Interzonal)
            # tiene su propio resumen.
            _por_zona_adm, _zonas_orden_adm = agrupar_por_zona_fecha(partidos_db)
            _jugados_zf = {}  # zona -> fecha -> [partido_id jugados]
            for _z in _zonas_orden_adm:
                for _f in sorted(_por_zona_adm[_z].keys(), key=int):
                    if int(_f) not in _fechas_mes:
                        continue
                    _ids = [
                        p["id"] for p in _por_zona_adm[_z][_f]
                        if p.get("goles_local") is not None and p.get("goles_visitante") is not None
                    ]
                    if _ids:
                        _jugados_zf.setdefault(_z, {})[_f] = _ids

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

                    # ── Card del MES: foto + posición + stats + resumen por zona ──
                    _foto_actual = (j.get("foto_base64") or "").strip() if _foto_col_disponible else ""
                    if not _esta_activo:
                        _tags_adm = '<span class="pc-tag">⏸️ Pausado</span>'
                    elif _pago_ok:
                        _tags_adm = '<span class="pc-tag pc-ok">💰 Inscripción paga</span>'
                    else:
                        _tags_adm = '<span class="pc-tag pc-bad">🔴 Sin pagar</span>'
                    if (j.get("alias_cbu") or "").strip():
                        _tags_adm += '<span class="pc-tag pc-ok">💸 Alias/CBU cargado</span>'
                    else:
                        _tags_adm += '<span class="pc-tag pc-warn">💸 Sin Alias/CBU</span>'

                    # Contenedor con key: permite pegar el ícono de subir foto
                    # al lado del círculo del avatar (CSS "st-key-cardbox_/fotoup_/fotodel_").
                    with st.container(key=f"cardbox_{j['id']}"):
                        st.markdown(
                            _card_participante_html(
                                nombre=j["nombre"],
                                username=j.get("username", "—"),
                                foto=_foto_actual,
                                rk=_rk,
                                jid=j["id"],
                                tags_html=_tags_adm,
                                zonas_html=_resumen_zonas_html(
                                    _pron_por_jugador.get(j["id"], {}), _jugados_zf, _zonas_orden_adm, _mes_lbl_adm
                                ),
                            ),
                            unsafe_allow_html=True,
                        )

                        if _foto_col_disponible:
                            # Contador para renovar la key del uploader después de
                            # guardar y no re-procesar el mismo archivo en bucle.
                            _foto_ctr_key = f"foto_up_ctr_{j['id']}"
                            _foto_ctr = st.session_state.get(_foto_ctr_key, 0)
                            _foto_nueva = st.file_uploader(
                                "Cambiar foto",
                                type=["png", "jpg", "jpeg"],
                                key=f"fotoup_{j['id']}_{_foto_ctr}",
                                label_visibility="collapsed",
                            )
                            if _foto_nueva is not None:
                                try:
                                    if _guardar_foto_jugador(j["id"], _procesar_foto_subida(_foto_nueva)):
                                        st.session_state[_foto_ctr_key] = _foto_ctr + 1
                                        st.toast(f"Foto de {j['nombre']} actualizada.", icon="📷")
                                        st.session_state[_exp_jugador_key] = True
                                        st.rerun(scope="fragment")
                                    else:
                                        st.error("⚠️ La foto no quedó guardada en la base. Revisar RLS (policy de UPDATE).")
                                except Exception as e:
                                    st.error(f"No se pudo guardar la foto: {e}")
                            if _foto_actual and st.button("✕", key=f"fotodel_{j['id']}", help="Quitar foto"):
                                _guardar_foto_jugador(j["id"], None)
                                st.session_state[_exp_jugador_key] = True
                                st.rerun(scope="fragment")

                    st.markdown("<hr style='opacity:0.08;margin:10px 0;'>", unsafe_allow_html=True)

                    # ── Estado de pago (marcar manual, ej. pagó en efectivo) ──
                    if j.get("mp_payment_id"):
                        st.caption(
                            f"ID de pago en MP: `{j['mp_payment_id']}`"
                            + ("" if _pago_ok else " — pago anterior, ya usado: no vuelve a habilitar al jugador")
                        )
                        if st.button(
                            "🔍 Ver detalle de este pago en Mercado Pago",
                            key=f"detalle_pago_{j['id']}",
                        ):
                            _mostrar_detalle_pago(j["mp_payment_id"], j["id"])
                    if _pago_ok:
                        st.success("💰 Inscripción pagada")
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

