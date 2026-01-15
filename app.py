import streamlit as st
import pandas as pd
import plotly.express as px 
import os
import time
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Bitácora Pro", layout="wide", page_icon="📷")
ARCHIVO_CSV = 'bitacora_datos.csv'

# Lista oficial de columnas
COLS_OFICIALES = [
    "ID", "Fecha", "Mes", "Año", "Propiedad", "Tipo", "Zona", 
    "Link_Maps", "Asesora", "Estatus", "Motivo_Cancel",
    "Foto", "Video", "Drone", 
    "Edicion_Foto", "Edicion_Video", "Entrega",
    "TikTok", "YouTube", "Insta", "Comentarios", "Condicion"
]

# --- FUNCIONES ---

def get_mes(dt):
    m = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
         7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    return m[dt.month]

def cargar_y_limpiar():
    if not os.path.exists(ARCHIVO_CSV):
        df = pd.DataFrame(columns=COLS_OFICIALES)
        df.to_csv(ARCHIVO_CSV, index=False)
        return df
    
    df = pd.read_csv(ARCHIVO_CSV, keep_default_na=False, na_values=[''])
    
    # 1. Eliminar duplicados
    df = df.loc[:, ~df.columns.duplicated()]

    # 2. Renombrar columnas viejas
    renombres = {
        "Nombre_Propiedad": "Propiedad", "Tipo_Propiedad": "Tipo",
        "Ubicacion": "Zona", "Estatus_Sesion": "Estatus", 
        "Fecha_Entrega": "Entrega"
    }
    for viejo, nuevo in renombres.items():
        if viejo in df.columns:
            if nuevo not in df.columns:
                df.rename(columns={viejo: nuevo}, inplace=True)
            else:
                df.drop(columns=[viejo], inplace=True)

    # 3. Completar faltantes
    for c in COLS_OFICIALES:
        if c not in df.columns:
            df[c] = ""

    # 4. Limpieza de tipos y MIGRACIÓN DE "N/A" a "No Aplica"
    bool_cols = ["Foto", "Video", "Drone", "TikTok", "YouTube", "Insta"]
    for c in bool_cols:
        df[c] = df[c].apply(lambda x: True if str(x).lower() in ['true', '1', 'si', 'sí'] else False)

    df.replace("N/A", "No Aplica", inplace=True)

    if df["Edicion_Foto"].dtype == object:
        df["Edicion_Foto"] = df["Edicion_Foto"].replace("", "Pendiente")
    
    if df["Edicion_Video"].dtype == object:
        df["Edicion_Video"] = df["Edicion_Video"].replace("", "No Aplica")
    
    return df[COLS_OFICIALES]

def get_asesoras(df):
    if 'Asesora' in df.columns:
        lista = [x for x in df['Asesora'].unique() if str(x).strip() != ""]
        lista.sort()
        return lista
    return []

# --- INTERFAZ ---

st.title("📷 Bitácora de Producción")
menu = st.radio("Navegación:", ["Nueva Captura", "Editar Registros", "📊 Estadísticas Avanzadas"], horizontal=True)
st.markdown("---")

