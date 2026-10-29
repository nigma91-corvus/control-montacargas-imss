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
    /* Fondo general claro y tipografia legible */
    .stApp {
        background-color: #F8F9FA;
        color: #1F2937;
    }
    
    /* Barra lateral institucional en Verde IMSS y texto blanco */
    [data-testid="stSidebar"] {
        background-color: #005A36 !important;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #FFFFFF !important;
    }
    
    /* Forzar texto oscuro legible en selectores, inputs y areas de texto */
    .stTextInput input, .stTextArea textarea, .stSelectbox select, div[data-baseweb="select"] div {
        color: #1F2937 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Forzar fondo blanco y texto oscuro en los menus desplegables flotantes (popovers / listbox) */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"], div[role="listbox"] {
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="popover"] *, div[data-baseweb="menu"] *, ul[role="listbox"] *, div[role="listbox"] * {
        color: #1F2937 !important;
        background-color: #FFFFFF !important;
    }
    ul[role="listbox"] li, div[role="option"], option {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
    }
    ul[role="listbox"] li:hover, div[role="option"]:hover {
        background-color: #E5E7EB !important;
        color: #111827 !important;
    }

    /* Forzar calendario (date_input) claro y legible */
    div[data-baseweb="calendar"], div[data-baseweb="datepicker"] {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
    }
    div[data-baseweb="calendar"] * {
        color: #1F2937 !important;
    }

    /* Correccion para etiquetas de codigo (texto entre backticks) */
    code {
        background-color: #E5E7EB !important;
        color: #005A36 !important;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 600;
    }

    /* Botones de envio de formularios en Verde IMSS con texto blanco destacado */
    .stFormSubmitButton button, button[type="submit"] {
        background-color: #005A36 !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stFormSubmitButton button:hover, button[type="submit"]:hover {
        background-color: #004D25 !important;
        color: #FFFFFF !important;
    }

    /* Textos generales de la app en color oscuro fuerte para buen contraste */
    p, span, label, div, h1, h2, h3, h4, h5, h6 {
        color: #1F2937;
    }

    /* Excepcion para mantener los titulos y textos dentro de la barra lateral en blanco */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    /* Tarjetas de metricas estilizadas claras */
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

    /* Formularios limpios */
    .stForm {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        padding: 20px !important;
        border-radius: 10px !important;
    }

    /* 🟢 ESTILOS EXCLUSIVOS DE IMPRESIÓN REFORZADOS CON AJUSTE AUTOMÁTICO DE GRÁFICA */
    @media print {
        @page {
            size: landscape; /* Configura la pagina por defecto en horizontal para maximizar espacio */
            margin: 1cm;
        }

        /* Ocultar elementos de navegacion e interfaz */
        [data-testid="stSidebar"], button, .stButton, header, footer, iframe {
            display: none !important;
        }
        
        /* Forzar fondo blanco impoluto */
        html, body, .stApp, .main, [data-testid="stAppViewContainer"], .block-container {
            background-color: #FFFFFF !important;
            background: #FFFFFF !important;
            color: #000000 !important;
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
        }

        /* Forzar textos legibles en negro */
        p, span, label, div, h1, h2, h3, h4, h5, h6, .main-title, .sub-title {
            color: #000000 !important;
        }

        /* Ajuste estricto para que las graficas y contenedores de Altair NO se corten */
        .element-container, .stVegaLiteChart, canvas, svg, div[data-testid="stVegaLiteChart"] {
            width: 100% !important;
            max-width: 100% !important;
            overflow: visible !important;
            page-break-inside: avoid !important;
        }

        /* Tarjetas de metricas */
        [data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            border: 1px solid #000000 !important;
            box-shadow: none !important;
        }
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
    
    # 🟢 Botón de impresión directa corregido con parent.window.print()
    import streamlit.components.v1 as components
    
    col_btn_print, col_empty = st.columns([1, 4])
    with col_btn_print:
        if st.button("🖨️ Imprimir / Guardar PDF"):
            components.html("""
                <script>
                    parent.window.print();
                </script>
            """, height=0)
            
    st.markdown("---")
    
    col_f1, col_f2 = st.columns([2, 4])
    with col_f1:
        # 🟢 Selector múltiple para elegir y combinar las etapas a visualizar
        opciones_etapas = ["Etapa 1 (2022)", "Etapa 2 (2024)", "Etapa 3 (2025)", "Etapa 4"]
        etapas_seleccionadas = st.multiselect(
            "🎯 Filtrar Dashboard por Etapa(s):",
            options=opciones_etapas,
            default=opciones_etapas  # Por defecto arranca mostrando todas combinadas
        )
    
    df_dash = df_padron.copy()
    if etapas_seleccionadas:
        mask = pd.Series(False, index=df_dash.index)
        for etapa in etapas_seleccionadas:
            if etapa == "Etapa 4":
                mask |= df_dash["etapa_contractual"].astype(str).str.contains("NO_EXISTE", case=False, na=False)
            else:
                mask |= (df_dash["etapa_contractual"].astype(str).str.strip().str.lower() == etapa.lower())
        df_dash = df_dash[mask]
    else:
        df_dash = df_padron.iloc[0:0]  # Si desmarca todas, muestra la vista vacía

    total_u = len(df_dash)

    # 🟢 OBTENER EL ÚLTIMO ESTATUS REAL DESDE EL HISTORIAL DE MANTENIMIENTOS
    series_inconclusas_set = set()
    series_garantia_set = set()

    if "historial_mantenimientos_local" in st.session_state:
        for reg in st.session_state.historial_mantenimientos_local:
            s_val = str(reg.get("serie", "")).strip()
            est_val = str(reg.get("estatus", "")).lower()
            
            if "inconcluso" in est_val or "refacción" in est_val:
                series_garantia_set.add(s_val)
            elif "no realizado" in est_val:
                series_inconclusas_set.add(s_val)

    inconcluso_count = 0
    garantia_count = 0
    op_count = 0

    col_ser_dash = next((c for c in df_dash.columns if "serie" in c.lower()), df_dash.columns[1] if len(df_dash.columns) > 1 else df_dash.columns[0])

    for _, row in df_dash.iterrows():
        s_ser = str(row.get(col_ser_dash, "")).strip()
        
        if s_ser in series_inconclusas_set:
            inconcluso_count += 1
        elif s_ser in series_garantia_set:
            garantia_count += 1
        else:
            op_count += 1

    disp_porcentaje = (op_count / total_u) * 100 if total_u > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Flota en Vista", f"{total_u} U")
    c2.metric("Disponibilidad", f"{disp_porcentaje:.1f}%")
    c3.metric("🟢 Operativos", f"{op_count} U")
    c4.metric("🟡 Garantía Inconclusa", f"{garantia_count} U")
    c5.metric("🔴 Servicios Inconclusos", f"{inconcluso_count} U")

    st.markdown("---")
    etiquetas_filtro_str = ", ".join(etapas_seleccionadas) if etapas_seleccionadas else "Ninguna"
    st.subheader(f"📍 Distribución por OOAD / Estado y Etapa Contractual ({etiquetas_filtro_str})")
    
    if "ooad_estado" in df_dash.columns and "etapa_contractual" in df_dash.columns and not df_dash.empty:
        # 1. Agrupar datos por OOAD_Estado y Etapa Contractual
        counts_ooad_etapa = df_dash.groupby(["ooad_estado", "etapa_contractual"]).size().reset_index(name="Unidades")
        
        # 2. Asignación de paleta de colores institucional por Etapa
        colores_etapa = alt.Scale(
            domain=['Etapa 1 (2022)', 'Etapa 2 (2024)', 'Etapa 3 (2025)', 'Etapa 4'],
            range=['#005A36', '#1E3A8A', '#D97706', '#9CA3AF']  # Verde IMSS, Azul, Ámbar, Gris
        )

        # 3. Construcción del gráfico de barras apiladas con autosize responsive
        chart = alt.Chart(counts_ooad_etapa).mark_bar().encode(
            x=alt.X('ooad_estado:N', title='OOAD / Estado', sort='-y', 
                    axis=alt.Axis(
                        labelAngle=-45, 
                        labelColor='#111827', 
                        titleColor='#111827', 
                        labelFontSize=10,
                        labelFontWeight='bold',
                        labelOverlap=False
                    )),
            y=alt.Y('Unidades:Q', title='Número de Unidades', 
                    axis=alt.Axis(
                        labelColor='#111827', 
                        titleColor='#111827', 
                        grid=True, 
                        gridColor='#E5E7EB', 
                        format='d'
                    )),
            color=alt.Color(
                'etapa_contractual:N', 
                scale=colores_etapa, 
                legend=alt.Legend(
                    title='Etapa Contractual',
                    titleColor='#111827',
                    titleFontWeight='bold',
                    labelColor='#111827'
                )
            ),
            tooltip=['ooad_estado', 'etapa_contractual', 'Unidades']
        ).properties(
            height=350
        ).configure_view(
            strokeWidth=0, 
            fill='white'
        ).configure(
            background='white'
        ).properties(
            autosize=alt.AutoSizingConfig(type='fit', contains='padding')
        )
        
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
    # PESTAÑA 1: CALENDARIZACIÓN POR LOTES + CONTROL ANTIDUPLICADOS + REPORTE
    # ==========================================
    with tab_cmms1:
        st.markdown("### 🗺️ Calendarización Rápida por Lotes (Control Anti-Duplicados)")
        st.markdown("💡 **Jerarquía Aplicada:** 1° Filtrado por `etapa_contractual` ➡️ 2° Filtrado de `ooad_estado` (excluyendo unidades ya calendarizadas).")

        etapas_disponibles = ["Etapa 1 (2022)", "Etapa 2 (2024)", "Etapa 3 (2025)"]
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

        # ==========================================
        # BLINDAJE 1: OBTENER SERIES YA REGISTRADAS EN LA SESIÓN
        # ==========================================
        series_ya_calendarizadas = set(str(item.get("serie", "")).strip() for item in st.session_state.equipos_calendarizados)
        
        # Excluir tajantemente las series que ya tengan un registro previo
        if not df_etapa_filtro.empty:
            total_en_etapa = len(df_etapa_filtro)
            df_disponibles = df_etapa_filtro[~df_etapa_filtro[c_ser_key].astype(str).str.strip().isin(series_ya_calendarizadas)].copy()
            omitidas = total_en_etapa - len(df_disponibles)
            
            if omitidas > 0:
                st.info(f"ℹ️ Se han omitido **{omitidas} unidades** de esta etapa que ya cuentan con calendarización previa para blindar el sistema contra duplicados.")
        else:
            df_disponibles = df_etapa_filtro

        col_ooad = "ooad_estado" if "ooad_estado" in df_padron.columns else c_ooad_key
        sedes_disponibles_etapa = sorted([s for s in df_disponibles[col_ooad].unique() if str(s).strip() != ""]) if not df_disponibles.empty else []

        with st.form("form_calendarizacion_lotes_smart"):
            sedes_lote = st.multiselect(
                f"📌 2. Filtrar por OOAD / Estado (`ooad_estado`) Disponibles en {etapa_seleccionada}:", 
                options=sedes_disponibles_etapa
            )
            
            fecha_teorica_lote = st.date_input("📌 3. Fecha Teórica Programada para este Lote", value=date.today())
            
            if sedes_lote:
                unidades_previstas = df_disponibles[df_disponibles[col_ooad].isin(sedes_lote)]
                st.caption(f"🔍 **Vista previa:** Se agregarán **{len(unidades_previstas)} unidades nuevas** (100% libres de duplicados).")

            submitted_lote = st.form_submit_button("➕ Agregar Lote a la Lista Acumulada")
            if submitted_lote and sedes_lote:
                contador_registros = 0
                for sede in sedes_lote:
                    unidades_sede = df_disponibles[df_disponibles[col_ooad] == sede]
                    
                    for _, u_row in unidades_sede.iterrows():
                        serie_actual = str(u_row.get(c_ser_key, "")).strip()
                        
                        # BLINDAJE 2: Validación doble por cada unidad antes de meterla
                        if serie_actual and serie_actual not in series_ya_calendarizadas:
                            etapa_real_val = str(u_row.get(col_etapa, etapa_seleccionada))
                            contrato_real_val = str(u_row.get("num_contrato", u_row.get("contrato", "J2523" if "3" in etapa_real_val else "J1954")))
                            
                            item_cal = {
                                "etapa": etapa_real_val,
                                "contrato": contrato_real_val,
                                "ooad": sede,
                                "inventario": str(u_row.get(c_inv_key, "")),
                                "serie": serie_actual,
                                "fecha_programada": str(fecha_teorica_lote)
                            }
                            st.session_state.equipos_calendarizados.append(item_cal)
                            series_ya_calendarizadas.add(serie_actual)
                            contador_registros += 1
                            
                st.success(f"✅ Se han agregado {contador_registros} unidades nuevas exitosamente a la lista.")
                st.rerun()
            elif submitted_lote:
                st.warning("⚠️ Selecciona al menos una sede para continuar.")

        # ==========================================
        # LISTADO ACUMULADO + BLINDAJE EN EL DATA EDITOR
        # ==========================================
        st.markdown("---")
        
        if st.session_state.equipos_calendarizados:
            total_vehiculos_acumulados = len(st.session_state.equipos_calendarizados)
            st.metric(label="📊 Total de Vehículos Registrados a Servicio", value=f"{total_vehiculos_acumulados} Unidades")
            
            col_b1, col_b2, col_b3 = st.columns([2, 2, 1])
            with col_b1:
                if st.button("☁️ Sincronizar Lotes con Supabase"):
                    try:
                        import math
                        
                        # Limpiar valores NaN, omitir id/created_at y convertir vacíos a None (NULL)
                        lotes_limpios = []
                        for item in st.session_state.equipos_calendarizados:
                            item_limpio = {}
                            for k, v in item.items():
                                if k in ["id", "created_at"]:  # Omitir columnas automáticas de Supabase
                                    continue
                                if pd.isna(v) or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))) or v == "":
                                    item_limpio[k] = None  # Enviar como NULL real a la base de datos
                                else:
                                    item_limpio[k] = v
                            lotes_limpios.append(item_limpio)

                        # Limpiar la tabla y reinsertar con datos limpios
                        supabase.table("calendarizacion_lotes").delete().neq("id", 0).execute()
                        supabase.table("calendarizacion_lotes").insert(lotes_limpios).execute()
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
            
            # BLINDAJE 3: Limpiar duplicados si el usuario escribe o duplica filas
            lista_cruda = df_editado.to_dict("records")
            lista_limpia = []
            series_vistas_editor = set()
            
            for item in lista_cruda:
                s_val = str(item.get("serie", "")).strip()
                if s_val and s_val not in series_vistas_editor:
                    series_vistas_editor.add(s_val)
                    lista_limpia.append(item)
                elif not s_val:
                    lista_limpia.append(item)
                    
            st.session_state.equipos_calendarizados = lista_limpia

        # ==========================================
        # REPORTE DE UNIDADES PENDIENTES DE CALENDARIZAR (POR ETAPA)
        # ==========================================
        st.markdown("---")
        st.markdown("### 📋 Reporte de Unidades Pendientes por Calendarizar")
        st.markdown("💡 Selecciona una etapa específica para auditar el volumen exacto y la ubicación de los montacargas que aún no tienen fecha asignada.")

        opciones_reporte_etapa = ["🌐 Todas las Etapas", "Etapa 1 (2022)", "Etapa 2 (2024)", "Etapa 3 (2025)"]
        etapa_reporte_sel = st.radio(
            "📌 Filtrar reporte de pendientes por etapa:",
            options=opciones_reporte_etapa,
            horizontal=True,
            key="radio_etapa_reporte_pendientes"
        )
        
        if "Todas" not in etapa_reporte_sel:
            if "Etapa 1" in etapa_reporte_sel:
                kw = "etapa 1"
            elif "Etapa 2" in etapa_reporte_sel:
                kw = "etapa 2"
            else:
                kw = "etapa 3"
            df_padron_base_reporte = df_padron[
                df_padron[col_etapa].astype(str).str.lower().str.contains(kw, na=False)
            ].copy()
        else:
            df_padron_base_reporte = df_padron.copy()

        df_pendientes = df_padron_base_reporte[~df_padron_base_reporte[c_ser_key].astype(str).str.strip().isin(series_ya_calendarizadas)].copy()

        total_pendientes = len(df_pendientes)
        total_padron_base = len(df_padron_base_reporte)
        porcentaje_avance = ((total_padron_base - total_pendientes) / total_padron_base * 100) if total_padron_base > 0 else 0

        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric(f"Total en {etapa_reporte_sel.replace('🌐 ', '')}", f"{total_padron_base} Unidades")
        col_p2.metric("Pendientes de Calendarizar", f"{total_pendientes} Unidades", delta=f"-{total_pendientes}" if total_pendientes > 0 else "0", delta_color="inverse")
        col_p3.metric("Avance de Calendarización", f"{porcentaje_avance:.1f}%")

        if total_pendientes > 0:
            df_resumen_pendientes = df_pendientes.groupby(col_ooad).agg(
                Unidades_Pendientes=(c_inv_key, "count")
            ).reset_index()
            df_resumen_pendientes.columns = ["Sede / OOAD", "Unidades Pendientes"]
            df_resumen_pendientes = df_resumen_pendientes.sort_values(by="Unidades Pendientes", ascending=False)

            st.markdown(f"#### 📍 Desglose por Sede (OOAD) - {etapa_reporte_sel.replace('🌐 ', '')}")
            st.dataframe(df_resumen_pendientes, use_container_width=True, hide_index=True)

            with st.expander(f"🔍 Ver listado detallado de unidades pendientes ({etapa_reporte_sel.replace('🌐 ', '')})"):
                st.dataframe(df_pendientes, use_container_width=True, hide_index=True)
        else:
            st.success(f"🎉 ¡Excelente noticia! El 100% de las unidades correspondientes a `{etapa_reporte_sel.replace('🌐 ', '')}` ya se encuentran calendarizadas.")

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
    with tab_cmms3:
        st.markdown("### 📂 Expediente Digital & Registro de Orden de Trabajo (OT)")
        st.markdown("Selecciona el tipo de servicio para filtrar los equipos por su fecha programada, atender inconclusos o realizar un reporte de fallo.")

        serie_preseleccionada = st.session_state.get("serie_reprogramar_activa", None)

        tipos_disponibles = [
            "📅 Mantenimiento Calendarizado (Servicio Programado)",
            "🚨 Reporte de Fallo del Equipo (Correctivo / Extraordinario)",
            "🔄 Seguimiento / Conclusión de Servicio Inconcluso"
        ]
        
        default_idx = 2 if serie_preseleccionada else 0
        tipo_servicio_sel = st.selectbox(
            "📌 Seleccione el Tipo de Servicio a Registrar:",
            options=tipos_disponibles,
            index=default_idx,
            key="select_tipo_servicio_ot"
        )

        serie_sel = ""
        inv_sel = ""
        eq_data = None
        fecha_sugerida = date.today()
        etapa_asociada = "N/D"
        contrato_asociado = "N/D"

        if "Calendarizado" in tipo_servicio_sel:
            if not st.session_state.equipos_calendarizados:
                st.warning("⚠️ No hay equipos calendarizados en la Lista Acumulada (Pestaña 1).")
            else:
                fechas_disponibles = sorted(list(set(item["fecha_programada"] for item in st.session_state.equipos_calendarizados)))
                fecha_elegida_cal = st.selectbox("📅 1. Seleccione la Fecha Programada:", options=fechas_disponibles, key="sel_fecha_calendarizada_ot")
                
                equipos_en_fecha = [item for item in st.session_state.equipos_calendarizados if item["fecha_programada"] == fecha_elegida_cal]
                
                opciones_cal_label = {}
                for item in equipos_en_fecha:
                    label = f"Sede: {item['ooad']} | Inv: {item['inventario']} | Serie: {item['serie']} | Etapa: {item['etapa']}"
                    opciones_cal_label[label] = item
                
                eq_label_elegido = st.selectbox("🚜 2. Seleccione el equipo programado para esta fecha:", options=list(opciones_cal_label.keys()), key="sel_eq_por_fecha")
                
                if eq_label_elegido:
                    item_elegido = opciones_cal_label[eq_label_elegido]
                    serie_sel = item_elegido["serie"]
                    inv_sel = item_elegido["inventario"]
                    etapa_asociada = item_elegido["etapa"]
                    contrato_asociado = item_elegido.get("contrato", "N/D")
                    try:
                        fecha_sugerida = datetime.strptime(item_elegido["fecha_programada"], "%Y-%m-%d").date()
                    except:
                        fecha_sugerida = date.today()
                    eq_data = {"ooad": item_elegido["ooad"]}

        elif "Inconcluso" in tipo_servicio_sel:
            inconclusos_reg = [s for s in st.session_state.historial_mantenimientos_local if "Inconcluso" in s.get("estatus", "") or "No Realizado" in s.get("estatus", "")]
            
            if not inconclusos_reg:
                st.success("🟢 No hay servicios inconclusos pendientes de seguimiento.")
            else:
                opciones_inc = {}
                for s in inconclusos_reg:
                    lbl = f"Serie: {s['serie']} | Inv: {s['inventario']} | Última Fecha: {s['fecha']} | Estatus: {s['estatus']}"
                    opciones_inc[lbl] = s
                
                sel_inc_lbl = st.selectbox("🔄 Seleccione el equipo inconcluso a dar continuidad:", options=list(opciones_inc.keys()), key="sel_inc_seguimiento")
                if sel_inc_lbl:
                    reg_ant = opciones_inc[sel_inc_lbl]
                    serie_sel = reg_ant["serie"]
                    inv_sel = reg_ant["inventario"]
                    etapa_asociada = reg_ant.get("etapa", "N/D")
                    contrato_asociado = reg_ant.get("contrato", "N/D")
                    eq_data = {"ooad": reg_ant.get("ooad", "Seguimiento en Sitio")}
                    st.info(f"💡 **Nota:** Está atendiendo la continuidad del servicio previo con observaciones: *'{reg_ant.get('observaciones','')}'*")

        else:
            opciones_equipos_cmms = {}
            for idx, row in df_padron.iterrows():
                inv_v = str(row.get(c_inv_key, "N/D"))
                ser_v = str(row.get(c_ser_key, "N/D"))
                ooad_v = str(row.get("ooad_estado", row.get(c_ooad_key, "N/D")))
                label_eq = f"Sede: {ooad_v} | Inv: {inv_v} | Serie: {ser_v}"
                opciones_equipos_cmms[label_eq] = row

            equipo_elegido_label = st.selectbox("🚜 Seleccione el equipo del Padrón General por Serie / Inventario:", options=list(opciones_equipos_cmms.keys()), key="select_eq_fallo_general")
            
            if equipo_elegido_label:
                eq_data = opciones_equipos_cmms[equipo_elegido_label]
                serie_sel = str(eq_data.get(c_ser_key, ""))
                inv_sel = str(eq_data.get(c_inv_key, ""))
                etapa_asociada = str(eq_data.get("etapa_contractual", "N/D"))
                contrato_asociado = str(eq_data.get("num_contrato", "N/D"))

        if serie_sel:
            ooad_real = "N/D"
            if isinstance(eq_data, dict):
                ooad_real = eq_data.get("ooad", eq_data.get("ooad_estado", eq_data.get(c_ooad_key, "N/D")))
            elif hasattr(eq_data, "get"):
                ooad_real = str(eq_data.get("ooad_estado", eq_data.get("ooad", eq_data.get(c_ooad_key, "N/D"))))
            
            if str(ooad_real).strip().upper() in ["N/D", "NONE", "NAN", ""]:
                match_p = df_padron[df_padron[c_ser_key].astype(str).str.strip() == str(serie_sel).strip()]
                if not match_p.empty:
                    col_ooad_p = "ooad_estado" if "ooad_estado" in df_padron.columns else c_ooad_key
                    ooad_real = match_p.iloc[0].get(col_ooad_p, "N/D")

            st.markdown("---")
            col_info1, col_info2, col_info3 = st.columns(3)
            col_info1.metric("Inventario", inv_sel)
            col_info2.metric("Número de Serie", serie_sel)
            col_info3.metric("Sede / OOAD", ooad_real)
            
            tipo_etiqueta = "Mantenimiento Calendarizado" if "Calendarizado" in tipo_servicio_sel else ("Seguimiento Inconcluso" if "Inconcluso" in tipo_servicio_sel else "Reporte de Fallo")
            st.markdown(f"#### 📝 Registrar Cierre o Continuidad ({tipo_etiqueta})")
            
            with st.form(f"form_captura_ot_{serie_sel}_v6"):
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_servicio = st.date_input("Fecha de Visita / Cierre de Continuidad", value=fecha_sugerida)
                    nombre_tecnico = st.text_input("Nombre del Técnico / Proveedor Responsable")
                    # 🟢 CAMPO NUEVO: Captura del Horómetro Actual
                    horometro_actual = st.number_input("⏱️ Horómetro Actual (Horas)", min_value=0.0, step=1.0, format="%.1f")
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
            
            if submitted_ot:
                nuevo_registro = {
                    "tipo_servicio": tipo_etiqueta,
                    "etapa": etapa_asociada,
                    "contrato": contrato_asociado,
                    "ooad": str(ooad_real),
                    "serie": serie_sel,
                    "inventario": inv_sel,
                    "fecha": str(fecha_servicio),
                    "tecnico": nombre_tecnico,
                    "horometro": float(horometro_actual),  # 🟢 Guardando el valor del horómetro
                    "estatus": estatus_pantone,
                    "firmante": nombre_firmante,
                    "observaciones": observaciones_ot
                }
                
                try:
                    # 1. Guardar el historial en Supabase
                    supabase.table("historial_mantenimientos").insert(nuevo_registro).execute()
                    st.session_state.historial_mantenimientos_local.insert(0, nuevo_registro)
                    
                    # ==========================================
                    # 2. LÓGICA DE LIBERACIÓN DE CALENDARIO VENCIDO
                    # ==========================================
                    st.session_state.equipos_calendarizados = [
                        item for item in st.session_state.equipos_calendarizados 
                        if str(item.get("serie", "")).strip() != str(serie_sel).strip()
                    ]
                    
                    # Remover de la tabla de lotes activos en Supabase
                    supabase.table("calendarizacion_lotes").delete().eq("serie", str(serie_sel)).execute()
                    
                    if "Concluido" in estatus_pantone:
                        st.success(f"✅ ¡Servicio CONCLUIDO para la serie {serie_sel} con horómetro en {horometro_actual} hrs! Unidad liberada exitosamente.")
                    else:
                        st.warning(f"⚠️ Servicio registrado con horómetro en {horometro_actual} hrs y estatus {estatus_pantone}. La unidad se ha enviado a la Bandeja de Inconclusos.")
                        
                except Exception as err_db:
                    st.error(f"❌ Error al procesar en Supabase: {str(err_db)}")
                
                if "serie_reprogramar_activa" in st.session_state:
                    del st.session_state["serie_reprogramar_activa"]
                    
                st.rerun()

            st.markdown("#### 📜 Historial Completo y Trazabilidad de este Equipo")
            historial_equipo = [s for s in st.session_state.historial_mantenimientos_local if s.get("serie") == serie_sel]
            if historial_equipo:
                for i, serv in enumerate(historial_equipo):
                    cols_hist = st.columns([5, 1])
                    with cols_hist[0]:
                        badge_tipo = serv.get('tipo_servicio', 'Servicio')
                        h_val = serv.get('horometro', 'N/D')
                        st.markdown(f"🔹 **[{badge_tipo}] Fecha:** {serv['fecha']} | ⏱️ **Horómetro:** `{h_val} hrs` | **Estatus:** {serv['estatus']}")
                        st.markdown(f"👨‍🔧 **Técnico:** {serv['tecnico']} | **Firmante:** {serv['firmante']}")
                        st.caption(f"Obs: {serv['observaciones']}")
                    with cols_hist[1]:
                        if st.button("🗑️ Borrar", key=f"btn_del_v6_{serie_sel}_{i}"):
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
                        # 🟢 Rescate automático: Si el historial dice N/D, lo busca directo en el padrón por número de serie
                        sede_inc = inc.get('ooad', 'N/D')
                        if str(sede_inc).strip().upper() in ["N/D", "NONE", "NAN", ""]:
                            match_padron = df_padron[df_padron[c_ser_key].astype(str).str.strip() == str(inc['serie']).strip()]
                            if not match_padron.empty:
                                col_ooad_p = "ooad_estado" if "ooad_estado" in df_padron.columns else c_ooad_key
                                sede_inc = match_padron.iloc[0].get(col_ooad_p, "Sede no especificada")

                        st.markdown(f"📍 **Sede / OOAD:** `{sede_inc}`")
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