from flask import Flask, request, jsonify

app = Flask(__name__)

# Token de seguridad que tú inventas para identificarte con Meta
VERIFY_TOKEN = "mibot123"

# 1. Ruta para que Meta VERIFIQUE tu servidor (petición GET)
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("WEBHOOK VERIFICADO CON ÉXITO")
        return challenge, 200
    else:
        return "Token incorrecto", 403

# 2. Ruta para RECIBIR los mensajes de los usuarios (petición POST)
@app.route('/webhook', methods=['POST'])
def receive_message():
    data = request.get_json()
    print("MENSAJE RECIBIDO DE META:")
    print(data)
    return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    # Arranca el servidor en el puerto 3000
    app.run(port=3000, debug=True)
