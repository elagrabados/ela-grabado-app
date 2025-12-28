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
st.info("✨ Sistema Inteligente: Restauración de Rostros + Fondo Transparente")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎛️ Panel de Control")
    st.subheader("Ajustes Finales")
    nitidez = st.slider("Nitidez (Sharpness)", 0.0, 3.0, 1.5)
    contraste = st.slider("Contraste", 0.0, 3.0, 1.2)
    st.divider()
    st.markdown("Desarrollado para **Ela Live Laser Bar**")

# --- INTERFAZ PRINCIPAL ---
uploaded_file = st.file_uploader("📂 Sube la foto (Idealmente rostros o mascotas)", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    # Mostrar original
    image = Image.open(uploaded_file)
    st.image(image, caption="Foto Original", use_column_width=True)

    if st.button("💎 PROCESAR FOTO AHORA"):
        
        if not st.secrets.get("REPLICATE_API_TOKEN"):
            st.error("⚠️ Faltan las llaves de la API. Configúralas en Streamlit Secrets.")
            st.stop()

        with st.status("🤖 La IA está trabajando...", expanded=True) as status:
            
            try:
                # PASO 1: RESTAURACIÓN (CodeFormer)
                status.write("1️⃣ Restaurando rostro en HD...")
                model_codeformer = replicate.models.get("sczhou/codeformer")
                version_codeformer = model_codeformer.versions.list()[0]
                
                output_restoration = replicate.run(
                    f"sczhou/codeformer:{version_codeformer.id}",
                    input={"image": uploaded_file, "upscale": 2, "face_upsample": True}
                )
                
                # --- PUENTE SEGURO ---
                buffer_restaurado = BytesIO()
                if hasattr(output_restoration, 'read'):
                    buffer_restaurado.write(output_restoration.read())
                elif hasattr(output_restoration, '__iter__'):
                    for chunk in output_restoration:
                        buffer_restaurado.write(chunk)
                else:
                    response = requests.get(str(output_restoration))
                    buffer_restaurado.write(response.content)
                buffer_restaurado.seek(0)
                # ---------------------

                # PASO 2: QUITAR FONDO (NUEVO MODELO MEJORADO)
                status.write("2️⃣ Eliminando fondo con precisión quirúrgica...")
                # CAMBIO CLAVE: Usamos un modelo diferente y más preciso
                model_rembg_pro = replicate.models.get("lucataco/remove-bg")
                version_rembg_pro = model_rembg_pro.versions.list()[0]
                
                output_rembg = replicate.run(
                    f"lucataco/remove-bg:{version_rembg_pro.id}",
                    input={"image": buffer_restaurado}
                )

                # Leemos el resultado final
                buffer_final = BytesIO()
                if hasattr(output_rembg, 'read'):
                    buffer_final.write(output_rembg.read())
                elif hasattr(output_rembg, '__iter__'):
                    for chunk in output_rembg:
                        buffer_final.write(chunk)
                else:
                    response = requests.get(str(output_rembg))
                    buffer_final.write(response.content)
                
                img_ia = Image.open(buffer_final)
                
                # PASO 3: AJUSTES PARA LÁSER
                status.write("3️⃣ Aplicando ajustes para acero inoxidable...")
                enhancer = ImageEnhance.Sharpness(img_ia)
                img_sharp = enhancer.enhance(nitidez)
                
                enhancer_c = ImageEnhance.Contrast(img_sharp)
                img_final = enhancer_c.enhance(contraste)

                status.update(label="✅ ¡Imagen Lista!", state="complete", expanded=False)
                
                # MOSTRAR RESULTADO
                st.divider()
                st.subheader("Resultado Final (Listo para LightBurn)")
                st.image(img_final, use_column_width=True, caption="Fondo Transparente")
                
                # BOTÓN DE DESCARGA
                buf = BytesIO()
                img_final.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="⬇️ DESCARGAR PNG (Transparente)",
                    data=byte_im,
                    file_name="ela_laser_ready.png",
                    mime="image/png"
                )

            except Exception as e:
                st.error(f"Ocurrió un error técnico: {e}")
                st.write(f"Detalle: {str(e)}")
