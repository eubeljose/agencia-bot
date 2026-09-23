import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuraciones existentes
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'mibot123')
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')

@app.route('/privacy', methods=['GET'])
def privacy_policy():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Política de Privacidad - Agencia Bot</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; color: #333; }
            h1 { color: #075e54; }
        </style>
    </head>
    <body>
        <h1>Política de Privacidad</h1>
        <p>En <strong>Agencia Bot</strong> respetamos y protegemos la privacidad de nuestros usuarios.</p>
        <h2>1. Información que recopilamos</h2>
        <p>Recopilamos únicamente el número de teléfono y los mensajes de texto enviados voluntariamente por los usuarios a través de WhatsApp para brindar respuestas automáticas.</p>
        <h2>2. Uso de la información</h2>
        <p>La información recibida se procesa en tiempo real exclusivamente para generar respuestas y no se comparte con terceros.</p>
        <h2>3. Almacenamiento y Seguridad</h2>
        <p>No almacenamos historiales de chat ni datos personales sensibles de forma permanente en servidores externos.</p>
        <h2>4. Contacto</h2>
        <p>Si tienes preguntas sobre esta política, puedes contactarnos a través de nuestros canales oficiales.</p>
    </body>
    </html>
    """, 200

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
                    
                    # 1. Si el usuario hace clic en un botón interactivo
                    if msg.get('type') == 'interactive':
                        btn_id = msg['interactive']['button_reply']['id']
                        procesar_opcion(sender_id, btn_id)
                    
                    # 2. Si el usuario envía un mensaje de texto normal
                    elif msg.get('type') == 'text':
                        enviar_menu_principal(sender_id)
                        
        return jsonify({'status': 'EVENT_RECEIVED'}), 200
    return jsonify({'status': 'NOT_FOUND'}), 404


def enviar_mensaje_raw(payload):
    """Envía la solicitud a la API oficial de Meta en WhatsApp Cloud"""
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    requests.post(url, json=payload, headers=headers)


def enviar_menu_principal(to):
    """Muestra el menú de bienvenida con los servicios de tu agencia"""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "¡Hola! 👋 Bienvenido a *Agencia Bot*.\n\n"
                    "Desarrollamos asistentes virtuales e integraciones de WhatsApp a la medida de tu negocio para automatizar tus ventas y atención 24/7.\n\n"
                    "💡 *Estás interactuando con un bot en tiempo real.* Selecciona una opción para conocer nuestros planes:"
                )
            },
            "footer": {
                "text": "Agencia Bot • Soluciones Automatizadas"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": "btn_servicios", "title": "🛠️ Servicios"}
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "btn_precios", "title": "💳 Planes y Precios"}
                    },
                    {
                        "type": "reply",
                        "reply": {"id": "btn_asesor", "title": "👤 Contactar Asesor"}
                    }
                ]
            }
        }
    }
    enviar_mensaje_raw(payload)


def procesar_opcion(to, btn_id):
    """Responde con detalle y siempre incluye botones al final para mantener la navegación activa"""
    
    if btn_id == "btn_servicios":
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": (
                        "🛠️ *Lo que podemos desarrollar para tu empresa:*\n\n"
                        "1️⃣ *Bots de Menú Interactivo:* Flujos como este con botones rápidos, catálogos y respuestas frecuentes.\n"
                        "2️⃣ *Captación de Prospectos:* Formularios automáticos para agendar citas o cotizaciones.\n"
                        "3️⃣ *Integración con IA:* Respuestas inteligentes usando Inteligencia Artificial para atención fluida sin guiones rígidos.\n"
                        "4️⃣ *Conexión a Sistemas:* Vinculación con tu base de datos, CRM, Google Sheets o pasarelas de pago.\n\n"
                        "📌 *Nota:* Todos nuestros desarrollos son 100% personalizados."
                    )
                },
                "footer": {
                    "text": "¿Qué te gustaría hacer ahora?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": "btn_precios", "title": "💳 Ver Precios"}
                        },
                        {
                            "type": "reply",
                            "reply": {"id": "btn_asesor", "title": "👤 Contactar Asesor"}
                        },
                        {
                            "type": "reply",
                            "reply": {"id": "btn_menu", "title": "🔙 Menú Principal"}
                        }
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
                        "💳 *Nuestros Planes de Inversión:*\n\n"
                        "🔹 *Plan Básico / Menú Interactivo*\n"
                        "• Configuración e instalación de la API oficial.\n"
                        "• Flujo interactivo con botones (hasta 5 secciones).\n"
                        "• *Inversión:* $150 USD (pago único) + $35/mes de mantenimiento y servidor.\n\n"
                        "🔹 *Plan Pro / Captación y Flujos*\n"
                        "• Todo lo del plan básico + captura automática de datos (leads).\n"
                        "• Integración con Google Sheets o correo.\n"
                        "• *Inversión:* $300 USD (pago único) + $50/mes.\n\n"
                        "🔹 *Plan Personalizado / IA*\n"
                        "• Bot inteligente con Inteligencia Artificial o integración a sistemas/CRM.\n"
                        "• Cotización según requerimientos."
                    )
                },
                "footer": {
                    "text": "El plan mensual incluye servidor activo 24/7 y soporte."
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": "btn_asesor", "title": "👤 Cotizar mi Bot"}
                        },
                        {
                            "type": "reply",
                            "reply": {"id": "btn_servicios", "title": "🛠️ Ver Servicios"}
                        },
                        {
                            "type": "reply",
                            "reply": {"id": "btn_menu", "title": "🔙 Menú Principal"}
                        }
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
                    "text": (
                        "👤 *Atención Personalizada:*\n\n"
                        "Un especialista de nuestro equipo se pondrá en contacto contigo en breve para evaluar las necesidades de tu negocio y diseñar una demostración a tu medida.\n\n"
                        "Si deseas agilizar el proceso, por favor escríbenos a continuación el nombre de tu empresa o tipo de negocio. 🚀"
                    )
                },
                "footer": {
                    "text": "Agencia Bot"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": "btn_menu", "title": "🔙 Volver al Menú"}
                        }
                    ]
                }
            }
        }

    else:
        # Si presiona "Volver al Menú" o cualquier otra opción
        enviar_menu_principal(to)
        return

    enviar_mensaje_raw(payload)


if __name__ == '__main__':
    app.run(port=5000)
