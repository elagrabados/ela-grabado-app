import streamlit as st
import replicate
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
import base64

# --- FUNCIÓN 1: CARGAR LOGO ---
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception:
        return ""

# --- FUNCIÓN 2: REDIMENSIONAR SEGURA ---
def redimensionar_imagen_segura(image, max_pixels=2000000):
    width, height = image.size
    total_pixels = width * height
    if total_pixels > max_pixels:
        ratio = (max_pixels / total_pixels) ** 0.5
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return image
    return image

# --- FUNCIÓN 3: ENVIAR A TELEGRAM (CON DATOS COMPLETOS) ---
def enviar_a_telegram(imagen_bytes, datos_pedido):
    if "TELEGRAM_TOKEN" not in st.secrets or "TELEGRAM_CHAT_ID" not in st.secrets:
        return False

    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    
    # Construimos el mensaje del recibo
    mensaje = f"""💎 *NUEVO PEDIDO ELA* 💎
    
👤 *Cliente:* {datos_pedido['nombre']}
📝 *Grabado Reverso:* {datos_pedido['reverso']}

💰 *Forma de Pago:* {datos_pedido['metodo_pago']}
{f"💸 *Monto Bs:* {datos_pedido['monto_bs']}" if datos_pedido['monto_bs'] else ""}

🚚 *Entrega:* {datos_pedido['tipo_entrega']}
{f"📍 *Dirección:* {datos_pedido['direccion']}" if datos_pedido['direccion'] else ""}
{f"📞 *Teléfono:* {datos_pedido['telefono']}" if datos_pedido['telefono'] else ""}

✨ _Pedido generado desde la App_
"""

    files = {'document': ('pedido_ela.png', imagen_bytes, 'image/png')}
    # parse_mode='Markdown' permite poner negritas
    data = {'chat_id': chat_id, 'caption': mensaje, 'parse_mode': 'Markdown'}
    
    try:
        r = requests.post(url, files=files, data=data)
        if r.status_code == 200:
            return True
        else:
            return False
    except Exception:
        return False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ela Grabado Pro", page_icon="💎", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main-title { color: #1E3A8A; text-align: center; font-family: sans-serif; margin-top: -20px; }
    .subtitle { text-align: center; color: #6B7280; margin-bottom: 30px; }
    .stButton>button { width: 100%; background-color: #1E3A8A; color: white; border-radius: 8px; font-weight: bold; padding: 0.75rem; border: none; }
    .stButton>button:hover { background-color: #152C6B; }
    /* Estilo para los datos de pago */
    .pago-box { background-color: #f0fdf4; padding: 15px; border-radius: 8px; border: 1px solid #bbf7d0; margin-bottom: 15px; }
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
st.markdown('<p class="subtitle">✨ Sistema de Pedidos y Diseño</p>', unsafe_allow_html=True)

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎛️ Panel de Imagen")
    usar_hd = st.checkbox("Activar HD (Super Resolución)", value=True)
    ayuda_sombras = st.slider("Revelar Sombras", 1.0, 2.0, 1.0)
    st.subheader("Acabado Láser")
    nitidez = st.slider("Nitidez", 0.0, 5.0, 2.0)
    contraste = st.slider("Contraste", 0.5, 3.0, 1.2)
    st.divider()
    st.markdown("Desarrollado para **Ela Live Laser Bar** 💎")

# --- INTERFAZ PRINCIPAL ---

# 1. CARGA DE FOTO
st.markdown("### 1️⃣ Sube la foto")
uploaded_file = st.file_uploader("", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")

if uploaded_file:
    image_original = Image.open(uploaded_file)
    st.image(image_original, caption="Foto Original", use_column_width=True)

    st.divider()

    # 2. DATOS DEL PEDIDO (NUEVA SECCIÓN)
    st.markdown("### 2️⃣ Datos del Pedido")
    
    col_nombre, col_reverso = st.columns(2)
    with col_nombre:
        nombre_cliente = st.text_input("Nombre del Cliente", placeholder="Ej: María Pérez")
    with col_reverso:
        texto_reverso = st.text_input("Grabado parte de atrás (Opcional)", placeholder="Ej: Te amo mamá 2025")

    # --- SECCIÓN DE PAGOS ---
    st.markdown("#### 💳 Forma de Pago")
    metodo_pago = st.selectbox(
        "Seleccione método:",
        ["Pago Móvil (Bolívares)", "Divisas en Efectivo", "Binance", "Zelle", "Bancolombia", "Depósito Divisas", "Otro"]
    )

    monto_bs = ""
    if metodo_pago == "Pago Móvil (Bolívares)":
        st.markdown('<div class="pago-box">⬇️ <b>Datos para Pago Móvil</b> (Copia y pega)</div>', unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("Banco")
            st.code("Bancamiga", language=None)
        with c2:
            st.caption("Teléfono")
            st.code("0414-7351289", language=None)
        with c3:
            st.caption("Cédula")
            st.code("26493459", language=None)
            
        monto_bs = st.text_input("💰 Monto transferido (Bs):", placeholder="Ej: 1500.00")
    
    elif metodo_pago == "Otro":
        otro_metodo = st.text_input("Especifique el método:")
        if otro_metodo:
            metodo_pago = f"Otro: {otro_metodo}"

    # --- SECCIÓN DE ENTREGA ---
    st.markdown("#### 🚚 Entrega")
    tipo_entrega = st.radio("Método de entrega:", ["En persona (Tienda)", "Con Envío"], horizontal=True)

    direccion_envio = ""
    telefono_contacto = ""

    if tipo_entrega == "Con Envío":
        st.info("📦 Datos para el delivery/envío")
        direccion_envio = st.text_area("Dirección exacta:", placeholder="Calle, Casa, Punto de referencia...")
        telefono_contacto = st.text_input("Teléfono de quien recibe:", placeholder="04XX-XXXXXXX")

    st.divider()

    # 3. BOTÓN DE ACCIÓN
    # Validamos que al menos pongan el nombre
    if st.button("💎 PROCESAR Y ENVIAR PEDIDO"):
        
        if not nombre_cliente:
            st.error("⚠️ Por favor escribe el Nombre del Cliente antes de procesar.")
        else:
            if not st.secrets.get("REPLICATE_API_TOKEN"):
                st.error("⚠️ Faltan las llaves de Replicate.")
                st.stop()

            with st.status("🤖 Procesando pedido...", expanded=True) as status:
                try:
                    # --- RECOPILAR DATOS ---
                    datos_pedido = {
                        "nombre": nombre_cliente,
                        "reverso": texto_reverso if texto_reverso else "N/A",
                        "metodo_pago": metodo_pago,
                        "monto_bs": monto_bs,
                        "tipo_entrega": tipo_entrega,
                        "direccion": direccion_envio,
                        "telefono": telefono_contacto
                    }

                    # --- PROCESAMIENTO IMAGEN (Igual que antes) ---
                    img_safe = redimensionar_imagen_segura(image_original)
                    buf_safe = BytesIO()
                    img_safe.save(buf_safe, format="PNG")
                    buf_safe.seek(0)
                    img_input = buf_safe
                    
                    if ayuda_sombras > 1.0:
                        status.write("💡 Ajustando luz...")
                        img_temp = Image.open(img_input).convert("RGB")
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

                    status.write("2️⃣ Recortando fondo...")
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
                    
                    status.write("3️⃣ Finalizando diseño...")
                    img_proc = img_sin_fondo.convert("RGBA")
                    enhancer_c = ImageEnhance.Contrast(img_proc)
                    img_proc = enhancer_c.enhance(contraste)
                    enhancer_s = ImageEnhance.Sharpness(img_proc)
                    img_proc = enhancer_s.enhance(nitidez)

                    buf_final = BytesIO()
                    img_proc.save(buf_final, format="PNG")
                    bytes_final = buf_final.getvalue()

                    # --- ENVÍO A TELEGRAM ---
                    telegram_ok = False
                    if st.secrets.get("TELEGRAM_TOKEN"):
                        status.write("🚀 Enviando recibo a Telegram...")
                        telegram_ok = enviar_a_telegram(bytes_final, datos_pedido)
                    
                    status.update(label="✅ ¡Pedido Enviado!", state="complete", expanded=False)
                    
                    # RESULTADO
                    st.divider()
                    st.success(f"¡Listo! Pedido de {nombre_cliente} procesado.")
                    st.image(img_proc, use_column_width=True, caption="Resultado Final")
                    
                    st.download_button("⬇️ DESCARGAR IMAGEN", data=bytes_final, file_name=f"pedido_{nombre_cliente.replace(' ','_')}.png", mime="image/png")
                    
                    if telegram_ok:
                        st.info("✨ Todos los datos del pedido ya están en el canal de Telegram.")

                except Exception as e:
                    st.error(f"Error: {e}")
