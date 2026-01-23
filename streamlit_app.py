import streamlit as st
import replicate
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
import base64
import random
import time
from replicate.exceptions import ReplicateError

# --- GESTIÓN DE ESTADO ---
if 'pedido_procesado' not in st.session_state:
    st.session_state.pedido_procesado = False
if 'resultado_imagen' not in st.session_state:
    st.session_state.resultado_imagen = None
if 'nombre_cliente_guardado' not in st.session_state:
    st.session_state.nombre_cliente_guardado = ""

# --- FUNCIÓN SEGURA CON AUTO-ESPERA ---
def ejecutar_replicate_seguro(modelo, inputs):
    # Intentamos hasta 3 veces si la red está ocupada
    for intento in range(3):
        try:
            return replicate.run(modelo, input=inputs)
        except ReplicateError as e:
            # Si el error es de velocidad (429) esperamos un poco
            if "429" in str(e):
                time.sleep(2)
                continue
            else:
                raise e # Si es otro error, avisamos

# --- FUNCIÓN REINICIAR ---
def reiniciar_app():
    st.session_state.pedido_procesado = False
    st.session_state.resultado_imagen = None
    st.session_state.nombre_cliente_guardado = ""
    st.rerun()

# --- UTILS (CON LÍMITE DE 1 MILLÓN DE PIXELES) ---
def redimensionar_imagen_segura(image, max_pixels=1000000): 
    width, height = image.size
    total_pixels = width * height
    if total_pixels > max_pixels:
        ratio = (max_pixels / total_pixels) ** 0.5
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image
    return image

def enviar_a_telegram(imagen_bytes, nombre, reverso):
    if "TELEGRAM_TOKEN" not in st.secrets or "TELEGRAM_CHAT_ID" not in st.secrets:
        return False
    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    
    mensaje = f"""🎡 *PEDIDO DESDE FERIA* 🎡
    
👤 *Cliente:* {nombre}
📝 *Reverso:* {reverso}
"""
    files = {'document': (f'ela_{nombre}.png', imagen_bytes, 'image/png')}
    data = {'chat_id': chat_id, 'caption': mensaje, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, files=files, data=data)
    except:
        pass

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Diseña tu Joya - Ela", page_icon="💎", layout="centered")

st.markdown("""
    <style>
    .main-title { color: #1E3A8A; text-align: center; font-family: sans-serif; margin-top: -20px; }
    .instruccion { text-align: center; color: #555; font-size: 0.9em; margin-bottom: 20px; }
    .stButton>button { width: 100%; background-color: #1E3A8A; color: white; border-radius: 20px; font-weight: bold; padding: 0.75rem; border: none; }
    .stButton>button:hover { background-color: #152C6B; }
    /* Botón secundario (Nuevo Cliente) en gris */
    .stButton>button.secondary { background-color: #6B7280; } 
    </style>
""", unsafe_allow_html=True)

# LOGO CENTRADO
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("Logo Ela.png", use_column_width=True)
    except:
        pass

st.markdown('<h1 class="main-title">¡Diseña tu Joya! ✨</h1>', unsafe_allow_html=True)

