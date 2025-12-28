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
st.info("✨ Motor Activado: BRIA AI (Calidad Comercial)")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎛️ Panel de Control")
    st.subheader("Asistente de Luz")
    # Dejamos esto por si acaso, pero Bria suele necesitar menos ayuda
    ayuda_sombras = st.slider("Revelar Sombras (Solo si es necesario)", 1.0, 3.0, 1.0)
    
    st.subheader("Acabado Láser")
    nitidez = st.slider("Nitidez", 0.0, 5.0, 2.0)
    contraste = st.slider("Contraste", 0.5, 3.0, 1.2)
    
    st.divider()
    st.markdown("Desarrollado para **Ela Live Laser Bar**")

# --- INTERFAZ PRINCIPAL ---
uploaded_file = st.file_uploader("📂 Sube la foto Original", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Foto Original", use_column_width=True)

    if st.button("💎 CORTAR CON BRIA AI"):
        
        if not st.secrets.get("REPLICATE_API_TOKEN"):
            st.error("⚠️ Faltan las llaves de la API.")
            st.stop()

        with st.status("🤖 BRIA está analizando la imagen...", expanded=True) as status:
            
            try:
                # PASO 1: PRE-PROCESO (OPCIONAL)
                # Si el usuario subió el slider, aclaramos la foto antes de enviarla
                if ayuda_sombras > 1.0:
                    status.write("💡 Aplicando 'Flash Digital' para separar el fondo...")
                    img_temp = image.convert("RGB")
                    enhancer_pre = ImageEnhance.Brightness(img_temp)
                    img_input = enhancer_pre.enhance(ayuda_sombras)
                    
                    # Guardamos en buffer para enviar
                    buffer_envio = BytesIO()
                    img_input.save(buffer_envio, format="PNG")
                    buffer_envio.seek(0)
                    input_final = buffer_envio
                else:
                    input_final = uploaded_file

                # PASO 2: BRIA AI (EL NUEVO MOTOR)
                status.write("✂️ Recortando con Bria Remove Background...")
                
                # Usamos el modelo oficial de Bria en Replicate
                output_bria = replicate.run(
                    "bria/remove-background",
                    input={
                        "image": input_final,
                        "preserve_alpha": True
                    }
                )

                # LEER RESULTADO
                buffer_bg = BytesIO()
                # Bria suele devolver una URL directa a la imagen PNG
                if isinstance(output_bria, str):
                    response = requests.get(output_bria)
                    buffer_bg.write(response.content)
                elif hasattr(output_bria, 'read'):
                    buffer_bg.write(output_bria.read())
                
                img_sin_fondo = Image.open(buffer_bg)
                
                # PASO 3: AJUSTES FINALES
                status.write("3️⃣ Ajustando para acero inoxidable...")
                
                img_proc = img_sin_fondo.convert("RGBA")
                
                enhancer_c = ImageEnhance.Contrast(img_proc)
                img_proc = enhancer_c.enhance(contraste)

                enhancer_s = ImageEnhance.Sharpness(img_proc)
                img_proc = enhancer_s.enhance(nitidez)

                status.update(label="✅ ¡Perfecto!", state="complete", expanded=False)
                
                # MOSTRAR RESULTADO
                st.divider()
                st.subheader("Resultado Final")
                st.markdown("""<style>[data-testid="stImage"] {background-color: #e0e0e0;}</style>""", unsafe_allow_html=True)
                st.image(img_proc, use_column_width=True, caption="Listo para LightBurn")
                
                # DESCARGA
                buf = BytesIO()
                img_proc.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button("⬇️ DESCARGAR PNG", data=byte_im, file_name="ela_bria_final.png", mime="image/png")

            except Exception as e:
                st.error(f"Ocurrió un error técnico: {e}")
