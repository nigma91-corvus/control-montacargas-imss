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
    """Carga todo el padrón desde Supabase"""
    response = supabase.table("padron_montacargas").select("*").order("id_equipo").execute()
    return pd.DataFrame(response.data)

def get_mantenimientos_data():
    """Carga el historial completo de mantenimientos desde Supabase"""
    try:
        response = supabase.table("mantenimientos_montacargas").select("*").order("fecha_servicio", desc=True).execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

# Encabezado principal
st.markdown('<div class="main-header">🚜 Sistema de Control de Montacargas - IMSS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Coordinación Técnica de Servicios Generales | División de Transportes y Operación</div>', unsafe_allow_html=True)

# Cargar bases de datos
try:
    df = get_padron_data()
    df_maint = get_mantenimientos_data()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")
    st.stop()

if df.empty:
    st.warning("La base de datos está vacía o no se devolvieron registros.")
    st.stop()

id_col = "id_equipo" if "id_equipo" in df.columns else df.columns[0]

# Pestañas Principales
tab_dashboard, tab_editar, tab_mantenimiento, tab_nueva_unidad = st.tabs([
    "📊 Panel General & Filtros", 
    "📝 Modificar Unidad", 
    "🛠️ Bitácora y Expediente de Mantenimiento",
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
    total_maint = len(df_maint) if not df_maint.empty else 0
    costo_total_flota = df_maint["costo"].sum() if not df_maint.empty and "costo" in df_maint.columns else 0.0
    
    col_kpi1.metric("Total en Padrón", f"{total_equipos} unidades")
    col_kpi2.metric("OOAD / Sedes", f"{ooad_count} registradas")
    col_kpi3.metric("Servicios Registrados", f"{total_maint} bitácoras")
    col_kpi4.metric("Costo Mantenimientos", f"${costo_total_flota:,.2f} MXN")

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
        search_query = st.text_input("Búsqueda global (ID, Serie, Sede, Factura):", "")

    # Aplicar filtros
    df_filtered = df.copy()
    if sel_ooad != "Todas" and "ooad_estado" in df.columns:
        df_filtered = df_filtered[df_filtered["ooad_estado"] == sel_ooad]
    if sel_etapa != "Todas" and "etapa_contractual" in df.columns:
        df_filtered = df_filtered[df_filtered["etapa_contractual"] == sel_etapa]
    if search_query:
        mask = df_filtered.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False).any(), axis=1)
        df_filtered = df_filtered[mask]

    st.markdown(f"**Mostrando:** {len(df_filtered)} de {total_equipos} unidades.")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    
    # Exportar a Excel
    output_excel = io.BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Padron_Montacargas')
        if not df_maint.empty:
            df_maint.to_excel(writer, index=False, sheet_name='Bitacora_Mantenimiento')
        
    st.download_button(
        label="📥 Exportar Base Completa a Excel (.xlsx)",
        data=output_excel.getvalue(),
        file_name=f"control_montacargas_imss_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==========================================
# PESTAÑA 2: MODIFICAR UNIDAD
# ==========================================
with tab_editar:
    st.subheader("📝 Edición Estructurada de Unidad")
    
    equipo_id = st.selectbox("Selecciona la Unidad a Modificar:", df[id_col].tolist(), key="edit_select_struct")
    row = df[df[id_col] == equipo_id].iloc[0]
    
    with st.form("form_edicion_estructurada"):
        st.markdown(f"#### Editando equipo: **{equipo_id}**")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            val_ooad = st.text_input("OOAD / Estado:", value=str(row.get("ooad_estado", "")))
            val_etapa = st.text_input("Etapa Contractual:", value=str(row.get("etapa_contractual", "")))
            val_area = st.text_input("Área de Asignación:", value=str(row.get("area_asignacion", "")))
            
        with c2:
            val_sede = st.text_area("Almacén / Sede:", value=str(row.get("almacen_sede", "")), height=100)
            val_factura = st.text_input("No. Factura:", value=str(row.get("no_factura", "")))
            
        with c3:
            val_serie_m = st.text_input("Serie Montacargas:", value=str(row.get("serie_montacargas", "")))
            val_serie_b = st.text_input("Serie Batería:", value=str(row.get("serie_bateria", "")))
            val_serie_c = st.text_input("Serie Cargador:", value=str(row.get("serie_cargador", "")))
            
        btn_actualizar = st.form_submit_button("💾 Guardar Cambios en Supabase")
        
        if btn_actualizar:
            try:
                data_update = {
                    "ooad_estado": val_ooad,
                    "etapa_contractual": val_etapa,
                    "area_asignacion": val_area,
                    "almacen_sede": val_sede,
                    "no_factura": val_factura,
                    "serie_montacargas": val_serie_m,
                    "serie_bateria": val_serie_b,
                    "serie_cargador": val_serie_c
                }
                supabase.table("padron_montacargas").update(data_update).eq(id_col, equipo_id).execute()
                st.success(f"¡Unidad {equipo_id} actualizada correctamente!")
                st.cache_resource.clear()
            except Exception as ex:
                st.error(f"Error al actualizar: {ex}")

# ==========================================
# PESTAÑA 3: BITÁCORA Y EXPEDIENTE DE MANTENIMIENTO
# ==========================================
with tab_mantenimiento:
    st.subheader("🛠️ Módulo Integral de Mantenimiento y Servicios")
    
    subtab_nuevo, subtab_historial = st.tabs(["➕ Registrar Nuevo Servicio", "📖 Expediente Histórico por Unidad"])
    
    with subtab_nuevo:
        with st.form("form_mantenimiento_real"):
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                m_id = st.selectbox("Unidad Atendida:", df[id_col].tolist(), key="maint_id_select")
                m_tipo = st.selectbox("Tipo de Servicio:", [
                    "Mantenimiento Preventivo", 
                    "Mantenimiento Correctivo", 
                    "Diagnóstico y Afinación", 
                    "Revisión de Batería/Sistema Eléctrico", 
                    "Garantía"
                ])
            with cm2:
                m_fecha = st.date_input("Fecha de Realización:")
                m_tecnico = st.text_input("Técnico / Taller Proveedor Responsable:")
            with cm3:
                m_horometro = st.number_input("Horómetro Actual (Horas):", min_value=0, value=0)
                m_costo = st.number_input("Costo Total ($ MXN):", min_value=0.0, value=0.0)

            m_obs = st.text_area("Observaciones Técnicas, Trabajos Realizados y Refacciones Reemplazadas:")
            
            btn_save_maint = st.form_submit_button("📌 Guardar Servicio en Base de Datos")
            
            if btn_save_maint:
                try:
                    maint_record = {
                        "id_equipo": m_id,
                        "tipo_servicio": m_tipo,
                        "fecha_servicio": str(m_fecha),
                        "horometro": m_horometro,
                        "costo": m_costo,
                        "tecnico": m_tecnico,
                        "observaciones": m_obs
                    }
                    supabase.table("mantenimientos_montacargas").insert(maint_record).execute()
                    st.success(f"¡Servicio registrado con éxito para la unidad {m_id}!")
                    st.cache_resource.clear()
                except Exception as ex:
                    st.error(f"Error al guardar el servicio: {ex}")

    with subtab_historial:
        st.markdown("#### Consultar Historial Técnico por Equipo")
        if not df_maint.empty:
            sel_equipo_historial = st.selectbox("Selecciona la Unidad para ver su Expediente:", df[id_col].tolist(), key="hist_eq_sel")
            df_equipo_maint = df_maint[df_maint["id_equipo"] == sel_equipo_historial]
            
            if not df_equipo_maint.empty:
                st.info(f"Se encontraron {len(df_equipo_maint)} registros de servicio para la unidad **{sel_equipo_historial}**.")
                st.dataframe(df_equipo_maint, use_container_width=True, hide_index=True)
            else:
                st.warning(f"La unidad **{sel_equipo_historial}** no cuenta con servicios registrados en la bitácora todavía.")
            
            st.markdown("---")
            st.subheader("📋 Bitácora General de Todos los Servicios")
            st.dataframe(df_maint, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay servicios registrados en la base de datos.")

# ==========================================
# PESTAÑA 4: ALTA DE NUEVA UNIDAD
# ==========================================
with tab_nueva_unidad:
    st.subheader("➕ Registrar Nuevo Montacargas en Padrón")
    
    with st.form("form_alta_nueva"):
        ca, cb = st.columns(2)
        with ca:
            n_id = st.text_input("ID Equipo (ejem: MTC-179):")
            n_ooad = st.text_input("OOAD / Estado:")
            n_sede = st.text_area("Almacén / Sede:")
            n_etapa = st.text_input("Etapa Contractual:", value="Etapa 1 (2022)")
        with cb:
            n_serie_m = st.text_input("Serie Montacargas:")
            n_serie_b = st.text_input("Serie Batería:")
            n_serie_c = st.text_input("Serie Cargador:")
            n_factura = st.text_input("No. Factura:")
            
        btn_crear = st.form_submit_button("🚀 Registrar Unidad en Supabase")
        
        if btn_crear:
            if not n_id:
                st.error("El ID del equipo es obligatorio.")
            else:
                try:
                    new_record = {
                        "id_equipo": n_id,
                        "ooad_estado": n_ooad,
                        "almacen_sede": n_sede,
                        "etapa_contractual": n_etapa,
                        "serie_montacargas": n_serie_m,
                        "serie_bateria": n_serie_b,
                        "serie_cargador": n_serie_c,
                        "no_factura": n_factura,
                        "area_asignacion": "Por rastrear"
                    }
                    supabase.table("padron_montacargas").insert(new_record).execute()
                    st.success(f"¡Equipo {n_id} agregado con éxito al padrón!")
                    st.cache_resource.clear()
                except Exception as ex:
                    st.error(f"Error al registrar la unidad: {ex}")