import streamlit as st
import replicate
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
import base64

# --- FUNCIÓN PARA CARGAR LOGO ---
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception:
        return ""

# --- FUNCIÓN PARA ENVIAR A TELEGRAM ---
def enviar_a_telegram(imagen_bytes, nombre_archivo):
    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    
    files = {'document': (nombre_archivo, imagen_bytes, 'image/png')}
    data = {'chat_id': chat_id, 'caption': '💎 Nuevo pedido listo para grabar (Ela App)'}
    
    try:
        r = requests.post(url, files=files, data=data)
        if r.status_code == 200:
            return True
        else:
            st.error(f"Error Telegram: {r.text}")
            return False
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return False

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ela Grabado Pro", page_icon="💎", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main-title { color: #1E3A8A; text-align: center; font-family: sans-serif; margin-top: -20px; }
    .subtitle { text-align: center; color: #6B7280; margin-bottom: 30px; }
    .stButton>button { width: 100%; background-color: #1E3A8A; color: white; border-radius: 8px; font-weight: bold; padding: 0.75rem; border: none; }
    .stButton>button:hover { background-color: #152C6B; }
    </style>
""", unsafe_allow_html=True)

# --- ENCABEZADO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("Logo Ela.png", use_column_width=True)
    except:
        pass

st.markdown('<h1 class="main-title">Ela Grabado de Joyería</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">✨ Sistema Automático: HD + Corte + Envío a Taller</p>', unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎛️ Panel de Control")
    usar_hd = st.checkbox("Activar HD (Super Resolución)", value=True)
    ayuda_sombras = st.slider("Revelar Sombras", 1.0, 2.0, 1.0)
    st.subheader("Acabado Láser")
    nitidez = st.slider("Nitidez", 0.0, 5.0, 2.0)
    contraste = st.slider("Contraste", 0.5, 3.0, 1.2)
    st.divider()
    st.markdown("Desarrollado para **Ela Live Laser Bar** 💎")

# --- INTERFAZ ---
st.markdown("### 📤 Sube la foto del cliente")
uploaded_file = st.file_uploader("", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Foto Original", use_column_width=True)

    # BOTÓN DE ACCIÓN
    if st.button("💎 PROCESAR Y ENVIAR AL TALLER"):
        
        if not st.secrets.get("REPLICATE_API_TOKEN"):
            st.error("⚠️ Faltan las llaves de Replicate.")
            st.stop()
        
        if not st.secrets.get("TELEGRAM_TOKEN"):
            st.warning("⚠️ Falta configurar Telegram. La imagen se procesará pero no se enviará automáticamente.")

        with st.status("🤖 Procesando pedido...", expanded=True) as status:
            try:
                # --- PROCESAMIENTO (Igual que antes) ---
                img_input = BytesIO(uploaded_file.getvalue())
                
                if ayuda_sombras > 1.0:
                    status.write("💡 Ajustando luz...")
                    img_temp = Image.open(uploaded_file).convert("RGB")
                    enhancer = ImageEnhance.Brightness(img_temp)
                    img_bright = enhancer.enhance(ayuda_sombras)
                    buf = BytesIO()
                    img_bright.save(buf, format="PNG")
                    buf.seek(0)
                    img_input = buf

                if usar_hd:
                    status.write("1️⃣ Mejorando calidad (HD)...")
                    output_upscale = replicate.run(
                        "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
                        input={"image": img_input, "scale": 2, "face_enhance": True}
                    )
                    
                    # Puente seguro
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

                status.write("2️⃣ Recortando fondo (Bria AI)...")
                output_bria = replicate.run(
                    "bria/remove-background",
                    input={"image": img_input, "preserve_alpha": True}
                )

                buffer_bg = BytesIO()
                if isinstance(output_bria, str):
                    resp = requests.get(output_bria)
                    buffer_bg.write(resp.content)
                elif hasattr(output_bria, 'read'):
                    buffer_bg.write(output_bria.read())
                
                buffer_bg.seek(0)
                img_sin_fondo = Image.open(buffer_bg)
                
                status.write("3️⃣ Finalizando para láser...")
                img_proc = img_sin_fondo.convert("RGBA")
                enhancer_c = ImageEnhance.Contrast(img_proc)
                img_proc = enhancer_c.enhance(contraste)
                enhancer_s = ImageEnhance.Sharpness(img_proc)
                img_proc = enhancer_s.enhance(nitidez)

                # Guardar resultado final
                buf_final = BytesIO()
                img_proc.save(buf_final, format="PNG")
                bytes_final = buf_final.getvalue()

                # --- ENVÍO AUTOMÁTICO A TELEGRAM ---
                if st.secrets.get("TELEGRAM_TOKEN"):
                    status.write("🚀 Enviando al Taller (Telegram)...")
                    enviado = enviar_a_telegram(bytes_final, "pedido_ela.png")
                    if enviado:
                        status.write("✅ ¡Enviado con éxito!")
                    else:
                        status.write("❌ Error al enviar (pero puedes descargarla abajo)")
                
                status.update(label="✅ ¡Proceso Terminado!", state="complete", expanded=False)
                
                # MOSTRAR RESULTADO
                st.divider()
                st.image(img_proc, use_column_width=True, caption="Resultado Final")
                
                st.download_button("⬇️ DESCARGAR MANUALMENTE", data=bytes_final, file_name="ela_laser_final.png", mime="image/png")
                
                if st.secrets.get("TELEGRAM_TOKEN"):
                    st.success("✨ La imagen ya fue enviada automáticamente al canal de Producción.")

            except Exception as e:
                st.error(f"Error: {e}")
