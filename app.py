import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CLAROS INSTITUCIONALES
# ==========================================
st.set_page_config(
    page_title="Sistema de Control de Montacargas - IMSS",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos limpios sobre fondo claro con acentos institucionales sutiles
st.markdown("""
    <style>
    .stApp {
        background-color: #F8F9FA;
        color: #1F2937;
    }
    
    /* Barra lateral institucional en Verde IMSS (#005A36) */
    [data-testid="stSidebar"] {
        background-color: #005A36;
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #FFFFFF !important;
        font-weight: 500;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #FFFFFF;
    }

    /* Encabezados principales */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #005A36;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 25px;
    }

    /* Tarjetas de métricas estilizadas claras */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    [data-testid="stMetric"] label {
        color: #4B5563 !important;
        font-weight: 600;
    }
    [data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #005A36 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN Y CARGA DE DATOS SUPABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def load_padron():
    try:
        response = supabase.table("padron_montacargas").select("*").order("id_equipo").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df = df.fillna("")
            if "estatus_operativo" not in df.columns:
                df["estatus_operativo"] = "Operativo"
        return df
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return pd.DataFrame()

def load_mantenimientos():
    try:
        response = supabase.table("mantenimientos_montacargas").select("*").order("fecha_servicio", desc=True).execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df = df.fillna("")
        return df
    except:
        return pd.DataFrame()

# Encabezado institucional claro
st.markdown('<div class="main-title">🚜 Sistema de Control de Montacargas</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">División de Transportes y Operación | Coordinación Técnica de Servicios Generales</div>', unsafe_allow_html=True)

df_padron = load_padron()
df_maint = load_mantenimientos()

if df_padron.empty:
    st.warning("La base de datos se encuentra vacía o hay un problema de conexión con Supabase.")
    st.stop()

# ==========================================
# 3. NAVEGACIÓN MODULAR (5 MÓDULOS)
# ==========================================
st.sidebar.markdown("### 📌 Módulos del Sistema")
menu = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "📊 Dashboard & Semáforo de Flota",
        "🔍 Buscador Universal & Tabla Maestro",
        "🎇 Ficha Digital por Equipo",
        "🛠️ Gestión de Mantenimiento (CMMS)",
        "📝 Editar / Registrar Unidad"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("🌐 **Infraestructura:** Supabase Cloud")
st.sidebar.caption(f"📦 **Flota Total:** {len(df_padron)} Unidades")
# ==========================================
# MÓDULO 1: DASHBOARD & SEMÁFORO DE FLOTA
# ==========================================
if menu == "📊 Dashboard & Semáforo de Flota":
    st.subheader("🚥 Semáforo Operativo y Disponibilidad de Flota")
    
    total_u = len(df_padron)
    
    # Conteo por estatus operativo alineado al nuevo enfoque
    op_count = len(df_padron[df_padron["estatus_operativo"].str.contains("Operativo", case=False, na=False)])
    garantia_count = len(df_padron[df_padron["estatus_operativo"].str.contains("Garantía|Garantia", case=False, na=False)])
    inconcluso_count = len(df_padron[df_padron["estatus_operativo"].str.contains("Inconcluso|Pendiente|Taller|Fuera", case=False, na=False)])
    
    # Ajuste por defecto si no existen diferencias de estatus aún
    if op_count == 0 and garantia_count == 0 and inconcluso_count == 0:
        op_count = total_u
        
    disp_porcentaje = (op_count / total_u) * 100 if total_u > 0 else 0
    
    # Desglose por Etapas Contractuales
    etapa1 = len(df_padron[df_padron["etapa_contractual"].str.contains("Etapa 1|1", case=False, na=False)])
    etapa2 = len(df_padron[df_padron["etapa_contractual"].str.contains("Etapa 2|2", case=False, na=False)])
    etapa3 = len(df_padron[df_padron["etapa_contractual"].str.contains("Etapa 3|3", case=False, na=False)])
    etapa4 = len(df_padron[df_padron["etapa_contractual"].str.contains("Etapa 4|4", case=False, na=False)])

    # Indicadores Métricos Superiores
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.metric("Total Flota", f"{total_u} U")
        st.caption(f"E1: {etapa1} | E2: {etapa2} | E3: {etapa3} | E4: {etapa4}")
        
    c2.metric("Disponibilidad", f"{disp_porcentaje:.1f}%")
    c3.metric("🟢 Operativos", f"{op_count} U")
    c4.metric("🟡 Servicio Garantía Inconcluso", f"{garantia_count} U")
    c5.metric("🔴 Servicios Inconclusos", f"{inconcluso_count} U")

    st.markdown("---")
    
    # DISTRIBUCIÓN COMPLETA POR OOAD EN FONDO CLARO
    st.subheader("📍 Distribución Completa por OOAD / Estado (100% de Registros)")
    
    if "ooad_estado" in df_padron.columns:
        counts_ooad_full = df_padron["ooad_estado"].value_counts()
        st.bar_chart(counts_ooad_full)
        
        with st.expander("📋 Ver Desglose Numérico de Unidades por Estado / OOAD"):
            df_summary = pd.DataFrame({
                "OOAD / Estado": counts_ooad_full.index,
                "Total Montacargas": counts_ooad_full.values
            })
            st.dataframe(df_summary, use_container_width=True, hide_index=True)

    st.markdown("---")
    
    # SEGUIMIENTO DE SERVICIOS INCONCLUSOS Y GARANTÍAS
    st.subheader("🔎 Control de Unidades con Servicios o Garantías Inconclusas")
    
    df_atencion = df_padron[df_padron["estatus_operativo"].str.contains("Garantía|Garantia|Inconcluso|Pendiente|Taller|Fuera", case=False, na=False)]
    
    if not df_atencion.empty:
        st.warning(f"Se identificaron {len(df_atencion)} unidades con trámites o servicios inconclusos.")
        st.dataframe(df_atencion, use_container_width=True, hide_index=True)
    else:
        st.success("🟢 No hay registros con servicios o garantías pendientes. Flota al 100% de cumplimiento.")