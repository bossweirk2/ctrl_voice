import os
import sys
import types
import time
import json
from PIL import Image
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho
from gtts import gTTS

# ⚙️ Parche para Python 3.12
sys.modules['cgi'] = types.ModuleType('cgi')

# ----------------- CONFIGURACIÓN MQTT -----------------
broker = "broker.mqttdashboard.com"
port = 1883
client_id = "nebula7_voice_module"

client1 = paho.Client(client_id)

def on_publish(client, userdata, result):
    print("🛰️ Transmisión vocal enviada con éxito.")

def on_message(client, userdata, message):
    global message_received
    time.sleep(1)
    message_received = str(message.payload.decode("utf-8"))
    st.markdown(f"<span style='color:#00FFFF;'>📡 Respuesta del núcleo:</span> `{message_received}`", unsafe_allow_html=True)

client1.on_message = on_message

# ----------------- CONFIGURACIÓN VISUAL -----------------
st.set_page_config(page_title="Nebula-7 | Módulo de Voz", page_icon="🎙️", layout="centered")

st.markdown("""
    <style>
    body {
        background: radial-gradient(circle at 20% 20%, #0f2027, #203a43, #2c5364);
        color: #00ffff;
        font-family: 'Share Tech Mono', monospace;
    }
    .stButton>button {
        background-color: #0b132b;
        color: #00ffff;
        border: 2px solid #00ffff;
        border-radius: 12px;
        padding: 0.6em 1.2em;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1b2a4e;
        color: #76e3ff;
        box-shadow: 0 0 15px #00ffff;
    }
    .title {
        text-align: center;
        color: #00ffff;
        text-shadow: 0 0 10px #00ffff;
        font-size: 32px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #76e3ff;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- INTERFAZ -----------------
st.markdown("<div class='title'>🪐 Estación Nebula-7</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Módulo de Comando por Voz - Unidad AURORA</div>", unsafe_allow_html=True)
st.markdown("---")

# Mostrar imagen decorativa
if os.path.exists("voice_ctrl.jpg"):
    image = Image.open("voice_ctrl.jpg")
    st.image(image, width=250, caption="Terminal de voz de la IA AURORA")
else:
    st.warning("🛰️ Imagen 'voice_ctrl.jpg' no encontrada en el directorio.")

st.markdown("### 🎙️ Envío de Comando Vocal")
st.write("Haz clic y dicta tu instrucción al sistema:")

# ----------------- BOTÓN DE RECONOCIMIENTO -----------------
stt_button = Button(label="🎤 Iniciar transmisión vocal", width=250)

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

# ----------------- PROCESAMIENTO DEL COMANDO -----------------
if result and "GET_TEXT" in result:
    texto = result.get("GET_TEXT").strip()
    st.success(f"🧠 AURORA detectó el comando: “{texto}”")

    # Envío del comando al broker MQTT
    client1.on_publish = on_publish
    client1.connect(broker, port)
    message = json.dumps({"VoiceCommand": texto})
    client1.publish("nebula7/voice_channel", message)
    st.info(f"📤 Comando transmitido a `nebula7/voice_channel`")

    # Generar respuesta de voz
    try:
        os.makedirs("temp", exist_ok=True)
        tts = gTTS(text=f"Comando recibido: {texto}", lang='es')
        audio_path = "temp/respuesta_aurora.mp3"
        tts.save(audio_path)
        st.audio(audio_path, format="audio/mp3")
        st.markdown("<p style='color:#76e3ff;'>🔊 AURORA: Comando procesado correctamente.</p>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"No se pudo generar el audio: {e}")

# ----------------- PIE DE PÁGINA -----------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#00ffff; font-size:13px;'>"
    "Nebula-7 Voice Command Module — Unidad AURORA v1.0<br>"
    "Desarrollado por Santiago Velásquez 🪐"
    "</p>",
    unsafe_allow_html=True
)
