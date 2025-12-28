import streamlit as st
import replicate
import requests
from PIL import Image, ImageEnhance
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ela Grabado Pro", page_icon="💎", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main-title { color: #1E3A8A; text-align: center; font-family: sans-serif; }
    .stButton>button { width: 100%; background-color: #1E3A8A; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">Ela Grabado de Joyería</h1>', unsafe_allow_html=True)
st.info("✨ Flujo Pro: Super Resolución (HD) + Corte Bria AI")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎛️ Panel de Control")
    
    st.subheader("1. Calidad de Imagen")
    usar_hd = st.checkbox("Activar Super Resolución (HD)", value=True, help="Aumenta el tamaño y define rostros antes de cortar")
    
    st.subheader("2. Asistente de Luz")
    ayuda_sombras = st.slider("Revelar Sombras", 1.0, 2.0, 1.0, help="Sube esto solo si la ropa oscura se mezcla con el fondo")
    
    st.subheader("3. Acabado Láser")
    nitidez = st.slider("Nitidez", 0.0, 5.0, 2.0)
    contraste = st.slider("Contraste", 0.5, 3.0, 1.2)
    
    st.divider()
    st.markdown("Desarrollado para **Ela Live Laser Bar**")

# --- INTERFAZ PRINCIPAL ---
uploaded_file = st.file_uploader("📂 Sube la foto Original", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Foto Original", use_column_width=True)

    if st.button("💎 PROCESAR IMAGEN COMPLETA"):
        
        if not st.secrets.get("REPLICATE_API_TOKEN"):
            st.error("⚠️ Faltan las llaves de la API.")
            st.stop()

        with st.status("🤖 Iniciando proceso de alta calidad...", expanded=True) as status:
            
            try:
                # --- PREPARACIÓN INICIAL ---
                # Convertimos el archivo subido en bytes para poder manipularlo
                img_input = BytesIO(uploaded_file.getvalue())
                
                # SI SE ACTIVÓ EL FLASH DIGITAL (Slider > 1.0)
                if ayuda_sombras > 1.0:
                    status.write("💡 Revelando sombras...")
                    img_temp = Image.open(uploaded_file).convert("RGB")
                    enhancer_pre = ImageEnhance.Brightness(img_temp)
                    img_bright = enhancer_pre.enhance(ayuda_sombras)
                    
                    # Sobrescribimos el input con la versión iluminada
                    buf_bright = BytesIO()
                    img_bright.save(buf_bright, format="PNG")
                    buf_bright.seek(0)
                    img_input = buf_bright

                # PASO 1: SUPER RESOLUCIÓN (Real-ESRGAN)
                if usar_hd:
                    status.write("1️⃣ Aumentando resolución y detalles (Real-ESRGAN)...")
                    output_upscale = replicate.run(
                        "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
                        input={
                            "image": img_input,
                            "scale": 2,
                            "face_enhance": True
                        }
                    )
                    
                    # --- PUENTE DE SEGURIDAD (SOLUCIÓN DEL ERROR) ---
                    # Convertimos la salida extraña de la IA en un archivo limpio
                    buffer_hd = BytesIO()
                    
                    # Caso A: Es una URL (String)
                    if isinstance(output_upscale, str):
                        resp = requests.get(output_ups