# ---------------------------------------------------------
# 1. NUEVA CAPTURA
# ---------------------------------------------------------
if menu == "Nueva Captura":
    df = cargar_y_limpiar()
    lista_ases = get_asesoras(df) + ["➕ Nueva..."]

    st.subheader("📍 1. Datos de la Propiedad")
    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha", datetime.now())
    prop = c2.text_input("Nombre Propiedad")
    tipo = c3.selectbox("Tipo", ["Casa", "Depa", "Terreno", "Local"])
    
    c4, c5 = st.columns([2, 1])
    zona = c4.text_input("Zona / Colonia")
    maps = c5.text_input("Link Maps")

    st.subheader("👤 2. Gestión")
    c_gest1, c_gest2 = st.columns(2)
    
    sel_ase = c_gest1.selectbox("Asesora", lista_ases)
    asesora_final = c_gest1.text_input("Nombre Nueva Asesora:") if sel_ase == "➕ Nueva..." else sel_ase

    estatus = c_gest2.selectbox("Estatus", ["Realizada", "Cancelada", "Reprogramada"])
    motivo = c_gest2.text_input("Motivo Cancelación") if estatus == "Cancelada" else ""

    st.subheader("🎥 3. Servicios")
    col_s1, col_s2, col_s3 = st.columns(3)
    s_foto = col_s1.toggle("Foto")
    s_video = col_s2.toggle("Video")
    s_drone = col_s3.toggle("Drone")
    
    st.markdown("---")
    c_e1, c_e2 = st.columns(2)
    
    idx_v = 3 if not s_video else 0
    opciones_foto = ["Pendiente", "Editando", "Entregado", "No Aplica"]
    opciones_video = ["Pendiente", "Montado", "Entregado", "No Aplica"]
    
    e_foto = c_e1.selectbox("Edición Foto", opciones_foto)
    e_video = c_e2.selectbox("Edición Video", opciones_video, index=idx_v)
    
    c_com1, c_com2 = st.columns(2)
    condicion = c_com1.select_slider("Condiciones", ["Mala", "Regular", "Buena", "Excelente"], value="Buena")
    coments = c_com2.text_area("Comentarios")

    if st.button("💾 GUARDAR SESIÓN", type="primary"):
        if not prop or not asesora_final:
            st.error("⚠️ Error: Falta Nombre de Propiedad o Asesora.")
        else:
            if estatus == "Cancelada":
                e_foto = "No Aplica"
                e_video = "No Aplica"
            else:
                if not s_foto: e_foto = "No Aplica"
                if not s_video: e_video = "No Aplica"

            nuevo = {
                "ID": datetime.now().strftime("%y%m%d%H%M"),
                "Fecha": fecha, "Mes": get_mes(fecha), "Año": fecha.year,
                "Propiedad": prop, "Tipo": tipo, "Zona": zona, "Link_Maps": maps,
                "Asesora": asesora_final, "Estatus": estatus, "Motivo_Cancel": motivo,
                "Foto": s_foto, "Video": s_video, "Drone": s_drone,
                "Edicion_Foto": e_foto, "Edicion_Video": e_video,
                "Entrega": "", "TikTok": False, "YouTube": False, "Insta": False,
                "Comentarios": coments, "Condicion": condicion
            }
            
            df_new = pd.DataFrame([nuevo])
            df_clean = cargar_y_limpiar()
            df_final = pd.concat([df_clean, df_new], ignore_index=True)
            df_final.to_csv(ARCHIVO_CSV, index=False)
            
            st.success(f"✅ Guardado correctamente.")
            time.sleep(1.2)
            st.rerun()

# ---------------------------------------------------------
# 2. EDITAR
# ---------------------------------------------------------
elif menu == "Editar Registros":
    st.info("💡 Nota: Los cambios de estatus 'Cancelada' o checks de servicios actualizan 'No Aplica' al guardar.")
    df = cargar_y_limpiar()
    
    opciones_foto = ["Pendiente", "Editando", "Entregado", "No Aplica"]
    opciones_video = ["Pendiente", "Montado", "Entregado", "No Aplica"]

    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "Foto": st.column_config.CheckboxColumn(width="small"),
            "Video": st.column_config.CheckboxColumn(width="small"),
            "Drone": st.column_config.CheckboxColumn(width="small"),
            "Link_Maps": st.column_config.LinkColumn("Mapa"),
            "Edicion_Foto": st.column_config.SelectboxColumn(options=opciones_foto, required=True),
            "Edicion_Video": st.column_config.SelectboxColumn(options=opciones_video, required=True),
            "Estatus": st.column_config.SelectboxColumn(options=["Realizada", "Cancelada", "Reprogramada"], required=True),
        }
    )

    if st.button("💾 ACTUALIZAR BASE DE DATOS", type="primary"):
        edited.loc[edited['Video'] == False, 'Edicion_Video'] = 'No Aplica'
        edited.loc[edited['Foto'] == False, 'Edicion_Foto'] = 'No Aplica'
        
        mask_cancel = edited['Estatus'] == 'Cancelada'
        edited.loc[mask_cancel, 'Edicion_Foto'] = 'No Aplica'
        edited.loc[mask_cancel, 'Edicion_Video'] = 'No Aplica'

        edited = edited.loc[:, ~edited.columns.duplicated()]
        edited.to_csv(ARCHIVO_CSV, index=False)
        st.success("✅ Base de datos actualizada.")
        time.sleep(1)
        st.rerun()

