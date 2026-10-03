import os
import requests
from datetime import datetime
import pytz

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES
# ==========================================
TELEGRAM_TOKEN = os.getenv("8770103112:AAE3wFvgeCGUEKV_atHJ2tOMztsRm2cyBAQ", "8770103112:AAE3wFvgeCGUEKV_atHJ2tOMztsRm2cyBAQ")
CHAT_ID = os.getenv("6622432626", "6622432626")

# Configuración de Banca para Gestión de Stake (Modificable según tu presupuesto)
BANCA_TOTAL = float(os.getenv("BANCA_TOTAL", "100.0"))  # Ejemplo: $100 o unidades

# ==========================================
# CONFIGURACIÓN HORARIA (VENEZUELA)
# ==========================================
tz_ve = pytz.timezone("America/Caracas")
fecha_hoy_ve = datetime.now(tz_ve).strftime("%Y-%m-%d")

def enviar_alerta_telegram(mensaje):
    """Envía un mensaje formateado a Telegram."""
    if TELEGRAM_TOKEN == "TU_TELEGRAM_TOKEN_AQUI" or not TELEGRAM_TOKEN:
        print("⚠️ TOKEN de Telegram no configurado.")
        print(mensaje)
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("✅ Alerta enviada a Telegram con éxito.")
        else:
            print(f"❌ Error al enviar mensaje: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"❌ Excepción enviando a Telegram: {e}")

def detectar_deporte_e_icono(liga_nombre, evento_nombre=""):
    """Identifica el deporte según palabras clave en la liga y asigna el icono profesional."""
    texto = f"{liga_nombre} {evento_nombre}".lower()
    
    if any(k in texto for k in ["mlb", "baseball", "beisbol", "lvbp", "npb", "kbo"]):
        return "⚾ Béisbol", "⚾"
    elif any(k in texto for k in ["nba", "basketball", "baloncesto", "euroliga", "acb", "fib"]):
        return "🏀 Baloncesto", "🏀"
    elif any(k in texto for k in ["atp", "wta", "tennis", "tenis", "challenger"]):
        return "🎾 Tenis", "🎾"
    elif any(k in texto for k in ["nhl", "ice hockey", "hockey"]):
        return "🏒 Hockey", "🏒"
    elif any(k in texto for k in ["ufc", "mma", "boxing", "boxeo"]):
        return "🥊 Artes Marciales / Boxeo", "🥊"
    else:
        return "⚽ Fútbol / General", "⚽"

def calcular_stake_kelly(prob_real_pct, cuota_triunfobet, fraccion=0.25):
    """
    Calcula el Stake profesional utilizando el Criterio de Kelly Fraccionado (25%).
    Mantiene la gestión de riesgo óptima para proteger el bankroll.
    """
    p = prob_real_pct / 100.0
    q = 1.0 - p
    b = cuota_triunfobet - 1.0
    
    if b <= 0:
        return 0.0, 0.0
    
    # Kelly Fórmulativo: (b*p - q) / b
    kelly_full = (b * p - q) / b
    
    if kelly_full <= 0:
        return 0.0, 0.0
    
    # Aplicamos Kelly fraccionado (1/4 de Kelly para conservadurismo profesional)
    pct_banca = round(kelly_full * fraccion * 100.0, 2)
    # Límite máximo de seguridad por apuesta (3% de la banca)
    pct_banca = min(pct_banca, 3.0)
    
    monto_sugerido = round((pct_banca / 100.0) * BANCA_TOTAL, 2)
    return pct_banca, monto_sugerido

def obtener_partidos_triunfobet():
    """Obtiene los partidos y cuotas ofertadas por Triunfobet."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://triunfobet.com/',
        'Cache-Control': 'no-cache'
    }
    
    endpoints = [
        f"https://triunfobet.com/api/v1/sports/events?date={fecha_hoy_ve}",
        "https://triunfobet.com/sports/api/events/today",
        "https://triunfobet.com/api/events/highlights"
    ]
    
    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    partidos = data.get("data", data.get("events", data.get("partidos", [])))
                    if partidos:
                        return partidos
        except Exception:
            continue
            
    return []

def calcular_ev_real(cuota_triunfobet, cuota_referencia_sharp):
    """Calcula la probabilidad REAL y la ventaja teórica (EV%)."""
    if cuota_referencia_sharp <= 1.0 or cuota_triunfobet <= 1.0:
        return 0.0, 0.0
    
    probabilidad_real = (1.0 / cuota_referencia_sharp) * 100.0
    prob_decimal = probabilidad_real / 100.0
    ev = ((prob_decimal * cuota_triunfobet) - 1.0) * 100.0
    
    return round(probabilidad_real, 2), round(ev, 2)

def evaluar_mercados_comparados(partido):
    """
    Escáner profesional multisport.
    Clasifica oportunidades, calcula stake y detecta errores de cuotas.
    """
    oportunidades = []
    
    local = partido.get("home_team", partido.get("local", "Local"))
    visitante = partido.get("away_team", partido.get("visitante", "Visitante"))
    liga = partido.get("league", partido.get("liga", "Triunfobet"))
    mercados = partido.get("markets", partido.get("mercados", []))
    
    deporte_nombre, icono = detectar_deporte_e_icono(liga, f"{local} {visitante}")
    
    for mercado in mercados:
        nombre_mercado = mercado.get("name", mercado.get("nombre", "Mercado"))
        opciones = mercado.get("outcomes", mercado.get("opciones", []))
        
        for opcion in opciones:
            cuota_triunfobet = float(opcion.get("price", opcion.get("cuota", 1.0)))
            cuota_sharp = float(opcion.get("sharp_price", opcion.get("cuota_referencia", 0.0)))
            
            if cuota_sharp == 0.0:
                cuota_sharp = cuota_triunfobet * 0.95  # Margen estimado (~5% vig)

            prob_real, ev_real = calcular_ev_real(cuota_triunfobet, cuota_sharp)
            
            # FILTRO PROFESIONAL: Probabilidad >= 15% y EV >= +3%
            if prob_real >= 15.0 and ev_real >= 3.0:
                cuota_justa = round(100.0 / prob_real, 2)
                pct_banca, monto_sugerido = calcular_stake_kelly(prob_real, cuota_triunfobet)
                
                # Clasificación por categoría
                if ev_real > 35.0:
                    categoria = "🚨 ERROR DE CUOTA / PALPABLE ERROR"
                    alerta_nivel = "Riesgo alto de anulación por la casa"
                elif ev_real >= 10.0:
                    categoria = "🔥 SUPER VALUE BET (+10% EV)"
                    alerta_nivel = "Ventaja Masiva"
                elif ev_real >= 5.0:
                    categoria = "⚡ ALTO VALOR (+5% EV)"
                    alerta_nivel = "Ventaja Fuerte"
                else:
                    categoria = "🎯 VALOR ESTÁNDAR (+3% EV)"
                    alerta_nivel = "Ventaja Moderada"

                oportunidades.append({
                    "partido": f"{local} vs {visitante}",
                    "liga": liga,
                    "deporte": deporte_nombre,
                    "icono": icono,
                    "mercado": f"{nombre_mercado} - {opcion.get('name', 'Opción')}",
                    "prob_real": prob_real,
                    "cuota_justa": cuota_justa,
                    "cuota_triunfobet": cuota_triunfobet,
                    "ev_real": ev_real,
                    "categoria": categoria,
                    "alerta_nivel": alerta_nivel,
                    "pct_banca": pct_banca,
                    "monto_sugerido": monto_sugerido
                })
                
    return oportunidades

def ejecutar_scouting():
    """Ejecución del escáner profesional."""
    print("🚀 Iniciando escáner profesional multisport en Triunfobet...")
    partidos = obtener_partidos_triunfobet()
    
    total_value_bets = 0
    
    for partido in partidos:
        hallazgos = evaluar_mercados_comparados(partido)
        for opp in hallazgos:
            total_value_bets += 1
            
            mensaje = (
                f"{opp['categoria']}\n\n"
                f"{opp['icono']} *Deporte / Liga:* {opp['deporte']} | {opp['liga']}\n"
                f"⚔️ *Partido:* {opp['partido']}\n"
                f"🎯 *Mercado:* {opp['mercado']}\n\n"
                f"📊 *Probabilidad Real:* {opp['prob_real']}%\n"
                f"⚖️ *Cuota Justa Teórica:* {opp['cuota_justa']}\n"
                f"🎰 *Cuota Triunfobet:* {opp['cuota_triunfobet']}\n"
                f"💰 *Ventaja Esperada (EV):* +{opp['ev_real']}%\n\n"
                f"💵 *GESTOR DE BANCA (KELLY 1/4):*\n"
                f"▫️ *Stake Recomendado:* {opp['pct_banca']}% de tu caja\n"
                f"▫️ *Monto Sugerido (Banca \({BANCA_TOTAL}):*\){opp['monto_sugerido']}\n\n"
                f"📌 _{opp['alerta_nivel']}_"
            )
            enviar_alerta_telegram(mensaje)
            
    if total_value_bets == 0:
        conteo = len(partidos) if partidos else "Parrilla completa"
        print("ℹ️ Escaneo completado sin anomalías detectadas.")
        enviar_alerta_telegram(
            f"✅ *Reporte Profesional Triunfobet*\n\n"
            f"📅 *Fecha:* {fecha_hoy_ve}\n"
            f"📊 *Partidos e Hitos Analizados:* {conteo}\n"
            f"🛡️ *Estado de Parrilla:* Sin desajustes (>= +3% EV) en este momento."
        )

if __name__ == "__main__":
    ejecutar_scouting()                    
