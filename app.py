import os
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==============================================================================
# CONFIGURACIONES Y VARIABLES GLOBALES DE SESIÓN
# ==============================================================================
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'mibot123')
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')

SESSION_DATA = {
    "token": None,
    "last_login": None
}

def obtener_token_valido():
    ahora = datetime.now()
    
    if SESSION_DATA["token"] and SESSION_DATA["last_login"]:
        tiempo_transcurrido = (ahora - SESSION_DATA["last_login"]).total_seconds()
        if tiempo_transcurrido < 480:
            return SESSION_DATA["token"]

    url_login = "https://backendteammx.yippeeagent.com:90/prod-api/login"
    payload = {
        "username": "5930685",
        "password": "siglo2026",
        "uuid": "419dac0e82834818a0ce05d069dbd467",
        "seller": True
    }
    headers_login = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es-419,es-VE;q=0.9,es;q=0.8,en-US;q=0.7,en;q=0.6,gl;q=0.5",
        "cache-control": "no-cache",
        "content-type": "application/json;charset=UTF-8",
        "Cookie": "sidebarStatus=0",
        "istoken": "false",
        "origin": "https://backendteammx.yippeeagent.com:90",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://backendteammx.yippeeagent.com:90/login?redirect=%2Findex",
        "repeatsubmit": "false",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    }

    try:
        res = requests.post(url_login, json=payload, headers=headers_login, timeout=12)
        try:
            data = res.json()
        except Exception:
            data = {"raw_text": res.text}

        nuevo_token = None
        if isinstance(data, dict):
            nuevo_token = data.get("token") or data.get("data", {}).get("token") or data.get("access_token")
        
        if nuevo_token:
            SESSION_DATA["token"] = nuevo_token
            SESSION_DATA["last_login"] = ahora
            return nuevo_token
        else:
            return None

    except Exception as e:
        return None

def consultar_ultimos_retiros(limit=3):
    """Consulta la API interna y devuelve los últimos N registros formateados correctamente."""
    token = obtener_token_valido()
    if not token:
        return "⚠️ Error de autenticación con el servidor central."

    ahora = datetime.now()
    hace_dos_dias = ahora - timedelta(days=2)
    begin_time = hace_dos_dias.strftime("%d-%m-%Y 00:00:00")
    end_time = ahora.strftime("%d-%m-%Y 23:59:59")

    url_target = "https://backendteammx.yippeeagent.com:90/prod-api/warteam/collect_record"
    
    # Se piden suficientes registros para capturar los últimos del arreglo
    params = {
        "pageNum": 1,
        "pageSize": 50,
        "captainId": "11332410",
        "type": 1,
        "params[beginTime]": begin_time,
        "params[endTime]": end_time
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    }

    # Mapa de estados numéricos a texto legible
    MAPA_ESTADOS = {
        6: "Apoyo realizado",
        3: "Pendiente",
        4: "Sin completar"
    }

    try:
        res = requests.get(url_target, params=params, headers=headers, timeout=12)
        data = res.json()
        
        rows = data.get("rows", [])
        if not rows:
            return "ℹ️ No se encontraron registros de retiros recientes."

        # Invertimos la lista para obtener primero los registros más recientes
        rows_recientes = list(reversed(rows))[:limit]

        mensaje = "📥 *ÚLTIMOS RETIROS REGISTRADOS*\n\n"
        for i, item in enumerate(rows_recientes, 1):
            jugador = item.get("name", "N/A")
            uid = item.get("uid", "N/A")
            cartas = item.get("num", 0)
            fecha = item.get("time") or "N/A"
            status_code = item.get("status")
            estado = MAPA_ESTADOS.get(status_code, f"Estado {status_code}")

            mensaje += f"*{i}. Jugador:* {jugador} (ID: {uid})\n"
            mensaje += f"   🃏 Cartas obtenidas: *{cartas}*\n"
            mensaje += f"   📅 Fecha: {fecha}\n"
            mensaje += f"   📌 Estado: {estado}\n\n"

        return mensaje.strip()

    except Exception as e:
        return f"⚠️ Error consultando los retiros: {str(e)}"

# ==============================================================================
# RUTA PUENTE API (GET)
# ==============================================================================
@app.route('/api/retiros', methods=['GET'])
def proxy_retiros():
    token = obtener_token_valido()
    if not token:
        return jsonify({"error": "No se pudo autenticar contra el servidor remoto"}), 500

    ahora = datetime.now()
    hace_dos_dias = ahora - timedelta(days=2)
    default_begin_time = hace_dos_dias.strftime("%d-%m-%Y 00:00:00")
    default_end_time = ahora.strftime("%d-%m-%Y 23:59:59")

    page_num = request.args.get('pageNum', default=1, type=int)
    page_size = request.args.get('pageSize', default=10, type=int)
    captain_id = request.args.get('captainId', default="11332410")
    type_val = request.args.get('type', default=1)
    begin_time = request.args.get('beginTime', default=default_begin_time)
    end_time = request.args.get('endTime', default=default_end_time)

    url_target = "https://backendteammx.yippeeagent.com:90/prod-api/warteam/collect_record"
    params = {
        "pageNum": page_num,
        "pageSize": page_size,
        "captainId": captain_id,
        "type": type_val,
        "params[beginTime]": begin_time,
        "params[endTime]": end_time
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url_target, params=params, headers=headers, timeout=12)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": "Fallo al consultar el backend de retiros", "details": str(e)}), 500

