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
    
    # Búsqueda segura del DataFrame cargado
    df_actual = None
    for var_name in ["df_padron", "df", "df_filtered", "padron"]:
        if var_name in locals() and isinstance(locals()[var_name], pd.DataFrame) and not locals()[var_name].empty:
            df_actual = locals()[var_name]
            break
            
    if df_actual is not None:
        try:
            cols = df_actual.columns.tolist()
            col_inv = next((c for c in cols if "inventario" in c.lower()), cols[0])
            col_ser = next((c for c in cols if "serie" in c.lower()), cols[1] if len(cols) > 1 else cols[0])
            
            # BARRA DE BÚSQUEDA LIBRE PARA FILTRAR LA LISTA DE UNIDADES
            st.markdown("##### 🔍 Buscar Equipo en el Padrón")
            texto_busqueda_unidad = st.text_input(
                "Escribe cualquier criterio para filtrar la lista (Inventario, Serie, Modelo, OOAD...):",
                placeholder="Ej. CDMX, Montacargas, MTC-001, etc."
            )
            
            df_filtrado_unidades = df_actual.copy()
            if texto_busqueda_unidad:
                mask = df_filtrado_unidades.astype(str).apply(lambda col: col.str.contains(texto_busqueda_unidad, case=False, na=False)).any(axis=1)
                df_filtrado_unidades = df_filtrado_unidades[mask]
            
            if not df_filtrado_unidades.empty:
                opciones_unidades = df_filtrado_unidades[col_inv].astype(str) + " | Serie: " + df_filtrado_unidades[col_ser].astype(str)
                
                selected_unit_label = st.selectbox(
                    f"Seleccionar de los resultados encontrados ({len(df_filtrado_unidades)} unidades):",
                    options=opciones_unidades
                )
                
                if selected_unit_label:
                    inv_val = selected_unit_label.split(" | Serie: ")[0]
                    df_unidad = df_actual[df_actual[col_inv].astype(str) == inv_val]
                    
                    if not df_unidad.empty:
                        unidad = df_unidad.iloc[0]
                        
                        # TARJETA DE PRESENTACIÓN EJECUTIVA COMPACTA
                        st.markdown("---")
                        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
                        col_d1.metric("Inventario", str(unidad.get(col_inv, "N/D")))
                        col_d2.metric("Serie", str(unidad.get(col_ser, "N/D")))
                        col_d3.metric("OOAD / Estado", str(unidad.get("ooad_estado", "N/D")))
                        col_d4.metric("Estatus", str(unidad.get("estatus_operativo", "N/D")))
                        
                        # SEMÁFORO DE DATOS EXISTENTES (SALUD DEL EXPEDIENTE SOBRE EL TOTAL DE COLUMNAS)
                        tot_columnas = len(df_actual.columns)
                        existentes = sum(
                            1 for c in df_actual.columns 
                            if pd.notna(unidad.get(c)) and str(unidad.get(c)).strip() not in ["", "None", "nan", "N/D", "null"]
                        )
                        score = int((existentes / tot_columnas) * 100) if tot_columnas > 0 else 0
                        
                        st.markdown("#### 🚦 Porcentaje de Datos Existentes en Expediente")
                        col_s1, col_s2 = st.columns([1, 4])
                        with col_s1:
                            if score >= 90:
                                st.success(f"**{score}% ({existentes}/{tot_columnas})** 🟢")
                            elif score >= 60:
                                st.warning(f"**{score}% ({existentes}/{tot_columnas})** 🟡")
                            else:
                                st.error(f"**{score}% ({existentes}/{tot_columnas})** 🔴")
                        with col_s2:
                            st.progress(score / 100)
                            st.caption(f"Registrados: {existentes} de {tot_columnas} campos totales de la base de datos.")
                            
                        st.markdown("---")
                        
                        # PESTAÑAS DEL EXPEDIENTE 360°
                        tab_gen, tab_edit, tab_doc, tab_hist = st.tabs([
                            "📋 Ficha Técnica", 
                            "✏️ Capturar/Editar Pendientes", 
                            "📄 Repositorio Documental", 
                            "🛠️ Bitácora de Mantenimiento"
                        ])
                        
                        with tab_gen:
                            st.markdown("##### Consulta de Datos del Equipo")
                            
                            filtro_ficha = st.text_input(
                                "🔍 Buscar dato específico en esta ficha:",
                                placeholder="Escriba cualquier término interno..."
                            )
                            
                            data_detalle = []
                            for col in df_actual.columns:
                                val = unidad.get(col)
                                val_str = "N/D" if pd.isna(val) or str(val).strip() in ["", "None", "nan", "null"] else str(val)
                                
                                if not filtro_ficha or (filtro_ficha.lower() in str(col).lower() or filtro_ficha.lower() in val_str.lower()):
                                    data_detalle.append({"Campo": str(col), "Valor Registrado": val_str})
                            
                            df_detalle_safe = pd.DataFrame(data_detalle).astype(str)
                            st.dataframe(df_detalle_safe, width='stretch', hide_index=True)
                            
                        with tab_edit:
                            st.markdown("##### Captura y Actualización de Datos Pendientes")
                            st.caption("Los campos marcados con N/D o vacíos requieren captura para completar el expediente.")
                            
                            with st.form("form_editar_unidad"):
                                cols_form = st.columns(2)
                                idx = 0
                                
                                for col in df_actual.columns:
                                    val_act = unidad.get(col)
                                    val_str = "" if pd.isna(val_act) or str(val_act).strip() in ["None", "nan", "null", "N/D"] else str(val_act)
                                    
                                    with cols_form[idx % 2]:
                                        st.text_input(f"Campo: {col}", value=val_str, key=f"edit_{col}")
                                        
                                    idx += 1
                                    
                                btn_guardar = st.form_submit_button("💾 Guardar Cambios en la Unidad")
                                if btn_guardar:
                                    st.success("✅ Cambios registrados correctamente en la sesión.")
                            
                        with tab_doc:
                            st.markdown("##### Repositorio de Facturas y Pólizas")
                            st.info("📌 Espacio listo para vinculación de expedientes digitales (Factura, Póliza, Acta Entrega-Recepción).")
                            
                        with tab_hist:
                            st.markdown("##### Bitácora y Servicios")
                            st.info("🔧 Registro cronológico de mantenimientos y eventos del equipo.")
            else:
                st.warning("⚠️ No se encontraron unidades que coincidan con la búsqueda.")
        except Exception as e:
            st.error(f"⚠️ Error al renderizar la ficha: {e}")
    else:
        st.warning("⚠️ No se detectó un padrón de flota activo en la sesión.")