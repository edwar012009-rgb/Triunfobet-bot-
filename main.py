import os
import         
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
