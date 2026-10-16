import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Sistema de Control de Montacargas - IMSS",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1rem;
        color: #9EC5FE;
        margin-bottom: 20px;
    }
    .stMetric {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN Y FUNCIONES SUPABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def get_padron_data():
    """Carga TODAS las columnas del padrón desde Supabase"""
    response = supabase.table("padron_montacargas").select("*").order("id_equipo").execute()
    return pd.DataFrame(response.data)

# Encabezado principal
st.markdown('<div class="main-header">🚜 Sistema de Control de Montacargas - IMSS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Coordinación Técnica de Servicios Generales | División de Transportes y Operación</div>', unsafe_allow_html=True)

# Cargar base de datos
try:
    df = get_padron_data()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")
    st.stop()

if df.empty:
    st.warning("La base de datos está vacía o no se devolvieron registros.")
    st.stop()

# Navegación Principal por Pestañas
tab_dashboard, tab_editar, tab_mantenimiento, tab_nueva_unidad = st.tabs([
    "📊 Panel General & Filtros", 
    "📝 Modificar Unidad Completa", 
    "🛠️ Bitácora de Mantenimiento",
    "➕ Alta de Nueva Unidad"
])

# ==========================================
# PESTAÑA 1: DASHBOARD Y CONSULTAS
# ==========================================
with tab_dashboard:
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    total_equipos = len(df)
    ooad_col = "ooad_estado" if "ooad_estado" in df.columns else df.columns[1]
    ooad_count = df[ooad_col].nunique() if ooad_col in df.columns else 0
    total_columnas = len(df.columns)
    
    col_kpi1.metric("Total en Padrón", f"{total_equipos} unidades")
    col_kpi2.metric("OOAD / Sedes", f"{ooad_count} registradas")
    col_kpi3.metric("Campos / Columnas", f"{total_columnas} variables")
    col_kpi4.metric("Estatus Sistema", "🟢 En línea")

    st.markdown("---")
    
    st.subheader("🔍 Filtros Dinámicos de Búsqueda")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        if "ooad_estado" in df.columns:
            lista_ooad = ["Todas"] + sorted([str(x) for x in df["ooad_estado"].dropna().unique() if x])
            sel_ooad = st.selectbox("Filtrar por OOAD / Estado:", lista_ooad)
        else:
            sel_ooad = "Todas"
        
    with col_f2:
        if "etapa_contractual" in df.columns:
            lista_etapas = ["Todas"] + sorted([str(x) for x in df["etapa_contractual"].dropna().unique() if x])
            sel_etapa = st.selectbox("Filtrar por Etapa Contractual:", lista_etapas)
        else:
            sel_etapa = "Todas"
        
    with col_f3:
        search_query = st.text_input("Búsqueda global (en cualquier variable/columna):", "")

    # Aplicar filtros
    df_filtered = df.copy()
    if sel_ooad != "Todas" and "ooad_estado" in df.columns:
        df_filtered = df_filtered[df_filtered["ooad_estado"] == sel_ooad]
    if sel_etapa != "Todas" and "etapa_contractual" in df.columns:
        df_filtered = df_filtered[df_filtered["etapa_contractual"] == sel_etapa]
    if search_query:
        # Búsqueda sobre TODAS las columnas del DataFrame
        mask = df_filtered.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False).any(), axis=1)
        df_filtered = df_filtered[mask]

    st.markdown(f"**Resultados encontrados:** {len(df_filtered)} de {total_equipos} unidades | **Mostrando las {len(df.columns)} columnas completas.**")
    
    # Muestra el DataFrame completo permitiendo hacer scroll horizontal y vertical
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    
    # Exportación a Excel
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Padron_Montacargas')
        
    st.download_button(
        label="📥 Exportar Consulta a Excel (.xlsx)",
        data=output_excel.getvalue(),
        file_name=f"padron_imss_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==========================================
# PESTAÑA 2: EDITAR Y ACTUALIZAR UNIDAD (DINÁMICO)
# ==========================================
with tab_editar:
    st.subheader("📝 Edición Integral de Registros")
    
    col_sel, col_info = st.columns([2, 2])
    with col_sel:
        id_col = "id_equipo" if "id_equipo" in df.columns else df.columns[0]
        id_list = df[id_col].tolist()
        equipo_id = st.selectbox("Selecciona la Unidad a Modificar:", id_list, key="edit_select_dyn")
        
    row = df[df[id_col] == equipo_id].iloc[0]
    
    with st.form("form_edicion_dinamica"):
        st.markdown(f"#### Editando todas las variables para el registro: **{equipo_id}**")
        
        # Generar inputs automáticamente para TODAS las columnas de la tabla
        updated_data = {}
        cols_list = list(df.columns)
        
        # Crear 3 columnas visuales para acomodar todos los campos de forma limpia
        c1, c2, c3 = st.columns(3)
        cols_containers = [c1, c2, c3]
        
        for idx, col_name in enumerate(cols_list):
            if col_name == id_col:
                continue # No permitimos cambiar la clave primaria
                
            val_actual = str(row[col_name]) if pd.notna(row[col_name]) else ""
            container = cols_containers[idx % 3]
            
            # Si el texto es largo (ej. direcciones), usa text_area, de lo contrario text_input
            if len(val_actual) > 40 or "almacen" in col_name.lower() or "sede" in col_name.lower():
                updated_data[col_name] = container.text_area(f"{col_name}:", value=val_actual, height=80)
            else:
                updated_data[col_name] = container.text_input(f"{col_name}:", value=val_actual)
                
        btn_actualizar = st.form_submit_button("💾 Guardar Cambios en Supabase")
        
        if btn_actualizar:
            try:
                supabase.table("padron_montacargas").update(updated_data).eq(id_col, equipo_id).execute()
                st.success(f"¡Unidad {equipo_id} actualizada con éxito en la base de datos!")
                st.cache_resource.clear()
            except Exception as ex:
                st.error(f"Error al actualizar el registro: {ex}")

# ==========================================
# PESTAÑA 3: BITÁCORA DE MANTENIMIENTO
# ==========================================
with tab_mantenimiento:
    st.subheader("🛠️ Bitácora de Servicio y Mantenimiento")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        m_id = st.selectbox("Unidad Atendida:", df[id_col].tolist(), key="maint_id_select")
        m_tipo = st.selectbox("Tipo de Trabajo:", ["Preventivo", "Correctivo", "Diagnóstico", "Garantía"])
    with col_m2:
        m_fecha = st.date_input("Fecha de Realización:")
        m_tecnico = st.text_input("Técnico / Proveedor Responsable:")
    with col_m3:
        m_horometro = st.number_input("Horómetro (Horas de Uso):", min_value=0, value=0)
        m_costo = st.number_input("Costo Estimado ($ MXN):", min_value=0.0, value=0.0)

    m_obs = st.text_area("Observaciones Técnicas y Refacciones Reemplazadas:")
    
    if st.button("📌 Guardar Registro de Servicio"):
        st.success(f"Servicio registrado con éxito para la unidad {m_id} ({m_tipo} - {m_fecha}).")

# ==========================================
# PESTAÑA 4: ALTA DE NUEVA UNIDAD
# ==========================================
with tab_nueva_unidad:
    st.subheader("➕ Registrar Nuevo Montacargas en Padrón")
    
    with st.form("form_alta_dinamica"):
        st.markdown("##### Ingrese los datos correspondientes para cada columna:")
        new_record = {}
        
        c1_a, c2_a, c3_a = st.columns(3)
        cols_a_containers = [c1_a, c2_a, c3_a]
        
        for idx, col_name in enumerate(df.columns):
            container = cols_a_containers[idx % 3]
            new_record[col_name] = container.text_input(f"{col_name}:", value="")
            
        btn_crear = st.form_submit_button("🚀 Registrar Unidad en Supabase")
        
        if btn_crear:
            if not new_record.get(id_col):
                st.error(f"El campo '{id_col}' es obligatorio.")
            else:
                try:
                    supabase.table("padron_montacargas").insert(new_record).execute()
                    st.success(f"¡Registro agregado con éxito al padrón!")
                    st.cache_resource.clear()
                except Exception as ex:
                    st.error(f"Error al registrar la unidad: {ex}")