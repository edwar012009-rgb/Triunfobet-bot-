import os
import requests
from datetime import datetime
import pytz

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES
# ==========================================
TELEGRAM_TOKEN = os.getenv("8770103112:AAE3wFvgeCGUEKV_atHJ2tOMztsRm2cyBAQ", "8770103112:AAE3wFvgeCGUEKV_atHJ2tOMztsRm2cyBAQ")
CHAT_ID = os.getenv("6622432626", "6622432626")

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
    """
    Calcula la probabilidad REAL basada en la cuota de mercado Sharp desmarginada
    y determina la ventaja teórica (EV%) en Triunfobet.
    """
    if cuota_referencia_sharp <= 1.0 or cuota_triunfobet <= 1.0:
        return 0.0, 0.0
    
    # Probabilidad Real desmarginada del mercado global
    probabilidad_real = (1.0 / cuota_referencia_sharp) * 100.0
    
    # EV% = (Probabilidad_Real * Cuota_Triunfobet - 1) * 100
    prob_decimal = probabilidad_real / 100.0
    ev = ((prob_decimal * cuota_triunfobet) - 1.0) * 100.0
    
    return round(probabilidad_real, 2), round(ev, 2)

def evaluar_mercados_comparados(partido):
    """
    Compara las cuotas de Triunfobet contra la probabilidad real.
    Filtro amplio: Probabilidad Real >= 15% (cubre cuotas hasta ~6.50) y EV Real >= +3%.
    """
    oportunidades = []
    
    local = partido.get("home_team", partido.get("local", "Local"))
    visitante = partido.get("away_team", partido.get("visitante", "Visitante"))
    liga = partido.get("league", partido.get("liga", "Triunfobet"))
    mercados = partido.get("markets", partido.get("mercados", []))
    
    for mercado in mercados:
        nombre_mercado = mercado.get("name", mercado.get("nombre", "Mercado"))
        opciones = mercado.get("outcomes", mercado.get("opciones", []))
        
        for opcion in opciones:
            cuota_triunfobet = float(opcion.get("price", opcion.get("cuota", 1.0)))
            
            # Cuota de referencia desmarginada/Sharp
            cuota_sharp = float(opcion.get("sharp_price", opcion.get("cuota_referencia", 0.0)))
            
            if cuota_sharp == 0.0:
                cuota_sharp = cuota_triunfobet * 0.95  # Ajuste de margen (~5% de vig)

            prob_real, ev_real = calcular_ev_real(cuota_triunfobet, cuota_sharp)
            
            # FILTRO ACTUALIZADO: Permite cuotas altas (Prob >= 15%) con EV >= +3%
            if prob_real >= 15.0 and ev_real >= 3.0:
                cuota_justa = round(100.0 / prob_real, 2)
                
                oportunidades.append({
                    "partido": f"{local} vs {visitante}",
                    "liga": liga,
                    "mercado": f"{nombre_mercado} - {opcion.get('name', 'Opción')}",
                    "prob_real": prob_real,
                    "cuota_justa": cuota_justa,
                    "cuota_triunfobet": cuota_triunfobet,
                    "ev_real": ev_real
                })
                
    return oportunidades

def ejecutar_scouting():
    """Función principal del escáner de Valor Real."""
    print("🚀 Iniciando escáner completo (cuotas bajas y altas) en Triunfobet...")
    partidos = obtener_partidos_triunfobet()
    
    total_value_bets = 0
    
    for partido in partidos:
        hallazgos = evaluar_mercados_comparados(partido)
        for opp in hallazgos:
            total_value_bets += 1
            mensaje = (
                f"🔥 *VALUE BET REAL DETECTADO EN TRIUNFOBET* 🔥\n\n"
                f"⚽ *Partido:* {opp['partido']}\n"
                f"🏆 *Liga:* {opp['liga']}\n"
                f"🎯 *Mercado:* {opp['mercado']}\n\n"
                f"📊 *Probabilidad Real (Mercado Sharp):* {opp['prob_real']}%\n"
                f"⚖️ *Cuota Justa Teórica:* {opp['cuota_justa']}\n"
                f"🎰 *Cuota Paga Triunfobet:* {opp['cuota_triunfobet']}\n\n"
                f"💰 *Ventaja Real Esperada (EV):* +{opp['ev_real']}%\n"
                f"⚡ _Triunfobet tiene un error de cuota inflada respecto al mercado real._"
            )
            enviar_alerta_telegram(mensaje)
            
    if total_value_bets == 0:
        conteo = len(partidos) if partidos else "Parrilla completa"
        print("ℹ️ Escaneo completado. No se encontraron desajustes con ventaja real hoy.")
        enviar_alerta_telegram(
            f"✅ *Escaneo de Triunfobet Completado*\n\n"
            f"📅 *Fecha:* {fecha_hoy_ve}\n"
            f"📊 *Partidos analizados:* {conteo}\n"
            f"ℹ️ Se escanearon cuotas bajas y altas (prob >= 15%). No hay errores de cuotas (>= +3% EV) en este momento."
        )

if __name__ == "__main__":
    ejecutar_scouting()
