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

# Estilos limpios sobre fondo claro con acentos institucionales y forzado de inputs legibles
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

# Inicializar estados en session_state
if "historial_mantenimientos_local" not in st.session_state:
    st.session_state.historial_mantenimientos_local = []

if "equipos_calendarizados" not in st.session_state:
    st.session_state.equipos_calendarizados = []

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
elif menu == "FC3  Ficha Digital por Equipo" or menu == "🎇 Ficha Digital por Equipo":
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
# MÓDULO 4: GESTIÓN DE MANTENIMIENTO (CMMS)
# ==========================================
elif menu == "🛠️ Gestión de Mantenimiento (CMMS)":
    st.subheader("🛠️ Módulo 4: Gestión de Mantenimiento (CMMS)")
    st.markdown("Control operativo, calendarización por lotes con filtro jerárquico estricto por etapa contractual, calendario activo y expediente.")

    # ------------------------------------------
    # CARGA AUTOMÁTICA DE REGISTROS DESDE SUPABASE
    # ------------------------------------------
    if "datos_remotos_cargados" not in st.session_state:
        try:
            res_cal = supabase.table("calendarizacion_lotes").select("*").execute()
            if res_cal.data:
                st.session_state.equipos_calendarizados = res_cal.data

            res_hist = supabase.table("historial_mantenimientos").select("*").order("created_at", desc=True).execute()
            if res_hist.data:
                st.session_state.historial_mantenimientos_local = res_hist.data
                
            st.session_state.datos_remotos_cargados = True
        except Exception as e:
            st.warning(f"⚠️ Nota de conexión Supabase: {e}")

    tab_cmms1, tab_cmms2, tab_cmms3, tab_cmms4 = st.tabs([
        "📂 1. Calendarización por Lotes (Lista Acumulada)",
        "📅 2. Calendario Activo & Resumen por Día",
        "📂 3. Expediente y Captura de Servicio en Sitio",
        "🔴 4. Bandeja de Inconclusos"
    ])

    cols_p = df_padron.columns.tolist()
    c_inv_key = next((c for c in cols_p if "inventario" in c.lower()), cols_p[0])
    c_ser_key = next((c for c in cols_p if "serie" in c.lower()), cols_p[1] if len(cols_p) > 1 else cols_p[0])
    c_ooad_key = next((c for c in cols_p if "ooad" in c.lower()), "ooad_estado")
    c_contrato_key = next((c for c in cols_p if "contrato" in c.lower()), "etapa_contractual")

    # ==========================================
    # PESTAÑA 1: CALENDARIZACIÓN POR LOTES + TOTAL DE VEHÍCULOS
    # ==========================================
    with tab_cmms1:
        st.markdown("### 🗺️ Calendarización Rápida por Lotes")
        st.markdown("💡 **Jerarquía Aplicada:** 1° Filtrado por `etapa_contractual` ➡️ 2° Filtrado de `ooad_estado` correspondientes.")

        # 1. PRIMER FILTRO FUERA DEL FORMULARIO
        etapas_disponibles = ["Etapa 1 (2022)", "Etapa 2 (2024)", "Etapa 3 (2024)"]
        etapa_seleccionada = st.selectbox(
            "📌 1. Filtrar por Etapa Contractual (`etapa_contractual`):", 
            options=etapas_disponibles,
            key="select_etapa_contrato_lote"
        )
        
        col_etapa = "etapa_contractual" if "etapa_contractual" in df_padron.columns else c_contrato_key
        
        df_etapa_filtro = df_padron[
            df_padron[col_etapa].astype(str).str.strip().str.lower() == etapa_seleccionada.strip().lower()
        ].copy()
        
        if df_etapa_filtro.empty:
            if "Etapa 1" in etapa_seleccionada:
                kw = "etapa 1"
            elif "Etapa 2" in etapa_seleccionada:
                kw = "etapa 2"
            else:
                kw = "etapa 3"
            df_etapa_filtro = df_padron[
                df_padron[col_etapa].astype(str).str.lower().str.contains(kw, na=False)
            ].copy()

        col_ooad = "ooad_estado" if "ooad_estado" in df_padron.columns else c_ooad_key
        sedes_disponibles_etapa = sorted([s for s in df_etapa_filtro[col_ooad].unique() if str(s).strip() != ""]) if not df_etapa_filtro.empty else []

        with st.form("form_calendarizacion_lotes_smart"):
            sedes_lote = st.multiselect(
                f"📌 2. Filtrar por OOAD / Estado (`ooad_estado`) en {etapa_seleccionada}:", 
                options=sedes_disponibles_etapa
            )
            
            fecha_teorica_lote = st.date_input("📌 3. Fecha Teórica Programada para este Lote", value=date.today())
            
            if sedes_lote:
                unidades_previstas = df_etapa_filtro[df_etapa_filtro[col_ooad].isin(sedes_lote)]
                st.caption(f"🔍 **Vista previa:** Se detectaron y agregarán **{len(unidades_previstas)} unidades** correspondientes a `{etapa_seleccionada}`.")

            submitted_lote = st.form_submit_button("➕ Agregar Lote a la Lista Acumulada")
            if submitted_lote and sedes_lote:
                contador_registros = 0
                for sede in sedes_lote:
                    unidades_sede = df_etapa_filtro[df_etapa_filtro[col_ooad] == sede]
                    
                    for _, u_row in unidades_sede.iterrows():
                        etapa_real_val = str(u_row.get(col_etapa, etapa_seleccionada))
                        contrato_real_val = str(u_row.get("num_contrato", u_row.get("contrato", "J2523" if "3" in etapa_real_val else "J1954")))
                        
                        item_cal = {
                            "etapa": etapa_real_val,
                            "contrato": contrato_real_val,
                            "ooad": sede,
                            "inventario": str(u_row.get(c_inv_key, "")),
                            "serie": str(u_row.get(c_ser_key, "")),
                            "fecha_programada": str(fecha_teorica_lote)
                        }
                        if item_cal not in st.session_state.equipos_calendarizados:
                            st.session_state.equipos_calendarizados.append(item_cal)
                            contador_registros += 1
                            
                st.success(f"✅ Se han agregado {contador_registros} unidades de **{etapa_seleccionada}** exitosamente a la lista.")
                st.rerun()
            elif submitted_lote:
                st.warning("⚠️ Selecciona al menos una sede para continuar.")

        # ==========================================
        # LISTADO ACUMULADO + MÉTRICA & SUPABASE
        # ==========================================
        st.markdown("---")
        
        if st.session_state.equipos_calendarizados:
            total_vehiculos_acumulados = len(st.session_state.equipos_calendarizados)
            st.metric(label="📊 Total de Vehículos Registrados a Servicio", value=f"{total_vehiculos_acumulados} Unidades")
            
            col_b1, col_b2, col_b3 = st.columns([2, 2, 1])
            with col_b1:
                if st.button("☁️ Sincronizar Lotes con Supabase"):
                    try:
                        supabase.table("calendarizacion_lotes").insert(st.session_state.equipos_calendarizados).execute()
                        st.success("✅ ¡Lotes calendarizados sincronizados con éxito en Supabase!")
                    except Exception as e:
                        st.error(f"❌ Error al guardar lotes: {e}")
            with col_b3:
                if st.button("🗑️ Vaciar Toda la Lista"):
                    st.session_state.equipos_calendarizados = []
                    st.success("Lista acumulada vaciada correctamente.")
                    st.rerun()

            df_acumulado = pd.DataFrame(st.session_state.equipos_calendarizados)
            
            df_editado = st.data_editor(
                df_acumulado,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor_equipos_calendarizados"
            )
            
            st.session_state.equipos_calendarizados = df_editado.to_dict("records")
        else:
            st.info("ℹ️ Aún no hay unidades acumuladas. Selecciona la etapa y sedes arriba para agregar.")

    # ==========================================
    # PESTAÑA 2: CALENDARIO RESUMIDO POR DÍA
    # ==========================================
    with tab_cmms2:
        st.markdown("### 📅 Calendario Operativo: Resumen de Servicios por Día")
        st.markdown("💡 Vista agrupada que muestra el volumen de unidades calendarizadas distribuidas por fecha de programación.")

        if not st.session_state.equipos_calendarizados:
            st.info("ℹ️ No hay equipos calendarizados todavía. Vaya a la **Pestaña 1** para programar por lotes.")
        else:
            df_cal_bruto = pd.DataFrame(st.session_state.equipos_calendarizados)
            
            if not df_cal_bruto.empty and "fecha_programada" in df_cal_bruto.columns:
                df_resumen_dia = df_cal_bruto.groupby("fecha_programada").agg(
                    Total_Unidades=("inventario", "count"),
                    Etapas_Incluidas=("etapa", lambda x: ", ".join(x.unique())),
                    Sedes_Incluidas=("ooad", lambda x: ", ".join(x.unique()))
                ).reset_index()
                
                df_resumen_dia.columns = ["Fecha Programada", "Total Unidades a Servir", "Etapas en la Fecha", "Sedes / OOADs"]
                
                st.metric(label="📅 Días con Programación Activa", value=f"{len(df_resumen_dia)} Fechas")
                st.markdown("---")
                
                st.dataframe(df_resumen_dia, use_container_width=True, hide_index=True)
                
                st.markdown("---")
                st.markdown("#### 🔍 Detalle Completo de Unidades Calendarizadas")
                st.dataframe(df_cal_bruto, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ No hay datos suficientes para generar el resumen por día.")

    # ==========================================
    # PESTAÑA 3: EXPEDIENTE Y CAPTURA DE SERVICIO EN SITIO
    # ==========================================
    # Formulario de Captura de la Orden de Trabajo
        if serie_sel:
            st.markdown("---")
            col_info1, col_info2, col_info3 = st.columns(3)
            col_info1.metric("Inventario", inv_sel)
            col_info2.metric("Número de Serie", serie_sel)
            col_info3.metric("Sede / OOAD", str(eq_data.get("ooad", eq_data.get(c_ooad_key, "N/D")) if isinstance(eq_data, dict) else "N/D"))
            
            tipo_etiqueta = "Mantenimiento Calendarizado" if "Calendarizado" in tipo_servicio_sel else ("Seguimiento Inconcluso" if "Inconcluso" in tipo_servicio_sel else "Reporte de Fallo")
            st.markdown(f"#### 📝 Registrar Cierre o Continuidad ({tipo_etiqueta})")
            
            with st.form(f"form_captura_ot_{serie_sel}_v5"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_servicio = st.date_input("Fecha de Visita / Cierre de Continuidad", value=fecha_sugerida)
                    nombre_tecnico = st.text_input("Nombre del Técnico / Proveedor Responsable")
                with col_f2:
                    estatus_pantone = st.selectbox(
                        "Estatus Actualizado",
                        [
                            "🟢 Concluido (100%)",
                            "🟡 Sigue Inconcluso / Requiere Nueva Refacción",
                            "🔴 No Realizado"
                        ]
                    )
                    nombre_firmante = st.text_input("Nombre y Cargo de Quien Firmó de Conformidad")
                
                observaciones_ot = st.text_area("Diagnóstico de Continuidad y Acciones Realizadas en esta Visita")
                pdf_evidencia = st.file_uploader("Cargar Nueva Orden de Trabajo / Acta Firmada (PDF)", type=["pdf", "png", "jpg"])
                
                submitted_ot = st.form_submit_button("💾 Guardar y Sincronizar con Supabase")
            
            # NOTA: El procesamiento va FUERA del "with st.form(...)":
            if submitted_ot:
                nuevo_registro = {
                    "tipo_servicio": tipo_etiqueta,
                    "etapa": etapa_asociada,
                    "contrato": contrato_asociado,
                    "ooad": str(eq_data.get("ooad", eq_data.get(c_ooad_key, "N/D")) if isinstance(eq_data, dict) else "N/D"),
                    "serie": serie_sel,
                    "inventario": inv_sel,
                    "fecha": str(fecha_servicio),
                    "tecnico": nombre_tecnico,
                    "estatus": estatus_pantone,
                    "firmante": nombre_firmante,
                    "observaciones": observaciones_ot
                }
                
                # Mostrar datos para diagnóstico en pantalla
                st.write("📦 Datos listos para enviar:", nuevo_registro)
                
                try:
                    response = supabase.table("historial_mantenimientos").insert(nuevo_registro).execute()
                    st.write("📡 Respuesta de Supabase:", response)
                    
                    # Guardar en memoria local
                    st.session_state.historial_mantenimientos_local.insert(0, nuevo_registro)
                    st.success(f"✅ ¡Servicio registrado y guardado en Supabase para la serie {serie_sel}!")
                except Exception as err_db:
                    st.error(f"❌ Error detallado de Supabase: {str(err_db)}")
                
                if "serie_reprogramar_activa" in st.session_state:
                    del st.session_state["serie_reprogramar_activa"]
                    
                st.rerun()r", key=f"btn_del_v5_{serie_sel}_{i}"):
                            st.session_state.historial_mantenimientos_local.remove(serv)
                            st.success("✅ ¡Registro eliminado correctamente!")
                            st.rerun()
                    st.markdown("---")
            else:
                st.info("ℹ️ No hay servicios registrados localmente para esta unidad.")

    # ==========================================
    # PESTAÑA 4: BANDEJA DE INCONCLUSOS & REPROGRAMACIÓN
    # ==========================================
    with tab_cmms4:
        st.markdown("### 🔴 Bandeja de Seguimiento a Servicios Inconclusos y Bloqueados")
        st.markdown("💡 Aquí se listan todas las unidades que quedaron pendientes. Puede dar clic en **'🔄 Atender Continuidad'** para saltar directamente a la Pestaña 3 y registrar la nueva visita.")
        
        inconclusos_locales = [s for s in st.session_state.historial_mantenimientos_local if "Inconcluso" in s.get("estatus", "") or "No Realizado" in s.get("estatus", "")]
        
        if inconclusos_locales:
            for i, inc in enumerate(inconclusos_locales):
                with st.container():
                    col_inc1, col_inc2 = st.columns([4, 1])
                    with col_inc1:
                        st.markdown(f"🚨 **Serie:** {inc['serie']} | **Inventario:** {inc['inventario']} | **Fecha Última:** {inc['fecha']}")
                        st.markdown(f"⚠️ **Estatus:** {inc['estatus']}")
                        st.caption(f"**Motivo / Observación:** {inc['observaciones']}")
                    with col_inc2:
                        if st.button("🔄 Atender Continuidad", key=f"btn_atender_inc_{i}"):
                            st.session_state["serie_reprogramar_activa"] = inc["serie"]
                            st.success("Redirigiendo a la Pestaña 3...")
                            st.rerun()
                    st.markdown("---")
        else:
            st.success("🟢 No hay unidades con servicios inconclusos o no realizados registrados en la sesión actual.")