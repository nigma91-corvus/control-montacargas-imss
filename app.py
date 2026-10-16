import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS AVANZADOS
# ==========================================
st.set_page_config(
    page_title="Control de Montacargas - IMSS CMMS",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para paneles ejecutivos
st.markdown("""
    <style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #38BDF8;
        margin-bottom: 25px;
    }
    .kpi-card {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .card-label {
        color: #94A3B8;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .card-value {
        color: #F8FAFC;
        font-size: 2rem;
        font-weight: 800;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN Y CARGA ROBUSTA DE DATOS
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def load_padron():
    """Carga el padrón maestro y previene ocultar datos incompletos mediante sanitización"""
    try:
        response = supabase.table("padron_montacargas").select("*").order("id_equipo").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df = df.fillna("") # Reemplaza valores nulos para asegurar visualización 100% limpia
            if "estatus_operativo" not in df.columns:
                df["estatus_operativo"] = "Operativo" # Asigna estatus por defecto si no existe
        return df
    except Exception as e:
        st.error(f"Error de conexión al cargar el padrón: {e}")
        return pd.DataFrame()

def load_mantenimientos():
    """Carga la bitácora de mantenimientos histórica"""
    try:
        response = supabase.table("mantenimientos_montacargas").select("*").order("fecha_servicio", desc=True).execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df = df.fillna("")
        return df
    except:
        return pd.DataFrame()

# Encabezado Principal
st.markdown('<div class="main-title">🚜 Plataforma de Control de Montacargas IMSS</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">División de Transportes y Operación | Coordinación Técnica de Servicios Generales</div>', unsafe_allow_html=True)

df_padron = load_padron()
df_maint = load_mantenimientos()

if df_padron.empty:
    st.warning("No se pudo conectar a la base de datos o el padrón está vacío.")
    st.stop()

id_col = "id_equipo" if "id_equipo" in df_padron.columns else df_padron.columns[0]

# NAVEGACIÓN MODULAR
menu = st.sidebar.radio(
    "📌 Módulos del Sistema",
    [
        "📊 Dashboard & Analítica Flota",
        "🔍 Buscador Universal & Tabla Maestro",
        "🎇 Ficha Digital por Equipo",
        "🛠️ Gestión de Mantenimiento (CMMS)",
        "📝 Editar / Registrar Unidad"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("🌐 **Servidor:** Supabase Cloud Live")
st.sidebar.caption(f"📦 **Total Equipos:** {len(df_padron)}")

# ==========================================
# MÓDULO 1: DASHBOARD & ANALÍTICA DE FLOTA
# ==========================================
if menu == "📊 Dashboard & Analítica Flota":
    st.subheader("📈 Estado Operativo de la Flota")
    
    # Tarjetas de Métricas Ejecutivas
    c1, c2, c3, c4 = st.columns(4)
    total_u = len(df_padron)
    ooad_u = df_padron["ooad_estado"].nunique() if "ooad_estado" in df_padron.columns else 0
    maint_count = len(df_maint) if not df_maint.empty else 0
    costo_acum = pd.to_numeric(df_maint["costo"], errors='coerce').sum() if not df_maint.empty and "costo" in df_maint.columns else 0.0
    
    c1.metric("Total Flota", f"{total_u} Unidades")
    c2.metric("OOAD / Sedes", f"{ooad_u} Coberturas")
    c3.metric("Servicios Totales", f"{maint_count} Eventos")
    c4.metric("Gasto Acumulado Mantenimiento", f"${costo_acum:,.2f} MXN")

    st.markdown("---")
    
    # Gráficas Estadísticas Rápidas
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("##### 📍 Distribución por OOAD / Estado")
        if "ooad_estado" in df_padron.columns:
            counts_ooad = df_padron["ooad_estado"].value_counts().head(10)
            st.bar_chart(counts_ooad)
            
    with col_g2:
        st.markdown("##### 📄 Distribución por Etapa Contractual")
        if "etapa_contractual" in df_padron.columns:
            counts_etapas = df_padron["etapa_contractual"].value_counts()
            st.bar_chart(counts_etapas)

# ==========================================
# MÓDULO 2: BUSCADOR UNIVERSAL & TABLA MAESTRO
# ==========================================
elif menu == "🔍 Buscador Universal & Tabla Maestro":
    st.subheader("🔎 Buscador Multicriterio de Equipos")
    
    f1, f2, f3 = st.columns(3)
    
    with f1:
        ooads = ["Todas"] + sorted([str(x) for x in df_padron["ooad_estado"].unique() if str(x).strip()])
        sel_ooad = st.selectbox("Filtrar por OOAD / Estado:", ooads)
        
    with f2:
        etapas = ["Todas"] + sorted([str(x) for x in df_padron["etapa_contractual"].unique() if str(x).strip()])
        sel_etapa = st.selectbox("Filtrar por Etapa Contractual:", etapas)
        
    with f3:
        search_query = st.text_input("🔎 Búsqueda Global (Serie Chasis, Batería, Cargador, Sede, Factura):", "")

    # Filtrado Robusto
    df_f = df_padron.copy()
    if sel_ooad != "Todas" and "ooad_estado" in df_f.columns:
        df_f = df_f[df_f["ooad_estado"] == sel_ooad]
    if sel_etapa != "Todas" and "etapa_contractual" in df_f.columns:
        df_f = df_f[df_f["etapa_contractual"] == sel_etapa]
    if search_query:
        mask = df_f.astype(str).apply(lambda row: row.str.contains(search_query, case=False, na=False).any(), axis=1)
        df_f = df_f[mask]

    st.markdown(f"**Coincidencias encontradas:** {len(df_f)} de {len(df_padron)} equipos.")
    st.dataframe(df_f, use_container_width=True, hide_index=True)
    
    # Exportar Consulta
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_f.to_excel(writer, index=False, sheet_name='Consulta_Padrón')
        
    st.download_button(
        "📥 Descargar Consulta en Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"consulta_montacargas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==========================================
# MÓDULO 3: FICHA DIGITAL POR EQUIPO (KARDEX)
# ==========================================
elif menu == "🎇 Ficha Digital por Equipo":
    st.subheader("🎇 Expediente Técnico Individual")
    
    selected_unit = st.selectbox("Selecciona la Unidad para Consultar Expediente:", df_padron[id_col].tolist())
    unit_data = df_padron[df_padron[id_col] == selected_unit].iloc[0]
    
    st.markdown(f"### 🚜 Ficha Técnica: **{selected_unit}**")
    
    fc1, fc2, fc3 = st.columns(3)
    
    with fc1:
        st.info("📍 **Ubicación Operativa**")
        st.write(f"**OOAD / Estado:** {unit_data.get('ooad_estado', 'N/A')}")
        st.write(f"**Almacén / Sede:** {unit_data.get('almacen_sede', 'N/A')}")
        st.write(f"**Área de Asignación:** {unit_data.get('area_asignacion', 'N/A')}")
        
    with fc2:
        st.success("⚙️ **Números de Serie y Componentes**")
        st.write(f"**Serie Montacargas (Chasis):** {unit_data.get('serie_montacargas', 'N/A')}")
        st.write(f"**Serie Batería:** {unit_data.get('serie_bateria', 'N/A')}")
        st.write(f"**Serie Cargador:** {unit_data.get('serie_cargador', 'N/A')}")
        
    with fc3:
        st.warning("📄 **Datos Contractuales y Facturación**")
        st.write(f"**Etapa Contractual:** {unit_data.get('etapa_contractual', 'N/A')}")
        st.write(f"**Número de Factura:** {unit_data.get('no_factura', 'N/A')}")

    st.markdown("---")
    st.markdown(f"#### 📜 Historial de Servicios Registrados para **{selected_unit}**")
    
    if not df_maint.empty and "id_equipo" in df_maint.columns:
        unit_maint = df_maint[df_maint["id_equipo"] == selected_unit]
        if not unit_maint.empty:
            st.dataframe(unit_maint, use_container_width=True, hide_index=True)
        else:
            st.info("Este equipo no tiene eventos registrados en la bitácora de mantenimiento.")
    else:
        st.info("Aún no existen mantenimientos registrados en el sistema.")

# ==========================================
# MÓDULO 4: GESTIÓN DE MANTENIMIENTO (CMMS)
# ==========================================
elif menu == "🛠️ Gestión de Mantenimiento (CMMS)":
    st.subheader("🛠️ Bitácora de Servicio y Control de Taller")
    
    with st.form("form_cmms"):
        mc1, mc2, mc3 = st.columns(3)
        
        with mc1:
            m_id = st.selectbox("Unidad a Atender:", df_padron[id_col].tolist())
            m_tipo = st.selectbox("Tipo de Intervención:", [
                "Mantenimiento Preventivo (Programado)",
                "Mantenimiento Correctivo (Falla)",
                "Diagnóstico y Ajuste",
                "Revisión de Batería e Hidráulica",
                "Atención por Garantía"
            ])
            
        with mc2:
            m_fecha = st.date_input("Fecha del Servicio:")
            m_tecnico = st.text_input("Taller Proveedor / Técnico Responsable:")
            
        with mc3:
            m_horo = st.number_input("Horómetro Actual (Horas):", min_value=0, value=0)
            m_costo = st.number_input("Costo Estimado ($ MXN):", min_value=0.0, value=0.0)
            
        m_obs = st.text_area("Dictamen Técnico, Observaciones y Refacciones Reemplazadas:")
        
        btn_cmms = st.form_submit_button("📌 Registrar Servicio en Supabase")
        
        if btn_cmms:
            try:
                record = {
                    "id_equipo": m_id,
                    "tipo_servicio": m_tipo,
                    "fecha_servicio": str(m_fecha),
                    "horometro": m_horo,
                    "costo": m_costo,
                    "tecnico": m_tecnico,
                    "observaciones": m_obs
                }
                supabase.table("mantenimientos_montacargas").insert(record).execute()
                st.success(f"¡Mantenimiento registrado exitosamente para la unidad {m_id}!")
                st.cache_resource.clear()
            except Exception as ex:
                st.error(f"Error al guardar servicio: {ex}")

    st.markdown("---")
    st.markdown("#### 📋 Bitácora General de Mantenimientos")
    if not df_maint.empty:
        st.dataframe(df_maint, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay registros de servicio guardados.")

# ==========================================
# MÓDULO 5: EDITAR / REGISTRAR UNIDAD
# ==========================================
elif menu == "📝 Editar / Registrar Unidad":
    sub_tab1, sub_tab2 = st.tabs(["📝 Modificar Datos de Unidad", "➕ Alta de Nueva Unidad"])
    
    with sub_tab1:
        st.subheader("Editar Registro Técnico")
        eq_sel = st.selectbox("Selecciona Unidad a Modificar:", df_padron[id_col].tolist(), key="edit_mod_sel")
        row_e = df_padron[df_padron[id_col] == eq_sel].iloc[0]
        
        with st.form("form_edit_mod"):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                e_ooad = st.text_input("OOAD / Estado:", value=str(row_e.get("ooad_estado", "")))
                e_etapa = st.text_input("Etapa Contractual:", value=str(row_e.get("etapa_contractual", "")))
                e_area = st.text_input("Área de Asignación:", value=str(row_e.get("area_asignacion", "")))
            with ec2:
                e_sede = st.text_area("Almacén / Sede:", value=str(row_e.get("almacen_sede", "")), height=100)
                e_fact = st.text_input("No. Factura:", value=str(row_e.get("no_factura", "")))
            with ec3:
                e_s_m = st.text_input("Serie Montacargas:", value=str(row_e.get("serie_montacargas", "")))
                e_s_b = st.text_input("Serie Batería:", value=str(row_e.get("serie_bateria", "")))
                e_s_c = st.text_input("Serie Cargador:", value=str(row_e.get("serie_cargador", "")))
                
            btn_update = st.form_submit_button("💾 Guardar Cambios en Supabase")
            
            if btn_update:
                try:
                    up_data = {
                        "ooad_estado": e_ooad,
                        "etapa_contractual": e_etapa,
                        "area_asignacion": e_area,
                        "almacen_sede": e_sede,
                        "no_factura": e_fact,
                        "serie_montacargas": e_s_m,
                        "serie_bateria": e_s_b,
                        "serie_cargador": e_s_c
                    }
                    supabase.table("padron_montacargas").update(up_data).eq(id_col, eq_sel).execute()
                    st.success(f"¡Unidad {eq_sel} actualizada correctamente!")
                    st.cache_resource.clear()
                except Exception as ex:
                    st.error(f"Error al actualizar datos: {ex}")

    with sub_tab2:
        st.subheader("Registrar Nueva Unidad al Padrón")
        with st.form("form_add_unit"):
            ac1, ac2 = st.columns(2)
            with ac1:
                n_id = st.text_input("ID Equipo (ejem: MTC-179):")
                n_ooad = st.text_input("OOAD / Estado:")
                n_sede = st.text_area("Almacén / Sede:")
                n_etapa = st.text_input("Etapa Contractual:", value="Etapa 1 (2022)")
            with ac2:
                n_sm = st.text_input("Serie Montacargas:")
                n_sb = st.text_input("Serie Batería:")
                n_sc = st.text_input("Serie Cargador:")
                n_fact = st.text_input("No. Factura:")
                
            btn_add = st.form_submit_button("🚀 Crear Unidad en Base de Datos")
            
            if btn_add:
                if not n_id:
                    st.error("El ID del equipo es un campo obligatorio.")
                else:
                    try:
                        n_record = {
                            "id_equipo": n_id,
                            "ooad_estado": n_ooad,
                            "almacen_sede": n_sede,
                            "etapa_contractual": n_etapa,
                            "serie_montacargas": n_sm,
                            "serie_bateria": n_sb,
                            "serie_cargador": n_sc,
                            "no_factura": n_fact,
                            "area_asignacion": "Por rastrear"
                        }
                        supabase.table("padron_montacargas").insert(n_record).execute()
                        st.success(f"¡Equipo {n_id} registrado en el padrón con éxito!")
                        st.cache_resource.clear()
                    except Exception as ex:
                        st.error(f"Error al crear registro: {ex}")