import streamlit as st
import replicate
import requests
from PIL import Image, ImageEnhance, ImageFilter
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
st.info("✨ Modo: CORTE DE PRECISIÓN (BiRefNet) + Ajuste Láser")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🎛️ Panel de Control")
    st.subheader("Ajustes de Grabado")
    # Aumentamos los rangos para darte más poder manual
    nitidez = st.slider("Nitidez (Sharpness)", 0.0, 5.0, 2.0, help="Sube esto para definir bordes en el acero")
    contraste = st.slider("Contraste", 0.5, 3.0, 1.3, help="Vital para separar grises en el láser")
    brillo = st.slider("Brillo", 0.5, 2.0, 1.0, help="Ajustar si la foto original es muy oscura")
    
    st.divider()
    st.markdown("Desarrollado para **Ela Live Laser Bar**")

# --- INTERFAZ PRINCIPAL ---
uploaded_file = st.file_uploader("📂 Sube la foto Original", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    # Mostrar original
    image = Image.open(uploaded_file)
    st.image(image, caption="Foto Original", use_column_width=True)

    if st.button("💎 CORTAR Y PREPARAR"):
        
        if not st.secrets.get("REPLICATE_API_TOKEN"):
            st.error("⚠️ Faltan las llaves de la API.")
            st.stop()

        with st.status("🤖 Trabajando en el corte...", expanded=True) as status:
            
            try:
                # PASO 1: QUITAR FONDO (BiRefNet - El modelo más potente actualmente)
                status.write("1️⃣ Aplicando corte de alta precisión (BiRefNet)...")
                
                # Usamos BiRefNet que es especialista en "Hard Cases" (casos difíciles)
                output_rembg = replicate.run(
                    "zhengxiaozou/birefnet:563a66acc0b39e5306e8343ee00905a92def95f191e2189a7509d6f6e2a22a36",
                    input={"image": uploaded_file}
                )

                # --- LEER RESULTADO ---
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
                
                # PASO 2: MEJORA MANUAL (Sin IA que borre detalles)
                status.write("2️⃣ Optimizando para láser (Nitidez y Contraste)...")
                
                # Convertimos a RGBA para asegurar manejo de transparencia
                img_proc = img_sin_fondo.convert("RGBA")

                # Ajuste de Brillo (Primero)
                enhancer_b = ImageEnhance.Brightness(img_proc)
                img_proc = enhancer_b.enhance(brillo)

                # Ajuste de Contraste
                enhancer_c = ImageEnhance.Contrast(img_proc)
                img_proc = enhancer_c.enhance(contraste)

                # Ajuste de Nitidez (Vital para grabado)
                enhancer_s = ImageEnhance.Sharpness(img_proc)
                img_proc = enhancer_s.enhance(nitidez)

                status.update(label="✅ ¡Corte Terminado!", state="complete", expanded=False)
                
                # MOSTRAR RESULTADO
                st.divider()
                st.subheader("Resultado Final")
                # Fondo gris claro para ver bien el borde negro
                st.markdown(
                    """
                    <style>
                    [data-testid="stImage"] {
                        background-color: #e0e0e0;
                        border-radius: 10px;
                        padding: 10px;
                    }
                    </style>
                    """, 
                    unsafe_allow_html=True
                )
                st.image(img_proc, use_column_width=True, caption="Listo para LightBurn")
                
                # BOTÓN DE DESCARGA
                buf = BytesIO()
                img_proc.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.download_button(
                    label="⬇️ DESCARGAR PNG",
                    data=byte_im,
                    file_name="ela_laser_birefnet.png",
                    mime="image/png"
                )

            except Exception as e:
                st.error(f"Ocurrió un error técnico: {e}")
                st.write(f"Detalle: {str(e)}")
