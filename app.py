import os
import sys
import types
import time
import glob
import json
from PIL import Image
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS

# ⚙️ Parche para Python 3.12 (soluciona el error "No module named 'cgi'")
sys.modules['cgi'] = types.ModuleType('cgi')

from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho
from gtts import gTTS
from googletrans import Translator


# ----------------- FUNCIONES MQTT -----------------
def on_publish(client, userdata, result):
    print("El dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(1)
    message_received = str(message.payload.decode("utf-8"))
    st.write("Mensaje recibido:", message_received)


# ----------------- CONFIGURACIÓN MQTT -----------------
broker = "broker.mqttdashboard.com"
port = 1883
client_id = "GIT-santiago"

client1 = paho.Client(client_id)
client1.on_message = on_message


# ----------------- INTERFAZ STREAMLIT -----------------
st.title("🎤 INTERFACES MULTIMODALES")
st.subheader("CONTROL POR VOZ")

# Mostrar imagen
if os.path.exists("voice_ctrl.jpg"):
    image = Image.open("voice_ctrl.jpg")
    st.image(image, width=200)
else:
    st.warning("No se encontró la imagen 'voice_ctrl.jpg' en el directorio.")

st.write("Toca el botón y habla:")

# Botón de inicio de reconocimiento de voz
stt_button = Button(label="🎙️ Iniciar reconocimiento", width=200)

# Código JavaScript que activa el micrófono del navegador
stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
"""))

# Captura del texto hablado
result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# ----------------- PROCESAMIENTO DE RESULTADO -----------------
if result:
    if "GET_TEXT" in result:
        texto = result.get("GET_TEXT").strip()
        st.success(f"🎧 Texto reconocido: {texto}")

        # Envío del comando al broker MQTT
        client1.on_publish = on_publish
        client1.connect(broker, port)
        message = json.dumps({"Act1": texto})
        ret = client1.publish("voice_ctrl", message)
        st.info(f"Mensaje enviado al tópico 'voice_ctrl': {message}")

        # Generar audio del texto (opcional)
        try:
            os.makedirs("temp", exist_ok=True)
            tts = gTTS(text=texto, lang='es')
            tts.save("temp/voz.mp3")
            st.audio("temp/voz.mp3", format="audio/mp3")
        except Exception as e:
            st.error(f"No se pudo generar el audio: {e}")
