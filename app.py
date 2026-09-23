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
    """Muestra un mensaje de bienvenida con 3 botones interactivos"""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "¡Hola! 👋 Bienvenido al bot de demostración de *Agencia Bot*.\n\n"
                    "🤖 Este es un prototipo interactivo. Recuerda que este flujo "
                    "se personaliza al 100% según las necesidades específicas de tu negocio.\n\n"
                    "¿Qué deseas explorar hoy?"
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
                        "reply": {"id": "btn_ejemplos", "title": "💡 Casos de uso"}
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
    """Maneja las respuestas de cada botón"""
    if btn_id == "btn_servicios":
        texto = (
            "🛠️ *Nuestros Servicios de Automatización:*\n\n"
            "1️⃣ *Bots a medida:* Flujos conversacionales interactivos con botones y menús.\n"
            "2️⃣ *Integraciones API:* Conexión con tu base de datos, CRM, Google Sheets o sistemas de pago.\n"
            "3️⃣ *Respuestas con Inteligencia Artificial:* Integración con modelos de IA para atención 24/7 sin guiones rígidos.\n\n"
            "📌 *Nota:* Todo se adapta a la lógica de tu empresa."
        )
    elif btn_id == "btn_ejemplos":
        texto = (
            "💡 *Casos de Uso Personalizables:*\n\n"
            "• *Restaurantes / Menú:* Catálogo digital, pedidos automatizados y reservas.\n"
            "• *Inmobiliarias & Citas:* Calificación de prospectos y agendamiento automático.\n"
            "• *Soporte & FAQ:* Atención a clientes frecuente en tiempo real.\n"
            "• *E-commerce:* Rastreo de pedidos y confirmación de compras."
        )
    elif btn_id == "btn_asesor":
        texto = (
            "👤 *Atención Personalizada:*\n\n"
            "Un especialista comercial se pondrá en contacto contigo muy pronto para "
            "analizar los requerimientos de tu negocio y diseñar una propuesta a tu medida.\n\n"
            "¡Gracias por probar nuestra demo!"
        )
    else:
        texto = "Opción no reconocida."

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": texto}
    }
    enviar_mensaje_raw(payload)


if __name__ == '__main__':
    app.run(port=5000)