# ==============================================================================
# WEBHOOKS & RUTAS DE WHATSAPP
# ==============================================================================
@app.route('/privacy', methods=['GET'])
def privacy_policy():
    return "<h1>Política de Privacidad</h1><p>Servicio automatizado de WhatsApp.</p>", 200

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if data and data.get('object'):
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                messages = value.get('messages', [])
                
                if messages:
                    msg = messages[0]
                    sender_id = msg.get('from')
                    
                    if msg.get('type') == 'interactive':
                        interactive_type = msg['interactive'].get('type')
                        
                        # Manejo de respuesta de Lista
                        if interactive_type == 'list_reply':
                            opt_id = msg['interactive']['list_reply']['id']
                            procesar_opcion(sender_id, opt_id)
                        # Manejo de respuesta de Botones
                        elif interactive_type == 'button_reply':
                            opt_id = msg['interactive']['button_reply']['id']
                            procesar_opcion(sender_id, opt_id)
                    
                    elif msg.get('type') == 'text':
                        enviar_menu_principal(sender_id)
                        
        return jsonify({'status': 'EVENT_RECEIVED'}), 200
    return jsonify({'status': 'NOT_FOUND'}), 404

# ==============================================================================
# FUNCIONES MENÚ E INTERACCIÓN WHATSAPP
# ==============================================================================
def enviar_mensaje_raw(payload):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    requests.post(url, json=payload, headers=headers)

def enviar_menu_principal(to):
    """Utiliza mensaje tipo LISTA para soportar 4 opciones sin violar las políticas de Meta."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "🤖 Menú Principal"
            },
            "body": {
                "text": "Bienvenido a *Agencia Bot*. Selecciona una de las opciones de nuestro menú interactivo:"
            },
            "footer": {
                "text": "Selecciona una opción abajo 👇"
            },
            "action": {
                "button": "Ver Opciones",
                "sections": [
                    {
                        "title": "Consultas y Servicios",
                        "rows": [
                            {
                                "id": "btn_retiros",
                                "title": "📥 Últimos 3 Retiros",
                                "description": "Consultar historial de retiros en tiempo real"
                            },
                            {
                                "id": "btn_servicios",
                                "title": "🛠️ Servicios",
                                "description": "Conoce lo que podemos desarrollar"
                            },
                            {
                                "id": "btn_precios",
                                "title": "💳 Planes y Precios",
                                "description": "Detalles de inversión y mantenimiento"
                            },
                            {
                                "id": "btn_asesor",
                                "title": "👤 Contactar Asesor",
                                "description": "Hablar con un representante humano"
                            }
                        ]
                    }
                ]
            }
        }
    }
    enviar_mensaje_raw(payload)

def procesar_opcion(to, btn_id):
    if btn_id == "btn_retiros":
        # 1. Enviar mensaje de espera al usuario
        payload_espera = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": "🔍 Consultando los últimos 3 retiros en la base de datos..."}
        }
        enviar_mensaje_raw(payload_espera)

        # 2. Consultar la API
        texto_retiros = consultar_ultimos_retiros(limit=3)

        # 3. Enviar el resultado con botones para volver al menú
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": texto_retiros
                },
                "footer": {
                    "text": "Agencia Bot • Monitoreo de Retiros"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": "btn_retiros", "title": "🔄 Actualizar"}
                        },
                        {
                            "type": "reply",
                            "reply": {"id": "btn_menu", "title": "🔙 Menú Principal"}
                        }
                    ]
                }
            }
        }

    elif btn_id == "btn_servicios":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": (
                        "🛠️ *Lo que podemos desarrollar para tu empresa:*\n\n"
                        "1️⃣ *Bots de Menú Interactivo:* Flujos interactivos con respuestas instantáneas.\n"
                        "2️⃣ *Monitoreo de APIs / Retiros:* Extracción e integración de datos en tiempo real.\n"
                        "3️⃣ *Integración con IA:* Respuestas fluidas mediante Inteligencia Artificial.\n"
                        "4️⃣ *Conexión a Sistemas:* CRM, bases de datos o pasarelas de pago."
                    )
                },
                "footer": {"text": "¿Qué deseas hacer?"},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "btn_precios", "title": "💳 Ver Precios"}},
                        {"type": "reply", "reply": {"id": "btn_asesor", "title": "👤 Contactar Asesor"}},
                        {"type": "reply", "reply": {"id": "btn_menu", "title": "🔙 Menú Principal"}}
                    ]
                }
            }
        }

    elif btn_id == "btn_precios":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": (
                        "💳 *Planes de Inversión:*\n\n"
                        "🔹 *Plan Básico / Menú Interactivo:* $150 USD + $25/mes.\n"
                        "🔹 *Plan Pro / Integración API & Leads:* $300 USD + $50/mes.\n"
                        "🔹 *Plan IA / Personalizado:* Cotización según sistema."
                    )
                },
                "footer": {"text": "Servidores activos 24/7 con soporte"},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "btn_asesor", "title": "👤 Cotizar mi Bot"}},
                        {"type": "reply", "reply": {"id": "btn_menu", "title": "🔙 Menú Principal"}}
                    ]
                }
            }
        }

    elif btn_id == "btn_asesor":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": "👤 Un asesor te contactará a la brevedad. Por favor indícanos tu nombre o negocio."
                },
                "footer": {"text": "Agencia Bot"},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "btn_menu", "title": "🔙 Volver al Menú"}}
                    ]
                }
            }
        }

    elif btn_id == "btn_menu":
        enviar_menu_principal(to)
        return

    else:
        enviar_menu_principal(to)
        return

    enviar_mensaje_raw(payload)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
