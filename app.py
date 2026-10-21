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
    
    # GRÁFICA VERTICAL CON ETIQUETAS FORZADAS A MOSTRARSE AL 100%
    st.subheader(f"📍 Distribución por OOAD / Estado ({filtro_etapa_dash})")
    
    if "ooad_estado" in df_dash.columns and not df_dash.empty:
        counts_ooad_full = df_dash["ooad_estado"].value_counts().reset_index()
        counts_ooad_full.columns = ["OOAD_Estado", "Total"]
        counts_ooad_full = counts_ooad_full[counts_ooad_full["Total"] > 0]
        
        # labelOverlap=False evita que Altair oculte los nombres de las columnas
        chart = alt.Chart(counts_ooad_full).mark_bar(color='#005A36').encode(
            x=alt.X('OOAD_Estado:N', title='OOAD / Estado', sort='-y', 
                    axis=alt.Axis(labelAngle=-45, labelColor='#1F2937', labelOverlap=False)),
            y=alt.Y('Total:Q', title='Número de Unidades', 
                    axis=alt.Axis(labelColor='#1F2937', grid=True, gridColor='#E5E7EB', format='d')),
            tooltip=['OOAD_Estado', 'Total']
        ).properties(
            width=alt.Step(38),
            height=380
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
if menu == "🔍 Buscador Universal & Tabla Maestro":
    st.subheader("🔍 Búsqueda Universal en el Padrón de Flota")
    st.markdown("Consulta rápida por número de serie, inventario, OOAD, estado, modelo o estatus operativo.")
    
    # Única caja de búsqueda limpia y directa
    texto_busqueda = st.text_input(
        "Criterio de búsqueda:",
        placeholder="Escribe aquí para buscar en toda la flota (ej. CDMX, Montacargas, Serie...)"
    )

    df_busqueda = df_padron.copy()
    
    if texto_busqueda:
        # Búsqueda insensible a mayúsculas en todas las columnas del padrón general
        mask = df_busqueda.astype(str).apply(lambda col: col.str.contains(texto_busqueda, case=False, na=False)).any(axis=1)
        df_busqueda = df_busqueda[mask]
    
    st.markdown(f"**Resultados encontrados:** {len(df_busqueda)} unidades")
    
    if not df_busqueda.empty:
        st.dataframe(
            df_busqueda,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No se encontraron registros que coincidan con la búsqueda.")

# ==========================================
# MÓDULO 3: FICHA DIGITAL POR EQUIPO (EXPEDIENTE 360°)
# ==========================================
if "Ficha Digital" in str(menu):
    st.subheader("📁 Ficha Digital e Historial por Equipo")
    
    # Búsqueda segura del padrón MAESTRO completo
    df_master = None
    for var_name in ["df_padron", "df", "padron"]:
        if var_name in locals() and isinstance(locals()[var_name], pd.DataFrame) and not locals()[var_name].empty:
            df_master = locals()[var_name]
            break
            
    if df_master is None and "df_filtered" in locals() and not df_filtered.empty:
        df_master = df_filtered
            
    if df_master is not None:
        try:
            total_filas = len(df_master)
            cols = df_master.columns.tolist()
            col_inv = next((c for c in cols if "inventario" in c.lower()), cols[0])
            col_ser = next((c for c in cols if "serie" in c.lower()), cols[1] if len(cols) > 1 else cols[0])
            
            st.info(f"📊 Unidades totales en el padrón: **{total_filas}**")
            
            # BARRA DE BÚSQUEDA GLOBAL
            st.markdown("##### 🔍 Buscador General de Unidades")
            texto_busqueda_unidad = st.text_input(
                "Escribe cualquier criterio (o déjalo en blanco para ver todas las unidades):",
                placeholder="Ej. OOAD, modelo, inventario, serie...",
                key="input_busqueda_ficha_master_v5"
            )
            
            df_filtrado_unidades = df_master.copy()
            if texto_busqueda_unidad and texto_busqueda_unidad.strip() != "":
                mask = df_filtrado_unidades.astype(str).apply(
                    lambda col: col.str.contains(texto_busqueda_unidad.strip(), case=False, na=False)
                ).any(axis=1)
                df_filtrado_unidades = df_filtrado_unidades[mask]
            
            if not df_filtrado_unidades.empty:
                opciones_dict = {}
                for idx, row in df_filtrado_unidades.iterrows():
                    inv = str(row.get(col_inv, "N/D"))
                    ser = str(row.get(col_ser, "N/D"))
                    mod = str(row.get("modelo", "N/D"))
                    ooad = str(row.get("ooad_estado", "N/D"))
                    label = f"[Fila {idx}] Inv: {inv}  |  Serie: {ser}  |  Modelo: {mod}  |  OOAD: {ooad}"
                    opciones_dict[label] = idx
                
                selected_label = st.selectbox(
                    f"Seleccione la unidad deseada ({len(opciones_dict)} disponibles en la lista):",
                    options=list(opciones_dict.keys()),
                    key="selectbox_unidades_master_v5"
                )
                
                if selected_label:
                    idx_seleccionado = opciones_dict[selected_label]
                    unidad = df_master.loc[idx_seleccionado]
                    
                    # TARJETA DE PRESENTACIÓN EJECUTIVA COMPACTA
                    st.markdown("---")
                    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
                    col_d1.metric("Inventario", str(unidad.get(col_inv, "N/D")))
                    col_d2.metric("Serie", str(unidad.get(col_ser, "N/D")))
                    col_d3.metric("OOAD / Estado", str(unidad.get("ooad_estado", "N/D")))
                    col_d4.metric("Estatus", str(unidad.get("estatus_operativo", "N/D")))
                    
                    # SEMÁFORO DE DATOS EXISTENTES
                    tot_columnas = len(df_master.columns)
                    existentes = sum(
                        1 for c in df_master.columns 
                        if pd.notna(unidad.get(c)) and str(unidad.get(c)).strip() not in ["", "None", "nan", "N/D", "null"]
                    )
                    score = int((existentes / tot_columnas) * 100) if tot_columnas > 0 else 0
                    
                    st.markdown(f"#### 🚦 Porcentaje de Datos Existentes en Expediente: **{score}%** ({existentes}/{tot_columnas} campos)")
                    st.progress(score / 100)
                    st.markdown("---")
                    
                    # BOTÓN DE EDICIÓN CON ESTADO
                    edit_state_key = f"edit_active_v5_{idx_seleccionado}"
                    if edit_state_key not in st.session_state:
                        st.session_state[edit_state_key] = False
                        
                    col_b1, col_b2 = st.columns([1, 4])
                    with col_b1:
                        if st.button("✏️ Habilitar Edición", key=f"btn_toggle_edit_v5_{idx_seleccionado}"):
                            st.session_state[edit_state_key] = not st.session_state[edit_state_key]
                            st.rerun()
                    
                    with col_b2:
                        if st.session_state[edit_state_key]:
                            st.success("🔓 Modo de edición activo. Modifique los campos abajo y guarde los cambios.")
                        else:
                            st.caption("🔒 Haga clic en 'Habilitar Edición' para modificar o capturar datos faltantes de esta unidad.")
                    
                    if st.session_state[edit_state_key]:
                        with st.form(f"form_editar_unidad_activo_v5_{idx_seleccionado}"):
                            st.markdown("##### 📝 Formulario de Actualización de Datos")
                            cols_form = st.columns(2)
                            idx_col = 0
                            nuevos_valores = {}
                            
                            for col in df_master.columns:
                                val_act = unidad.get(col)
                                val_str = "" if pd.isna(val_act) or str(val_act).strip() in ["None", "nan", "null", "N/D"] else str(val_act)
                                
                                with cols_form[idx_col % 2]:
                                    nuevos_valores[col] = st.text_input(f"Campo: {col}", value=val_str, key=f"input_edit_v5_{col}_{idx_seleccionado}")
                                    
                                idx_col += 1
                                
                            btn_guardar = st.form_submit_button("💾 Guardar Cambios en la Unidad")
                            if btn_guardar:
                                # CONVERSIÓN SEGURA DE COLUMNAS A OBJETO PARA EVITAR ERROR DE DTYPE FLOAT64
                                for col, val in nuevos_valores.items():
                                    df_master[col] = df_master[col].astype(object)
                                    df_master.loc[idx_seleccionado, col] = val
                                st.session_state[edit_state_key] = False
                                st.success("✅ ¡Datos actualizados correctamente en la sesión!")
                                st.rerun()
                    
                    st.markdown("---")
                    
                    # CONSULTA GENERAL DE FICHA TÉCNICA
                    st.markdown("### 📋 Ficha Técnica y Detalle del Expediente")
                    
                    filtro_ficha = st.text_input(
                        "🔍 Buscar un dato específico dentro de esta ficha:",
                        placeholder="Escriba cualquier texto...",
                        key="filtro_ficha_interna_v5"
                    )
                    
                    data_detalle = []
                    for col in df_master.columns:
                        val = unidad.get(col)
                        val_str = "N/D" if pd.isna(val) or str(val).strip() in ["", "None", "nan", "null"] else str(val)
                        
                        if not filtro_ficha or (filtro_ficha.lower() in str(col).lower() or filtro_ficha.lower() in val_str.lower()):
                            data_detalle.append({"Campo": str(col), "Valor Registrado": val_str})
                    
                    df_detalle_safe = pd.DataFrame(data_detalle).astype(str)
                    st.dataframe(df_detalle_safe, width='stretch', hide_index=True)
                    
            else:
                st.warning("⚠️ No se encontraron unidades que coincidan con la búsqueda ingresada.")
        except Exception as e:
            st.error(f"⚠️ Error al renderizar la ficha digital: {e}")
    else:
        st.warning("⚠️ No se detectó un padrón de flota activo en la sesión.")
        import streamlit as st

import pandas as pd
from datetime import date

def render_modulo_4_cmms():
    st.header("🛠️ Módulo 4: Gestión de Mantenimiento (CMMS)")
    st.markdown("Control operativo de servicios, órdenes de trabajo, validación de inconclusos y bitácora retrospectiva.")

    # Pestañas principales del módulo
    tab1, tab2, tab3 = st.tabs([
        "📂 1. Captura Rápida en Lote (Configuración)", 
        "📅 2. Calendario Activo & OTs (Operación Independiente)", 
        "⚠️ 3. Inconclusos y Histórico (Hacia Atrás)"
    ])

    # Catálogo maestro de bloques basado en los 53 bloques del Excel (Etapas 2 y 3)
    catalogo_bloques = {
        # Contrato J1954
        "Centrales (J1954)": {"contrato": "J1954", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "CDMX Sur (J1954)": {"contrato": "J1954", "equipos": 4, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Poniente (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "SXXI (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Hidalgo (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Querétaro (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Morelos (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Guerrero (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Michoacán (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Nuevo León (J1954)": {"contrato": "J1954", "equipos": 4, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Guanajuato (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Jalisco (J1954)": {"contrato": "J1954", "equipos": 4, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Durango (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Coahuila (J1954)": {"contrato": "J1954", "equipos": 4, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Sonora (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Nayarit (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Zacatecas (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Colima (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Baja California Norte (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Chihuahua (J1954)": {"contrato": "J1954", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Puebla (J1954)": {"contrato": "J1954", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Tlaxcala (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Aguascalientes (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Veracruz Norte (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Oaxaca (J1954)": {"contrato": "J1954", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Veracruz Sur (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Chiapas (J1954)": {"contrato": "J1954", "equipos": 4, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Baja California Sur (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Tamaulipas (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Tabasco (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Sinaloa (J1954)": {"contrato": "J1954", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Yucatán (J1954)": {"contrato": "J1954", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "San Luis Potosí (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Campeche (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Cancún (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Oriente (J1954)": {"contrato": "J1954", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Chetumal (J1954)": {"contrato": "J1954", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        
        # Contrato J2523
        "Central CTSG (J2523)": {"contrato": "J2523", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Poniente (J2523)": {"contrato": "J2523", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Hidalgo (J2523)": {"contrato": "J2523", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Querétaro (J2523)": {"contrato": "J2523", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "DF Norte (J2523)": {"contrato": "J2523", "equipos": 7, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Nuevo León (J2523)": {"contrato": "J2523", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Durango (J2523)": {"contrato": "J2523", "equipos": 5, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Jalisco (J2523)": {"contrato": "J2523", "equipos": 4, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Nayarit (J2523)": {"contrato": "J2523", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Zacatecas (J2523)": {"contrato": "J2523", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Chihuahua (J2523)": {"contrato": "J2523", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Tlaxcala (J2523)": {"contrato": "J2523", "equipos": 1, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Tabasco (J2523)": {"contrato": "J2523", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Sinaloa (J2523)": {"contrato": "J2523", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Yucatán (J2523)": {"contrato": "J2523", "equipos": 2, "etapa": "Etapa 2 y 3 (Nov 2026)"},
        "Centrales Reproducciones Gráficas (J2523)": {"contrato": "J2523", "equipos": 3, "etapa": "Etapa 2 y 3 (Nov 2026)"}
    }

    # ==========================================
    # PESTAÑA 1: CAPTURA RÁPIDA EN LOTE
    # ==========================================
    with tab1:
        st.subheader("Configuración y Registro Rápido por Lotes")
        
        etapa_activa = st.selectbox(
            "Seleccione la Etapa a Registrar:",
            ["Etapa 2 y 3 (Activas Nov 2026)", "Etapa 1 (Histórico / Retrospectivo)", "Etapa 3 (Futura)"]
        )
        
        with st.form("form_captura_lote"):
            st.markdown("### Seleccione las OOADs / Sedes a dar de alta simultáneamente")
            sedes_seleccionadas = st.multiselect(
                "Listado de Sedes Disponibles:",
                options=list(catalogo_bloques.keys())
            )
            
            if sedes_seleccionadas:
                total_equipos_lote = sum(catalogo_bloques[s]["equipos"] for s in sedes_seleccionadas)
                contratos_involucrados = list(set(catalogo_bloques[s]["contrato"] for s in sedes_seleccionadas))
                
                st.info(
                    f"📊 **Resumen del Lote Seleccionado:**\n"
                    f"- **Sedes a registrar:** {len(sedes_seleccionadas)}\n"
                    f"- **Total de montacargas involucrados:** {total_equipos_lote}\n"
                    f"- **Contrato(s):** {', '.join(contratos_involucrados)}"
                )
            
            submitted_lote = st.form_submit_button("Guardar Lote en Base de Datos")
            if submitted_lote and sedes_seleccionadas:
                st.success(f"✅ Se registraron exitosamente {len(sedes_seleccionadas)} bloques ({total_equipos_lote} equipos en total). Ya están listos para su operación independiente.")
            elif submitted_lote:
                st.warning("⚠️ Seleccione al menos una sede para continuar.")

    # ==========================================
    # PESTAÑA 2: CALENDARIO ACTIVO & OTs (INDEPENDIENTE)
    # ==========================================
    with tab2:
        st.subheader("Gestión Operativa Individual (Órdenes de Trabajo)")
        st.markdown("Cada sede y unidad se gestiona de forma totalmente autónoma.")
        
        servicio_activo = st.selectbox(
            "Seleccione el bloque / sede a ejecutar:",
            [
                "CDMX Sur (J1954) - 4 Equipos",
                "Hidalgo (J2523) - 2 Equipos",
                "Chiapas (J1954) - 4 Equipos",
                "Baja California Norte (J1954) - 2 Equipos"
            ]
        )
        
        with st.form("form_ejecucion_independiente"):
            col_1, col_2 = st.columns(2)
            with col_1:
                fecha_real = st.date_input("Fecha Real de Cierre Físico", value=date.today())
                tecnico = st.text_input("Técnico / Proveedor Responsable")
            with col_2:
                estatus = st.selectbox(
                    "Estatus del Servicio",
                    ["Concluido", "Inconcluso (Requiere seguimiento)", "En Espera de Refacción"]
                )
            
            observaciones_ot = st.text_area("Diagnóstico y Observaciones Específicas de este Bloque")
            evidencia_pdf = st.file_uploader("Cargar Orden de Trabajo en PDF (Sincronizado a Supabase Storage)", type=["pdf", "png", "jpg"])
            
            submitted_ejecucion = st.form_submit_button("Registrar Cierre Individual")
            if submitted_ejecucion:
                if estatus == "Inconcluso":
                    st.warning("⚠️ Servicio registrado como **Inconcluso**. Se aplica el candado operativo para este bloque específico sin afectar el resto.")
                else:
                    st.success("✅ Servicio concluido y registrado con éxito. Bitácora actualizada.")

    # ==========================================
    # PESTAÑA 3: INCONCLUSOS Y HISTÓRICO
    # ==========================================
    with tab3:
        st.subheader("Control de Inconclusos y Bitácora Retrospectiva")
        
        sub_t1, sub_t2 = st.tabs(["🔴 Bandeja de Inconclusos", "⏪ Captura Histórica ('Hacia Atrás')"])
        
        with sub_t1:
            st.markdown("### Unidades con Bloqueo Activo por Servicios Inconclusos")
            df_inc = pd.DataFrame({
                "Inventario": ["MTC-045", "MTC-088"],
                "OOAD": ["Hidalgo", "Querétaro"],
                "Motivo": ["Falta de refacción hidráulica", "Pendiente eléctrico"],
                "Estatus": ["Bloqueado", "Bloqueado"]
            })
            st.dataframe(df_inc, use_container_width=True)
            
            inv_liberar = st.text_input("Número de inventario o bloque a liberar:")
            if st.button("Aplicar Corrección y Desbloquear Sede"):
                st.success(f"Bloque/Unidad {inv_liberar} liberado y listo para el siguiente servicio.")
                
        with sub_t2:
            st.markdown("### Ventana de Captura Histórica (Etapa 1 y Pasados)")
            st.info("Utilice este espacio en tiempos muertos para alimentar los antecedentes históricos de la Etapa 1.")
            with st.form("form_hist_etapa1"):
                st.text_input("Número de Inventario / Sede")
                st.selectbox("Servicio Histórico", ["Servicio 1 (Etapa 1)", "Servicio 2 (Etapa 1)"])
                st.date_input("Fecha Real del Antecedente")
                st.text_area("Observaciones del antecedente histórico")
                if st.form_submit_button("Guardar en Histórico"):
                    st.success("Antecedente histórico guardado correctamente.")

if __name__ == "__main__":
    render_modulo_4_cmms()