# ==========================================
#  VISTA CLIENTE (FORMULARIO)
# ==========================================
if not st.session_state.pedido_procesado:
    
    st.markdown('<p class="instruccion">Sube tu foto favorita y la prepararemos para grabarla en acero inoxidable al instante.</p>', unsafe_allow_html=True)

    # 1. NOMBRE
    nombre_cliente = st.text_input("👤 Tu Nombre", placeholder="Ej: Ana María")

    # 2. FOTO
    uploaded_file = st.file_uploader("📸 Sube tu Foto", type=['jpg', 'png', 'jpeg'])

    if uploaded_file:
        st.image(uploaded_file, caption="Tu foto seleccionada", width=150)
        
        # 3. REVERSO
        texto_reverso = st.text_input("📝 ¿Qué escribimos atrás? (Opcional)", placeholder="Ej: Una fecha, un nombre...")

        st.divider()
        
        # BOTÓN FINAL
        if st.button("✨ ¡LISTO! PROCESAR MI IMAGEN"):
            if not nombre_cliente:
                st.error("⚠️ Por favor escribe tu nombre.")
            else:
                if not st.secrets.get("REPLICATE_API_TOKEN"):
                    st.error("⚠️ Error de conexión.")
                    st.stop()

                with st.status("💎 Creando tu diseño mágico...", expanded=True) as status:
                    try:
                        # PROCESAMIENTO
                        image_original = Image.open(uploaded_file)
                        
                        # REDIMENSIONAR (SEGURIDAD)
                        img_safe = redimensionar_imagen_segura(image_original)
                        
                        buf_safe = BytesIO()
                        img_safe.save(buf_safe, format="PNG")
                        buf_safe.seek(0)
                        img_input = buf_safe
                        
                        # PASO 1: HD
                        status.write("✨ Mejorando calidad de la foto...")
                        output_upscale = ejecutar_replicate_seguro(
                            "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
                            {"image": img_input, "scale": 2, "face_enhance": True}
                        )
                        
                        buffer_hd = BytesIO()
                        if isinstance(output_upscale, str):
                            resp = requests.get(output_upscale)
                            buffer_hd.write(resp.content)
                        elif hasattr(output_upscale, 'read'):
                            buffer_hd.write(output_upscale.read())
                        elif hasattr(output_upscale, '__iter__'):
                            for chunk in output_upscale:
                                buffer_hd.write(chunk)
                        buffer_hd.seek(0)
                        img_input = buffer_hd

                        # PASO 2: RECORTAR
                        status.write("✂️ Recortando el fondo...")
                        output_bria = ejecutar_replicate_seguro(
                            "bria/remove-background",
                            {"image": img_input, "preserve_alpha": True}
                        )
                        
                        buffer_bg = BytesIO()
                        if isinstance(output_bria, str):
                            resp = requests.get(output_bria)
                            buffer_bg.write(resp.content)
                        elif hasattr(output_bria, 'read'):
                            buffer_bg.write(output_bria.read())
                        buffer_bg.seek(0)
                        img_sin_fondo = Image.open(buffer_bg)
                        
                        # PASO 3: LOOK ACERO
                        status.write("⚙️ Ajustando para el láser...")
                        img_proc = img_sin_fondo.convert("RGBA")
                        enhancer_c = ImageEnhance.Contrast(img_proc)
                        img_proc = enhancer_c.enhance(1.2)
                        enhancer_s = ImageEnhance.Sharpness(img_proc)
                        img_proc = enhancer_s.enhance(2.0)

                        # --- AQUI ESTABA EL ERROR DE ESPACIOS, YA CORREGIDO ---
                        buf_final = BytesIO()
                        img_proc.save(buf_final, format="PNG")
                        st.session_state.resultado_imagen = buf_final.getvalue()
                        st.session_state.nombre_cliente_guardado = nombre_cliente

                        # TELEGRAM
                        if st.secrets.get("TELEGRAM_TOKEN"):
                            status.write("🚀 Enviando al taller...")
                            enviar_a_telegram(st.session_state.resultado_imagen, nombre_cliente, texto_reverso if texto_reverso else "N/A")
                        
                        st.session_state.pedido_procesado = True
                        st.rerun()

                    except Exception as e:
                        if "CUDA" in str(e):
                             st.error("⚠️ Imagen demasiado pesada. Intenta recortarla un poco.")
                        else:
                             st.error("Hubo un pequeño error técnico. Intenta de nuevo.")

# ==========================================
#  VISTA CLIENTE (RESULTADO)
# ==========================================
else:
    st.balloons()
    nombre = st.session_state.nombre_cliente_guardado
    st.success(f"¡Excelente {nombre}! Tu imagen ya está lista.")
    
    st.image(st.session_state.resultado_imagen, use_column_width=True)
    
    st.info("💎 Muestra esta pantalla en el mostrador.")
    
    # --- BOTONES FINALES ---
    col_descarga, col_nuevo = st.columns(2)
    
    with col_descarga:
        st.download_button(
            label="⬇️ DESCARGAR MI IMAGEN", 
            data=st.session_state.resultado_imagen, 
            file_name=f"ela_diseno_{nombre}.png", 
            mime="image/png"
        )
    
    with col_nuevo:
        if st.button("🔄 NUEVO CLIENTE"):
            reiniciar_app()
