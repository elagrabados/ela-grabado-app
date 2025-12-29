import streamlit as st
import replicate
import requests
from PIL import Image, ImageEnhance
from io import BytesIO
import base64
import random

# --- GESTIÓN DE ESTADO (MEMORIA DE LA APP) ---
# Esto permite que la app recuerde si ya procesó un pedido o no
if 'pedido_procesado' not in st.session_state:
    st.session_state.pedido_procesado = False
if 'resultado_imagen' not in st.session_state:
    st.session_state.resultado_imagen = None
if 'datos_pedido_guardados' not in st.session_state:
    st.session_state.datos_pedido_guardados = {}
# Generamos los números del captcha solo una vez por sesión
if 'captcha_num1' not in st.session_state:
    st.session_state.captcha_num1 = random.randint(1, 10)
    st.session_state.captcha_num2 = random.randint(1, 10)

# --- FUNCIÓN PARA REINICIAR (NUEVO PEDIDO) ---
def reiniciar_app():
    st.session_state.pedido_procesado = False
    st.session_state.resultado_imagen = None
    st.session_state.datos_pedido_guardados = {}
    # Generar nuevo captcha
    st.session_state.captcha_num1 = random.randint(1, 10)
    st.session_state.captcha_num2 = random.randint(1, 10)
    st.rerun()

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

