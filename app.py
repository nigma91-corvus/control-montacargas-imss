import streamlit as st
from supabase import create_client

# Configuración de la página web
st.set_page_config(
    page_title="Control de Montacargas IMSS",
    page_icon="🚜",
    layout="wide"
)

# Inicializar conexión a Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
    
    st.title("🚜 Sistema de Control de Montacargas - IMSS")
    st.caption("Coordinación Técnica de Servicios Generales | División de Transportes y Operación")
    st.divider()

    # Consulta de prueba a la base de datos
    response = supabase.table("padron_montacargas").select("*", count="exact").execute()
    total_unidades = response.count
    
    # Métricas principales
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Unidades en Padrón", f"{total_unidades} equipos")
    col2.metric("Estatus del Sistema", "🟢 Conectado a Supabase")
    col3.metric("Acceso Web", "En línea")
    
    st.subheader("📋 Padrón Maestro de Equipos")
    if response.data:
        import pandas as pd
        df = pd.DataFrame(response.data)
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error de conexión con la base de datos: {e}")