# ---------------------------------------------------------
# 3. ESTADÍSTICAS AVANZADAS
# ---------------------------------------------------------
elif menu == "📊 Estadísticas Avanzadas":
    df = cargar_y_limpiar()
    
    if df.empty:
        st.warning("No hay datos registrados aún.")
    else:
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha_DT'])
        
        # --- FILTROS DE TIEMPO ---
        st.markdown("### 🔎 Configuración del Periodo")
        modo_filtro = st.radio("Ver por:", ["Mes", "Año", "Semana (Lun-Vie)", "Rango Personalizado"], horizontal=True)
        
        df_view = df.copy() 
        titulo_grafica = "Histórico Completo"

        if modo_filtro == "Mes":
            c_f1, c_f2 = st.columns(2)
            years = sorted(df['Año'].unique().tolist(), reverse=True)
            sel_year = c_f1.selectbox("Año", years)
            meses_disp = df[df['Año'] == sel_year]['Mes'].unique().tolist()
            sel_mes = c_f2.selectbox("Mes", meses_disp)
            df_view = df[(df['Año'] == sel_year) & (df['Mes'] == sel_mes)]
            titulo_grafica = f"{sel_mes} {sel_year}"

        elif modo_filtro == "Año":
            years = sorted(df['Año'].unique().tolist(), reverse=True)
            sel_year = st.selectbox("Año", years)
            df_view = df[df['Año'] == sel_year]
            titulo_grafica = f"Año {sel_year}"

        elif modo_filtro == "Semana (Lun-Vie)":
            fecha_ref = st.date_input("Selecciona un día de la semana", datetime.now())
            lunes = fecha_ref - timedelta(days=fecha_ref.weekday())
            viernes = lunes + timedelta(days=4)
            st.caption(f"Semana: {lunes.strftime('%d/%m')} al {viernes.strftime('%d/%m')}")
            mask = (df['Fecha_DT'] >= pd.to_datetime(lunes)) & (df['Fecha_DT'] <= pd.to_datetime(viernes))
            df_view = df.loc[mask]
            titulo_grafica = f"Semana del {lunes.strftime('%d-%b')}"

        elif modo_filtro == "Rango Personalizado":
            c_r1, c_r2 = st.columns(2)
            f_inicio = c_r1.date_input("Desde", datetime.now() - timedelta(days=30))
            f_fin = c_r2.date_input("Hasta", datetime.now())
            mask = (df['Fecha_DT'] >= pd.to_datetime(f_inicio)) & (df['Fecha_DT'] <= pd.to_datetime(f_fin))
            df_view = df.loc[mask]
            titulo_grafica = f"Periodo Personalizado"

        st.markdown("---")
        st.header(f"Resultados: {titulo_grafica}")
        
        if df_view.empty:
            st.info("Sin registros en este periodo.")
        else:
            # --- SEPARACIÓN DE DATOS ---
            df_realizadas = df_view[df_view['Estatus'] == 'Realizada']
            df_canceladas = df_view[df_view['Estatus'] == 'Cancelada']

            # 1. MÉTRICAS
            k1, k2, k3, k4 = st.columns(4)
            total_real = len(df_realizadas)
            k1.metric("Sesiones Realizadas", total_real)
            k2.metric("Canceladas", len(df_canceladas))
            
            # Pendientes Reales
            pendientes = df_realizadas[df_realizadas['Edicion_Foto'].isin(['Pendiente', 'Editando'])]
            k3.metric("Fotos Pendientes", len(pendientes))
            
            entregadas = df_realizadas[df_realizadas['Edicion_Foto'] == 'Entregado']
            k4.metric("Fotos Entregadas", len(entregadas))

            st.markdown("---")

            # 2. GRÁFICAS
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.subheader("🏆 Top Asesoras (Solo Realizadas)")
                if not df_realizadas.empty and 'Asesora' in df_realizadas.columns:
                    conteo_asesoras = df_realizadas['Asesora'].value_counts()
                    st.bar_chart(conteo_asesoras, color="#4CAF50")
                else:
                    st.info("No hay sesiones realizadas.")
            
            with col_g2:
                st.subheader("📊 Porcentaje de Servicios")
                if total_real > 0:
                    # Cálculo de porcentajes
                    pct_foto = (df_realizadas['Foto'].sum() / total_real) * 100
                    pct_video = (df_realizadas['Video'].sum() / total_real) * 100
                    pct_drone = (df_realizadas['Drone'].sum() / total_real) * 100
                    
                    data_barras = pd.DataFrame({
                        'Servicio': ['Fotografía', 'Video', 'Drone'],
                        'Porcentaje': [pct_foto, pct_video, pct_drone]
                    })
                    
                    # Gráfica de barras con escala fija 0-100%
                    fig = px.bar(data_barras, x='Servicio', y='Porcentaje',
                                 title=f"Frecuencia de Servicios (Base: {total_real} Sesiones)",
                                 text_auto='.1f', # Muestra el número con 1 decimal
                                 color='Servicio',
                                 range_y=[0, 100]) # Fija la escala hasta el 100%
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay sesiones realizadas para calcular porcentajes.")

            # 3. CANCELACIONES
            if not df_canceladas.empty:
                st.markdown("---")
                st.subheader("🚨 Análisis de Cancelaciones")
                c_can1, c_can2 = st.columns(2)
                
                with c_can1:
                    st.write("**¿Quién cancela más?**")
                    st.bar_chart(df_canceladas['Asesora'].value_counts(), color="#FF4B4B")
                
                with c_can2:
                    st.write("**Detalle de Cancelaciones:**")
                    st.dataframe(df_canceladas[['Fecha', 'Asesora', 'Propiedad', 'Motivo_Cancel']], hide_index=True)