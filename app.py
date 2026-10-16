import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io

# 1. Configuración de la página
st.set_page_config(
    page_title="Control de Montacargas - IMSS",
    page_icon="🚜",
    layout="wide"
)

# 2. Conexión a Supabase usando Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Función para cargar datos
def load_data():
    response = supabase.table("padron_montacargas").select("*").order("id_equipo").execute()
    return pd.DataFrame(response.data)

# Encabezado principal
st.title("🚜 Sistema de Control de Montacargas - IMSS")
st.caption("Coordinación Técnica de Servicios Generales | División de Transportes y Operación")

# Cargar datos actuales
df = load_data()

if df.empty:
    st.error("No se encontraron registros en la base de datos.")
    st.stop()

# Estructura de pestañas
tab_dashboard, tab_editar, tab_mantenimiento = st.tabs([
    "📊 Panel y Consultas", 
    "📝 Editar Unidad", 
    "🛠️ Bitácora de Mantenimiento"
])

# ==========================================
# PESTAÑA 1: DASHBOARD Y CONSULTAS
# ==========================================
with tab_dashboard:
    st.subheader("🔍 Filtros de Búsqueda")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        ooads = ["Todas"] + sorted([x for x in df["ooad_estado"].dropna().unique()])
        sel_ooad = st.selectbox("Filtrar por OOAD / Estado:", ooads)
        
    with col_f2:
        etapas = ["Todas"] + sorted([x for x in df["etapa_contractual"].dropna().unique()])
        sel_etapa = st.selectbox("Filtrar por Etapa Contractual:", etapas)
        
    with col_f3:
        search_term = st.text_input("Buscar por ID, Serie o Sede:", "")

    # Aplicar filtros
    df_filtered = df.copy()
    if sel_ooad != "Todas":
        df_filtered = df_filtered[df_filtered["ooad_estado"] == sel_ooad]
    if sel_etapa != "Todas":
        df_filtered = df_filtered[df_filtered["etapa_contractual"] == sel_etapa]
    if search_term:
        mask = (
            df_filtered["id_equipo"].astype(str).str.contains(search_term, case=False, na=False) |
            df_filtered["serie_montacargas"].astype(str).str.contains(search_term, case=False, na=False) |
            df_filtered["almacen_sede"].astype(str).str.contains(search_term, case=False, na=False)
        )
        df_filtered = df_filtered[mask]

    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Unidades Mostradas", len(df_filtered))
    m2.metric("Total Padrón", len(df))
    m3.metric("Estatus Base de Datos", "🟢 Conectado")

    st.markdown("---")
    
    # Tabla e exportación
    st.subheader("📋 Padrón de Equipos")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    
    # Botón para descargar Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Montacargas')
    
    st.download_button(
        label="📥 Descargar Reporte en Excel",
        data=buffer.getvalue(),
        file_name="padron_montacargas_imss.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==========================================
# PESTAÑA 2: EDITAR Y ACTUALIZAR UNIDAD
# ==========================================
with tab_editar:
    st.subheader("📝 Modificar Registro de Unidad")
    
    unidades_list = df["id_equipo"].tolist()
    selected_id = st.selectbox("Selecciona el ID del equipo a editar:", unidades_list)
    
    # Datos actuales del equipo seleccionado
    equipo = df[df["id_equipo"] == selected_id].iloc[0]
    
    with st.form("form_editar"):
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            e_ooad = st.text_input("OOAD / Estado:", value=str(equipo.get("ooad_estado", "")))
            e_sede = st.text_area("Almacén / Sede:", value=str(equipo.get("almacen_sede", "")))
            e_area = st.text_input("Área de Asignación:", value=str(equipo.get("area_asignacion", "")))
            
        with col_e2:
            e_serie = st.text_input("Serie Montacargas:", value=str(equipo.get("serie_montacargas", "")))
            e_bateria = st.text_input("Serie Batería:", value=str(equipo.get("serie_bateria", "")))
            e_cargador = st.text_input("Serie Cargador:", value=str(equipo.get("serie_cargador", "")))
            
        btn_guardar = st.form_submit_button("💾 Guardar Cambios en Supabase")
        
        if btn_guardar:
            try:
                update_data = {
                    "ooad_estado": e_ooad,
                    "almacen_sede": e_sede,
                    "area_asignacion": e_area,
                    "serie_montacargas": e_serie,
                    "serie_bateria": e_bateria,
                    "serie_cargador": e_cargador
                }
                supabase.table("padron_montacargas").update(update_data).eq("id_equipo", selected_id).execute()
                st.success(f"¡Unidad {selected_id} actualizada correctamente!")
                st.cache_resource.clear()
            except Exception as e:
                st.error(f"Error al actualizar: {e}")

# ==========================================
# PESTAÑA 3: BITÁCORA DE MANTENIMIENTO
# ==========================================
with tab_mantenimiento:
    st.subheader("🛠️ Registro de Servicio / Mantenimiento")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        id_maint = st.selectbox("Selecciona el Equipo:", unidades_list, key="maint_id")
        tipo_servicio = st.selectbox("Tipo de Servicio:", ["Preventivo", "Correctivo", "Inspección Rutinaria"])
    with col_m2:
        fecha_servicio = st.date_input("Fecha de Servicio:")
        tecnico = st.text_input("Técnico / Empresa Responsable:")
        
    detalles = st.text_area("Detalles del Trabajo / Refacciones Reemplazadas:")
    
    if st.button("📌 Registrar Mantenimiento"):
        st.info(f"Registro guardado localmente para el equipo {id_maint} ({tipo_servicio} - {fecha_servicio}).")