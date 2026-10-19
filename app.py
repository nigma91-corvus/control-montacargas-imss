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
    page_icon="🏛️",
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
st.markdown('<div class="main-title">🏛️ Sistema de Control de Montacargas</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">División de Transportes y Operación | Coordinación Técnica de Servicios Generales</div>', unsafe_allow_html=True)

df_padron = load_padron()
df_maint = load_mantenimientos()

if df_padron.empty:
    st.warning("La base de datos se encuentra vacía o hay un problema de conexión con Supabase.")
    st.stop()

# ==========================================
# 3. NAVEGACIÓN MODULAR (5 MÓDULOS)
# ==========================================
st.sidebar.markdown("### 🏛️ IMSS - Control de Flota")
st.sidebar.markdown("---")
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

import altair as alt

# ==========================================
# MÓDULO 1: DASHBOARD & SEMÁFORO DE FLOTA
# ==========================================
if menu == "📊 Dashboard & Semáforo de Flota":
    st.subheader("🚥 Semáforo Operativo y Disponibilidad de Flota")
    
    st.markdown("""
        <style>
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #1F2937 !important;
            border-color: #D1D5DB !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col_f1, col_f2 = st.columns([2, 4])
    with col_f1:
        filtro_etapa_dash = st.selectbox(
            "🎯 Filtrar Dashboard por Etapa:",
            ["Todas las Etapas", "Etapa 1 (2022)", "Etapa 2 (2024)", "Etapa 3 (2024)", "Etapa 4"]
        )
    
    # FILTRADO EXACTO BASADO EN LOS NOMBRES REALES DE SUPABASE
    df_dash = df_padron.copy()
    if filtro_etapa_dash != "Todas las Etapas":
        if filtro_etapa_dash == "Etapa 4":
            # Como la etapa 4 no existe, filtramos por un valor imposible para que arroje 0 unidades limpiamente
            df_dash = df_dash[df_dash["etapa_contractual"].astype(str).str.contains("NO_EXISTE", case=False, na=False)]
        else:
            df_dash = df_dash[df_dash["etapa_contractual"].astype(str).str.strip().str.lower() == filtro_etapa_dash.lower()]

    total_u = len(df_dash)
    
    op_count = len(df_dash[df_dash["estatus_operativo"].astype(str).str.contains("Operativo", case=False, na=False)])
    garantia_count = len(df_dash[df_dash["estatus_operativo"].astype(str).str.contains("Garantía|Garantia", case=False, na=False)])
    inconcluso_count = len(df_dash[df_dash["estatus_operativo"].astype(str).str.contains("Inconcluso|Pendiente|Taller|Fuera", case=False, na=False)])
    
    if op_count == 0 and garantia_count == 0 and inconcluso_count == 0:
        op_count = total_u
        
    disp_porcentaje = (op_count / total_u) * 100 if total_u > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.metric("Flota en Vista", f"{total_u} U")
        st.caption(f"Filtro: {filtro_etapa_dash}")
        
    c2.metric("Disponibilidad", f"{disp_porcentaje:.1f}%")
    c3.metric("🟢 Operativos", f"{op_count} U")
    c4.metric("🟡 Servicio Garantía Inconcluso", f"{garantia_count} U")
    c5.metric("🔴 Servicios Inconclusos", f"{inconcluso_count} U")

    st.markdown("---")
    
    # GRÁFICA AJUSTADA AL FILTRO SELECCIONADO
    st.subheader(f"📍 Distribución por OOAD / Estado ({filtro_etapa_dash})")
    
    if "ooad_estado" in df_dash.columns and not df_dash.empty:
        counts_ooad_full = df_dash["ooad_estado"].value_counts().reset_index()
        counts_ooad_full.columns = ["OOAD_Estado", "Total"]
        
        chart = alt.Chart(counts_ooad_full).mark_bar(color='#005A36').encode(
            y=alt.Y('OOAD_Estado:N', title='OOAD / Estado', sort='-x', 
                    axis=alt.Axis(labelColor='#1F2937', labelLimit=300)),
            x=alt.X('Total:Q', title='Número de Unidades', axis=alt.Axis(labelColor='#1F2937', grid=True, gridColor='#E5E7EB')),
            tooltip=['OOAD_Estado', 'Total']
        ).properties(
            height=max(400, len(counts_ooad_full) * 22)
        ).configure_view(
            strokeWidth=0,
            fill='white'
        ).configure(
            background='white'
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        with st.expander("📋 Ver Desglose Numérico de Unidades por Estado / OOAD"):
            st.dataframe(counts_ooad_full, use_container_width=True, hide_index=True)
    else:
        st.info(f"⚠️ No hay unidades registradas para la selección: {filtro_etapa_dash}")

    st.markdown("---")
    
    st.subheader("🔎 Control de Unidades con Servicios o Garantías Inconclusas")
    
    df_atencion = df_dash[df_dash["estatus_operativo"].astype(str).str.contains("Garantía|Garantia|Inconcluso|Pendiente|Taller|Fuera", case=False, na=False)]
    
    if not df_atencion.empty:
        st.warning(f"Se identificaron {len(df_atencion)} unidades con trámites o servicios inconclusos en esta selección.")
        st.dataframe(df_atencion, use_container_width=True, hide_index=True)
    else:
        st.success("🟢 No hay registros con servicios o garantías pendientes en esta vista.")
# ==========================================
# MÓDULO 2: BUSCADOR UNIVERSAL & TABLA MAESTRO
# ==========================================
elif menu == "🔍 Buscador Universal & Tabla Maestro":
    st.subheader("🔍 Buscador Universal de Unidades")
    st.caption("Localice equipos rápidamente por NNI, Número de Inventario, Serie o Etapa Contractual.")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        search_nni = st.text_input("Buscar por NNI", placeholder="Ej. NNI-...")
    with col_s2:
        search_inv = st.text_input("Buscar por No. Inventario", placeholder="Ej. INV-...")
    with col_s3:
        search_stage = st.selectbox("Filtrar por Etapa Contractual", ["Todas", "Etapa 1", "Etapa 2", "Etapa 3", "Etapa 4"])
        
    df_filtered = df_padron.copy()
    
    if search_nni:
        df_filtered = df_filtered[df_filtered["nni"].astype(str).str.contains(search_nni, case=False, na=False)]
    if search_inv:
        df_filtered = df_filtered[df_filtered["numero_inventario"].astype(str).str.contains(search_inv, case=False, na=False)]
    if search_stage != "Todas":
        df_filtered = df_filtered[df_filtered["etapa_contractual"].astype(str).str.contains(search_stage, case=False, na=False)]
        
    st.markdown("---")
    st.subheader(f"📋 Padrón y Resultados ({len(df_filtered)} unidades encontradas)")
    
    if not df_filtered.empty:
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No se encontraron unidades con los criterios de búsqueda especificados. Verifique los datos o intente con otro parámetro.")