import os
import requests
from datetime import datetime
import pytz

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES
# ==========================================
# Puedes colocarlos directamente entre comillas o usar variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8770103112:AAE3wFvgeCGUEKV_atHJ2tOMztsRm2cyBAQ")
CHAT_ID = os.getenv("CHAT_ID", "6622432626")

# ==========================================
# CONFIGURACIÓN HORARIA (VENEZUELA)
# ==========================================
tz_ve = pytz.timezone("America/Caracas")
fecha_hoy_ve = datetime.now(tz_ve).strftime("%Y-%m-%d")

def enviar_alerta_telegram(mensaje):
    """Envia mensaje formateado a Telegram."""
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

def obtener_partidos_del_dia():
    """
    Realiza una petición en vivo a Triunfobet forzando la fecha
    actual de Venezuela y usando encabezados anti-caché.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    
    # Parámetro de tiempo dinámico (?t=...) para obligar recarga en vivo
    timestamp_actual = datetime.now().timestamp()
    url = f"https://triunfobet.com/api/partidos?fecha={fecha_hoy_ve}&t={timestamp_actual}"
    
    print(f"🔄 Consultando partidos de hoy ({fecha_hoy_ve}) en Triunfobet...")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            datos = response.json()
            # Ajustar la clave según la respuesta exacta de la API de Triunfobet
            partidos = datos.get("data", datos.get("partidos", []))
            print(f"📊 Se encontraron {len(partidos)} partidos para el día de hoy.")
            return partidos
        else:
            print(f"⚠️ Error al conectar con Triunfobet: Código HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Ocurrió una excepción al consultar Triunfobet: {e}")
        return []

def calcular_ev(probabilidad_estimada, cuota_casa):
    """
    Fórmula: EV% = ((Probabilidad * Cuota) - 1) * 100
    """
    prob_dec = probabilidad_estimada / 100.0
    ev = ((prob_dec * cuota_casa) - 1.0) * 100.0
    return round(ev, 2)

def evaluar_mercados_partido(partido):
    """
    Escanea todos los mercados disponibles del partido en búsqueda de Value Bets.
    Filtro: Probabilidad >= 60% y EV >= +5%.
    """
    oportunidades = []
    
    # Datos básicos del partido
    local = partido.get("home_team", "Local")
    visitante = partido.get("away_team", "Visitante")
    liga = partido.get("league", "Liga Desconocida")
    mercados = partido.get("markets", partido.get("mercados", []))
    
    for mercado in mercados:
        nombre_mercado = mercado.get("name", "Mercado Generico")
        opciones = mercado.get("outcomes", mercado.get("opciones", []))
        
        for opcion in opciones:
            nombre_apuesta = opcion.get("name", "Opción")
            cuota = float(opcion.get("price", opcion.get("cuota", 1.0)))
            
            # Estimación de probabilidad implícita/analítica
            # (Se obtiene del sistema o se calcula sobre probabilidad del modelo)
            prob_estimada = float(opcion.get("probabilidad_estimada", 0.0))
            
            # Si la API no la provee directo, usamos cálculo de margen o métrica base
            if prob_estimada == 0.0 and cuota > 1.0:
                # Estimación referencial para evaluación de cuota desajustada
                prob_estimada = (1.0 / cuota) * 100.0
            
            ev = calcular_ev(prob_estimada, cuota)
            
            # CRITERIOS ESTRICTOS: Probabilidad >= 60% y EV >= 5%
            if prob_estimada >= 60.0 and ev >= 5.0:
                cuota_justa = round(100.0 / prob_estimada, 2) if prob_estimada > 0 else 0
                
                oportunidad = {
                    "partido": f"{local} vs {visitante}",
                    "liga": liga,
                    "mercado": f"{nombre_mercado} - {nombre_apuesta}",
                    "probabilidad": prob_estimada,
                    "cuota_justa": cuota_justa,
                    "cuota_triunfobet": cuota,
                    "ev": ev
                }
                oportunidades.append(oportunidad)
                
    return oportunidades

def ejecutar_scouting():
    """Función principal del escáner."""
    print("🚀 Iniciando escáner diario de Triunfobet...")
    partidos = obtener_partidos_del_dia()
    
    total_value_bets = 0
    
    for partido in partidos:
        hallazgos = evaluar_mercados_partido(partido)
        for opp in hallazgos:
            total_value_bets += 1
            mensaje = (
                f"🔥 *VALUE BET DETECTADO EN TRIUNFOBET* 🔥\n\n"
                f"⚽ *Partido:* {opp['partido']}\n"
                f"🏆 *Liga:* {opp['liga']}\n"
                f"🎯 *Mercado:* {opp['mercado']}\n\n"
                f"📈 *Probabilidad Estimada:* {opp['probabilidad']}%\n"
                f"⚖️ *Cuota Justa Teórica:* {opp['cuota_justa']}\n"
                f"🎰 *Cuota en Triunfobet:* {opp['cuota_triunfobet']}\n\n"
                f"💰 *Ventaja Esperada (EV):* +{opp['ev']}%\n"
                f"⚡ _Triunfobet está pagando por encima del valor real._"
            )
            enviar_alerta_telegram(mensaje)
            
    if total_value_bets == 0:
        print("ℹ️ Escaneo completado. No se encontraron apuestas que cumplan los criterios estrictos hoy.")
        # Opcional: Descomentar si deseas recibir notificación confirmando que se ejecutó sin hallazgos
        # enviar_alerta_telegram("✅ *Escaneo completado:* No se detectaron errores de cuotas >= 5% EV hoy.")

if __name__ == "__main__":
    ejecutar_scouting
    if total_value_bets == 0:
        print("ℹ️ Escaneo completado. No se encontraron apuestas que cumplan los criterios estrictos hoy.")
        # Quitamos el '#' de la línea de abajo para que SIEMPRE mande reporte a Telegram:
        enviar_alerta_telegram("✅ *Escaneo de Triunfobet completado:* No se detectaron desajustes de cuotas (>= 5% EV) para los partidos de hoy.")
