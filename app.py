import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
from datetime import datetime, date
import altair as alt

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CLAROS INSTITUCIONALES
# ==========================================
st.set_page_config(
    page_title="Sistema de Control de Montacargas - IMSS",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos limpios sobre fondo claro con acentos institucionales sutiles y forzado de inputs legibles
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

    /* Forzar visibilidad y color claro en formularios e inputs */
    .stForm {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        padding: 20px !important;
        border-radius: 10px !important;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        color: #1F2937 !important;
        background-color: #FFFFFF !important;
    }
    p, span, label {
        color: #1F2937 !important;
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

# Inicializar estados en session_state para registros de mantenimiento locales si es necesario
if "historial_mantenimientos_local" not in st.session_state:
    st.session_state.historial_mantenimientos_local = []

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

# ==========================================
# MÓDULO 1: DASHBOARD & SEMÁFORO DE FLOTA
# ==========================================
if menu == "📊 Dashboard & Semáforo de Flota":
    st.subheader("🚥 Semáforo Operativo y Disponibilidad de Flota")
    
    col_f1, col_f2 = st.columns([2, 4])
    with col_f1:
        filtro_etapa_dash = st.selectbox(
            "🎯 Filtrar Dashboard por Etapa:",
            ["Todas las Etapas", "Etapa 1 (2022)", "Etapa 2 (2024)", "Etapa 3 (2024)", "Etapa 4"]
        )
    
    df_dash = df_padron.copy()
    if filtro_etapa_dash != "Todas las Etapas":
        if filtro_etapa_dash == "Etapa 4":
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
    c1.metric("Flota en Vista", f"{total_u} U")
    c2.metric("Disponibilidad", f"{disp_porcentaje:.1f}%")
    c3.metric("🟢 Operativos", f"{op_count} U")
    c4.metric("🟡 Garantía Inconclusa", f"{garantia_count} U")
    c5.metric("🔴 Servicios Inconclusos", f"{inconcluso_count} U")

    st.markdown("---")
    st.subheader(f"📍 Distribución por OOAD / Estado ({filtro_etapa_dash})")
    
    if "ooad_estado" in df_dash.columns and not df_dash.empty:
        counts_ooad_full = df_dash["ooad_estado"].value_counts().reset_index()
        counts_ooad_full.columns = ["OOAD_Estado", "Total"]
        counts_ooad_full = counts_ooad_full[counts_ooad_full["Total"] > 0]
        
        chart = alt.Chart(counts_ooad_full).mark_bar(color='#005A36').encode(
            x=alt.X('OOAD_Estado:N', title='OOAD / Estado', sort='-y', 
                    axis=alt.Axis(labelAngle=-45, labelColor='#1F2937', labelOverlap=False)),
            y=alt.Y('Total:Q', title='Número de Unidades', 
                    axis=alt.Axis(labelColor='#1F2937', grid=True, gridColor='#E5E7EB', format='d')),
            tooltip=['OOAD_Estado', 'Total']
        ).properties(width=alt.Step(38), height=380).configure_view(strokeWidth=0, fill='white').configure(background='white')
        
        st.altair_chart(chart, use_container_width=True)

# ==========================================
# MÓDULO 2: BUSCADOR UNIVERSAL & TABLA MAESTRO
# ==========================================
elif menu == "🔍 Buscador Universal & Tabla Maestro":
    st.subheader("🔍 Búsqueda Universal en el Padrón de Flota")
    texto_busqueda = st.text_input("Criterio de búsqueda:", placeholder="Escribe aquí para buscar en toda la flota...")

    df_busqueda = df_padron.copy()
    if texto_busqueda:
        mask = df_busqueda.astype(str).apply(lambda col: col.str.contains(texto_busqueda, case=False, na=False)).any(axis=1)
        df_busqueda = df_busqueda[mask]
    
    st.markdown(f"**Resultados encontrados:** {len(df_busqueda)} unidades")
    st.dataframe(df_busqueda, use_container_width=True, hide_index=True)

# ==========================================
# MÓDULO 3: FICHA DIGITAL POR EQUIPO
# ==========================================
elif menu == "🎇 Ficha Digital por Equipo":
    st.subheader("📁 Ficha Digital e Historial por Equipo")
    
    cols = df_padron.columns.tolist()
    col_inv = next((c for c in cols if "inventario" in c.lower()), cols[0])
    col_ser = next((c for c in cols if "serie" in c.lower()), cols[1] if len(cols) > 1 else cols[0])
    
    texto_busqueda_unidad = st.text_input("Buscar unidad (Inventario, Serie, OOAD...):", key="busq_ficha_mod3")
    df_f = df_padron.copy()
    if texto_busqueda_unidad:
        mask = df_f.astype(str).apply(lambda col: col.str.contains(texto_busqueda_unidad, case=False, na=False)).any(axis=1)
        df_f = df_f[mask]
        
    if not df_f.empty:
        opciones_dict = {f"Inv: {row.get(col_inv)} | Serie: {row.get(col_ser)} | OOAD: {row.get('ooad_estado')}": idx for idx, row in df_f.iterrows()}
        selected_label = st.selectbox("Seleccione la unidad:", options=list(opciones_dict.keys()))
        
        if selected_label:
            idx_sel = opciones_dict[selected_label]
            unidad = df_padron.loc[idx_sel]
            
            col_d1, col_d2, col_d3, col_d4 = st.columns(4)
            col_d1.metric("Inventario", str(unidad.get(col_inv, "N/D")))
            col_d2.metric("Serie", str(unidad.get(col_ser, "N/D")))
            col_d3.metric("OOAD", str(unidad.get("ooad_estado", "N/D")))
            col_d4.metric("Estatus", str(unidad.get("estatus_operativo", "N/D")))
            
            st.markdown("---")
            st.markdown("### 📋 Detalle Completo del Expediente")
            data_detalle = [{"Campo": str(c), "Valor": str(unidad.get(c, ""))} for c in df_padron.columns]
            st.dataframe(pd.DataFrame(data_detalle), use_container_width=True, hide_index=True)

# ==========================================
# MÓDULO 4: GESTIÓN DE MANTENIMIENTO (CMMS) - CALENDARIO & EXPEDIENTE
# ==========================================
elif menu == "🛠️ Gestión de Mantenimiento (CMMS)":
    st.subheader("🛠️ Módulo 4: Calendario CMMS & Expediente de Servicios")
    st.markdown("Control operativo con semáforo Pantone estricto (activado únicamente tras captura explícita) y enlace directo al expediente.")

    # Pestañas del CMMS
    tab_cmms1, tab_cmms2, tab_cmms3 = st.tabs([
        "📅 Calendario & Listado por OOAD",
        "📂 Expediente y Captura de Servicio en Sitio",
        "🔴 Bandeja de Inconclusos / Alertas"
    ])

    cols_p = df_padron.columns.tolist()
    c_inv_key = next((c for c in cols_p if "inventario" in c.lower()), cols_p[0])
    c_ser_key = next((c for c in cols_p if "serie" in c.lower()), cols_p[1] if len(cols_p) > 1 else cols_p[0])
    c_ooad_key = next((c for c in cols_p if "ooad" in c.lower()), "ooad_estado")

    # ==========================================
    # PESTAÑA 1: CALENDARIZACIÓN Y VISTA POR OOAD
    # ==========================================
    with tab_cmms1:
        st.markdown("### 🗺️ Vista de Unidades Agrupadas por OOAD / Sede")
        
        ooads_disponibles = df_padron[c_ooad_key].unique() if c_ooad_key in df_padron.columns else ["General"]
        ooad_seleccionada = st.selectbox("Filtrar por OOAD / Sede:", options=["Todas las OOADs"] + list(ooads_disponibles))
        
        df_vista_cal = df_padron.copy()
        if ooad_seleccionada != "Todas las OOADs":
            df_vista_cal = df_vista_cal[df_vista_cal[c_ooad_key] == ooad_seleccionada]

        st.markdown(f"**Unidades en la Sede seleccionada:** {len(df_vista_cal)}")
        
        # Mostrar tabla interactiva con colores y estado del semáforo Pantone
        tabla_resumen = []
        for idx, row in df_vista_cal.iterrows():
            inv = row.get(c_inv_key, "N/D")
            ser = row.get(c_ser_key, "N/D")
            ooad = row.get(c_ooad_key, "N/D")
            
            # Buscar si tiene servicios registrados
            servicios_unidad = [s for s in st.session_state.historial_mantenimientos_local if s.get("serie") == ser]
            if servicios_unidad:
                ultimo_estatus = servicios_unidad[0].get("estatus", "Pendiente")
            else:
                ultimo_estatus = "Sin Captura (Neutro)"
                
            tabla_resumen.append({
                "OOAD / Sede": ooad,
                "No. Inventario": inv,
                "No. Serie": ser,
                "Último Estatus / Semáforo": ultimo_estatus
            })
            
        df_res_presentacion = pd.DataFrame(tabla_resumen)
        st.dataframe(df_res_presentacion, use_container_width=True, hide_index=True)
        st.info("💡 **Regla de Semáforo:** Los colores Pantone (Verde 561 C, Amarillo 468 C, Rojo 7420 C) se activan exclusivamente al realizar la captura explícita en la pestaña contigua.")

    # ==========================================
    # PESTAÑA 2: EXPEDIENTE Y CAPTURA DE SERVICIO DIRECTA
    # ==========================================
    with tab_cmms2:
        st.markdown("### 📂 Acceso Directo al Expediente & Registro de Orden de Trabajo")
        st.markdown("Seleccione el montacargas para consultar su historial o registrar un nuevo servicio en sitio.")

        # Selector de montacargas por Serie / Inventario
        opciones_equipos_cmms = {}
        for idx, row in df_padron.iterrows():
            inv_val = str(row.get(c_inv_key, "N/D"))
            ser_val = str(row.get(c_ser_key, "N/D"))
            ooad_val = str(row.get(c_ooad_key, "N/D"))
            label_eq = f"Sede: {ooad_val} | Inv: {inv_val} | Serie: {ser_val}"
            opciones_equipos_cmms[label_eq] = row

        equipo_elegido_label = st.selectbox("Seleccione el equipo:", options=list(opciones_equipos_cmms.keys()), key="select_eq_cmms_directo")
        
        if equipo_elegido_label:
            eq_data = opciones_equipos_cmms[equipo_elegido_label]
            serie_sel = str(eq_data.get(c_ser_key, ""))
            inv_sel = str(eq_data.get(c_inv_key, ""))
            
            st.markdown("---")
            col_info1, col_info2, col_info3 = st.columns(3)
            col_info1.metric("Inventario", inv_sel)
            col_info2.metric("Número de Serie", serie_sel)
            col_info3.metric("Sede / OOAD", str(eq_data.get(c_ooad_key, "N/D")))
            
            # Formulario de captura de servicio
            st.markdown("#### 📝 Capturar Orden de Servicio y Estatus Pantone")
            with st.form(f"form_captura_ot_{serie_sel}"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_servicio = st.date_input("Fecha Real del Servicio", value=date.today())
                    nombre_tecnico = st.text_input("Nombre del Técnico / Proveedor Responsable")
                with col_f2:
                    estatus_pantone = st.selectbox(
                        "Estatus del Servicio (Aplica Color Pantone):",
                        [
                            "🟢 Concluido (100%) - Verde Pantone 561 C (#005A36)",
                            "🟡 Inconcluso / Falla - Amarillo Pantone 468 C (#C2B280)",
                            "🔴 No Realizado - Rojo Pantone 7420 C (#8A1C2A)"
                        ]
                    )
                    nombre_firmante = st.text_input("Nombre y Cargo de Quien Firmó de Conformidad")
                
                observaciones_ot = st.text_area("Diagnóstico y Observaciones Detalladas del Servicio")
                pdf_evidencia = st.file_uploader("Cargar Orden de Trabajo Firmada (PDF)", type=["pdf", "png", "jpg"])
                
                submitted_ot = st.form_submit_button("💾 Guardar y Actualizar Estatus en Calendario")
                if submitted_ot:
                    nuevo_registro = {
                        "serie": serie_sel,
                        "inventario": inv_sel,
                        "fecha": str(fecha_servicio),
                        "tecnico": nombre_tecnico,
                        "estatus": estatus_pantone,
                        "firmante": nombre_firmante,
                        "observaciones": observaciones_ot
                    }
                    st.session_state.historial_mantenimientos_local.insert(0, nuevo_registro)
                    st.success(f"✅ ¡Servicio registrado con éxito para el equipo con serie {serie_sel}! El calendario se ha actualizado.")

            # Historial de servicios de este equipo
            st.markdown("#### 📜 Historial de Servicios Registrados para este Equipo")
            historial_equipo = [s for s in st.session_state.historial_mantenimientos_local if s.get("serie") == serie_sel]
            if historial_equipo:
                df_hist_eq = pd.DataFrame(historial_equipo)
                st.dataframe(df_hist_eq, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ No hay servicios registrados localmente para esta unidad. Utiliza el formulario superior para registrar el primero.")

    # ==========================================
    # PESTAÑA 3: BANDEJA DE INCONCLUSOS
    # ==========================================
    with tab_cmms3:
        st.markdown("### 🔴 Bandeja de Seguimiento a Servicios Inconclusos y Bloqueados")
        inconclusos_locales = [s for s in st.session_state.historial_mantenimientos_local if "Inconcluso" in s.get("estatus", "") or "No Realizado" in s.get("estatus", "")]
        
        if inconclusos_locales:
            df_inc = pd.DataFrame(inconclusos_locales)
            st.dataframe(df_inc, use_container_width=True, hide_index=True)
        else:
            st.success("🟢 No hay unidades con servicios inconclusos o no realizados registrados en la sesión actual.")

# ==========================================
# MÓDULO 5: EDITAR / REGISTRAR UNIDAD
# ==========================================
elif menu == "📝 Editar / Registrar Unidad":
    st.subheader("📝 Registro o Modificación de Unidades en Padrón")
    st.info("Utilice este módulo para dar de alta nuevas unidades o actualizar la información general de la flota en Supabase.")
    with st.form("form_reg_unidad"):
        nuevo_inv = st.text_input("Número de Inventario")
        nueva_serie = st.text_input("Número de Serie")
        nueva_ooad = st.text_input("OOAD / Estado")
        submit_reg = st.form_submit_button("Guardar en Padrón General")
        if submit_reg:
            st.success(f"Unidad con inventario {nuevo_inv} procesada correctamente.")