# --- FUNCIÓN 3: ENVIAR A TELEGRAM ---
def enviar_a_telegram(imagen_bytes, datos_pedido):
    if "TELEGRAM_TOKEN" not in st.secrets or "TELEGRAM_CHAT_ID" not in st.secrets:
        return False

    token = st.secrets["TELEGRAM_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    
    mensaje = f"""💎 *NUEVO PEDIDO ELA* 💎
    
👤 *Cliente:* {datos_pedido['nombre']}
📝 *Grabado Reverso:* {datos_pedido['reverso']}
💍 *Producto:* {datos_pedido['producto']}

💰 *Pago:* {datos_pedido['metodo_pago']}
💵 *Monto:* {datos_pedido['monto']} {datos_pedido['moneda']}
{f"🔢 *Ref:* {datos_pedido['referencia']}" if datos_pedido['referencia'] else ""}

🚚 *Entrega:* {datos_pedido['tipo_entrega']}
{f"📍 *Dirección:* {datos_pedido['direccion']}" if datos_pedido['direccion'] else ""}
{f"📞 *Teléfono:* {datos_pedido['telefono']}" if datos_pedido['telefono'] else ""}

✨ _Pedido verificado por Captcha_
"""
    files = {'document': ('pedido_ela.png', imagen_bytes, 'image/png')}
    data = {'chat_id': chat_id, 'caption': mensaje, 'parse_mode': 'Markdown'}
    
    try:
        r = requests.post(url, files=files, data=data)
        return r.status_code == 200
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
    .pago-box { background-color: #f0fdf4; padding: 15px; border-radius: 8px; border: 1px solid #bbf7d0; margin-bottom: 15px; }
    /* Estilo para el botón de nuevo pedido (Gris) */
    .stButton>button.secondary { background-color: #6B7280; }
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

# ==========================================
#  VISTA 1: FORMULARIO (Si no se ha procesado)
# ==========================================
if not st.session_state.pedido_procesado:
    
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

    # --- FORMULARIO ---
    st.markdown("### 1️⃣ Sube la foto")
    uploaded_file = st.file_uploader("", type=['jpg', 'png', 'jpeg'], label_visibility="collapsed")

    if uploaded_file:
        image_original = Image.open(uploaded_file)
        st.image(image_original, caption="Foto Original", use_column_width=True)
        st.divider()

        st.markdown("### 2️⃣ Datos del Pedido")
        col_nombre, col_prod = st.columns(2)
        with col_nombre:
            nombre_cliente = st.text_input("👤 Nombre del Cliente", placeholder="Ej: María Pérez")
        with col_prod:
            tipo_producto = st.selectbox("💍 Tipo de Pieza", ["Dije Corazón", "Dije Rectangular", "Dije Militar", "Pulsera", "Llavero", "Termo", "Otro"])

        texto_reverso = st.text_input("📝 Grabado reverso (Opcional)", placeholder="Ej: Te amo mamá 2025")

        st.markdown("#### 💳 Forma de Pago")
        lista_pagos = ["Divisas en Efectivo", "Pago Móvil (Bolívares)", "Binance", "Zelle", "Bancolombia", "Depósito Divisas", "Otro"]
        metodo_pago = st.selectbox("Seleccione método:", lista_pagos)

        moneda_simbolo = "$"
        mostrar_ref = False

        if metodo_pago == "Divisas en Efectivo":
            moneda_seleccion = st.radio("Moneda de entrega:", ["Dólares (USD)", "Pesos (COP)"], horizontal=True)
            moneda_simbolo = "USD" if "Dólares" in moneda_seleccion else "COP"
        elif metodo_pago == "Pago Móvil (Bolívares)":
            moneda_simbolo = "Bs"
            mostrar_ref = True
            st.markdown('<div class="pago-box">⬇️ <b>Datos Bancamiga</b><br>0414-7351289<br>26493459</div>', unsafe_allow_html=True)
        elif metodo_pago == "Binance":
            moneda_simbolo = "USDT"
            mostrar_ref = True
        elif metodo_pago == "Zelle":
            moneda_simbolo = "USD"
            mostrar_ref = True
        elif metodo_pago == "Bancolombia":
            moneda_simbolo = "COP"
            mostrar_ref = True

        c_monto, c_ref = st.columns(2)
        with c_monto:
            monto_pago = st.text_input(f"💰 Monto Total ({moneda_simbolo}) *", placeholder="0.00")
        with c_ref:
            referencia_pago = ""
            if mostrar_ref:
                referencia_pago = st.text_input("🔢 Nro Referencia / Capture", placeholder="Últimos 4 dígitos")

        st.markdown("#### 🚚 Entrega")
        tipo_entrega = st.radio("Método:", ["En persona (Tienda)", "Con Envío"], horizontal=True)

        direccion_envio = ""
        telefono_contacto = ""

        if tipo_entrega == "Con Envío":
            st.info("📦 Datos de Envío")
            direccion_envio = st.text_area("Dirección:", placeholder="Calle, Casa...")
            telefono_contacto = st.text_input("Teléfono:", placeholder="04XX-XXXXXXX")

        st.divider()
        
        # --- CAPTCHA SENCILLO ---
        st.markdown("#### 🛡️ Verificación de Seguridad")
        c_captcha1, c_captcha2 = st.columns([2, 1])
        with c_captcha1:
            st.write(f"¿Cuánto es **{st.session_state.captcha_num1} + {st.session_state.captcha_num2}**?")
        with c_captcha2:
            respuesta_captcha = st.number_input("Respuesta", min_value=0, max_value=100, step=1, label_visibility="collapsed")
        
        # --- BOTÓN DE PROCESAR ---
        if st.button("💎 PROCESAR Y ENVIAR PEDIDO"):
            
            # 1. Validar Captcha
            suma_correcta = st.session_state.captcha_num1 + st.session_state.captcha_num2
            
            if respuesta_captcha != suma_correcta:
                st.error("❌ La respuesta de la suma es incorrecta. Intenta de nuevo.")
            else:
                # 2. Validar Campos
                errores = []
                if not nombre_cliente: errores.append("Falta el Nombre del Cliente.")
                if not monto_pago: errores.append("Falta el Monto del Pago.")
                    
                if errores:
                    for error in errores: st.error(f"⚠️ {error}")
                else:
                    if not st.secrets.get("REPLICATE_API_TOKEN"):
                        st.error("⚠️ Error API.")
                        st.stop()

                    with st.status("🤖 Procesando pedido...", expanded=True) as status:
                        try:
                            # --- PROCESO IA ---
                            img_safe = redimensionar_imagen_segura(image_original)
                            buf_safe = BytesIO()
                            img_safe.save(buf_safe, format="PNG")
                            buf_safe.seek(0)
                            img_input = buf_safe
                            
                            if ayuda_sombras > 1.0:
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
                            
                            status.write("3️⃣ Finalizando...")
                            img_proc = img_sin_fondo.convert("RGBA")
                            enhancer_c = ImageEnhance.Contrast(img_proc)
                            img_proc = enhancer_c.enhance(contraste)
                            enhancer_s = ImageEnhance.Sharpness(img_proc)
                            img_proc = enhancer_s.enhance(nitidez)

                            # Guardar en Session State
                            buf_final = BytesIO()
                            img_proc.save(buf_final, format="PNG")
                            st.session_state.resultado_imagen = buf_final.getvalue()
                            
                            st.session_state.datos_pedido_guardados = {
                                "nombre": nombre_cliente,
                                "producto": tipo_producto,
                                "reverso": texto_reverso if texto_reverso else "N/A",
                                "metodo_pago": metodo_pago,
                                "moneda": moneda_simbolo,
                                "monto": monto_pago,
                                "referencia": referencia_pago,
                                "tipo_entrega": tipo_entrega,
                                "direccion": direccion_envio,
                                "telefono": telefono_contacto
                            }

                            # --- TELEGRAM ---
                            if st.secrets.get("TELEGRAM_TOKEN"):
                                status.write("🚀 Enviando recibo a Telegram...")
                                enviar_a_telegram(st.session_state.resultado_imagen, st.session_state.datos_pedido_guardados)
                            
                            status.update(label="✅ ¡Listo!", state="complete")
                            
                            # CAMBIAR ESTADO A PROCESADO Y RECARGAR
                            st.session_state.pedido_procesado = True
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")

# ==========================================
#  VISTA 2: RESULTADO (Éxito)
# ==========================================
else:
    st.balloons() # 🎉 Efecto de celebración
    st.success(f"✅ ¡Pedido de {st.session_state.datos_pedido_guardados['nombre']} enviado correctamente!")
    
    st.markdown("### 🖼️ Resultado Final")
    # Mostramos la imagen guardada en memoria
    st.image(st.session_state.resultado_imagen, caption="Listo para grabar", use_column_width=True)
    
    # Columnas para los botones finales
    col_descargar, col_nuevo = st.columns(2)
    
    with col_descargar:
        st.download_button(
            label="⬇️ DESCARGAR IMAGEN", 
            data=st.session_state.resultado_imagen, 
            file_name=f"pedido_{st.session_state.datos_pedido_guardados['nombre']}.png", 
            mime="image/png"
        )
        
    with col_nuevo:
        # Este botón reinicia la app para el siguiente cliente
        if st.button("🔄 PROCESAR NUEVO PEDIDO"):
            reiniciar_app()
    
    st.info("ℹ️ La pantalla se ha limpiado por seguridad. Si necesitas hacer otro pedido, dale al botón de arriba.")
