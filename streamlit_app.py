import streamlit as st
import replicate
import requests
from PIL import Image, ImageEnhance
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Ela Grabado", page_icon="💎", layout="centered")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .main-title { color: #1E3A8A; text-align: center; font-family: sans-serif; }
    .stButton>button { width: 100%; background-color: #1E3A8A; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">Ela Grabado de Joyería</h1>', unsafe_allow_html=True)
st.info("✨ Modo: CORTE EXPERTO (IS-Net) + Ajuste Manual")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎛️ Panel de Control")
    st.subheader("Ajustes de Grabado")
    nitidez = st.slider("Nitidez (Sharpness)", 0.0, 5.0, 2.0)
    contraste = st.slider("Contraste", 0.5, 3.0, 1.3)
    brillo = st.slider("Brillo", 0.5, 2.0, 1.0)
    
    st.divider()
    st.markdown("Desarrollado para **Ela Live Laser Bar**")

# --- INTERFAZ PRINCIPAL ---
uploaded_file = st.file_uploader("📂 Sube la foto Original", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Foto Original", use_column_width=True)

    if st.button("💎 CORTAR Y PREPARAR"):
        
        if not st.secrets.get("REPLICATE_API_TOKEN"):
            st.error("⚠️ Faltan las llaves de la API.")
            st.stop()

        with st.status("🤖 Trabajando en el corte...", expanded=True) as status:
            
            try:
                # PASO 1: QUITAR FONDO (Modo Experto)
                status.write("1️⃣ Buscando especialista en bordes difíciles...")
                
                # Buscamos la versión automáticamente para que no de error 422
                model_rembg = replicate.models.get("cjwbw/rembg")
                version_rembg = model_rembg.versions.list()[0]
                
                status.write("✂️ Aplicando corte con algoritmo IS-Net...")
                output_rembg = replicate.run(
                    f"cjwbw/rembg:{version_rembg.id}",
                    input={
                        "image": uploaded_file,
                        "model": "isnet-general-use" # <--- EL SECRETO: Algoritmo de alta precisión
                    }
                )

                # LEER RESULTADO
                buffer_bg = BytesIO()
                if hasattr(output_rembg, 'read'):
                    buffer_bg.write(output_rembg.read())
                elif hasattr(output_rembg, '__iter__'):
                    for chunk in output_rembg:
                        buffer_bg.write(chunk)
                else:
                    response = requests.get(str(output_rembg))
                    buffer_bg.write(response.content)
                
                img_sin_fondo = Image.open(buffer_bg)
                
                # PASO 2: MEJORA MANUAL
                status.write("2️⃣ Optimizando para láser...")
                
                img_proc = img_sin_fondo.convert("RGBA")
                
                # Ajustes en orden: Brillo -> Contraste -> Nitidez
                enhancer_b = ImageEnhance.Brightness(img_proc)
                img_proc = enhancer_b.enhance(brillo)

                enhancer_c = ImageEnhance.Contrast(img_proc)
                img_proc = enhancer_c.enhance(contraste)

                enhancer_s = ImageEnhance.Sharpness(img_proc)
                img_proc = enhancer_s.enhance(nitidez)

                status.update(label="✅ ¡Listo!", state="complete", expanded=False)
                
                # MOSTRAR RESULTADO
                st.divider()
                st.subheader("Resultado Final")
                # Fondo gris para contrastar
                st.markdown("""<style>[data-testid="stImage"] {background-color: #e0e0e0;}</style>""", unsafe_allow_html=True)
                st.image(img_proc, use_column_width=True, caption="Listo para LightBurn")
                
                # DESCARGA
                buf = BytesIO()
                img_proc.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button("⬇️ DESCARGAR PNG", data=byte_im, file_name="ela_laser_v2.png", mime="image/png")

            except Exception as e:
                st.error(f"Ocurrió un error técnico: {e}")
