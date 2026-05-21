import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Bitácora Prya", layout="wide", page_icon="📷")
ARCHIVO_CSV = 'bitacora_datos.csv'

# Lista oficial de columnas
COLS = [
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
        df = pd.DataFrame(columns=COLS)
        df.to_csv(ARCHIVO_CSV, index=False)
        return df
    
    # keep_default_na=False evita que "No Aplica" se lea como vacío
    df = pd.read_csv(ARCHIVO_CSV, keep_default_na=False, na_values=[''])
    
    # 1. Eliminar duplicados
    df = df.loc[:, ~df.columns.duplicated()]

    # 2. Renombrar viejas columnas si existen
    renombres = {
        "Nombre_Propiedad": "Propiedad", 
        "Tipo_Propiedad": "Tipo", 
        "Ubicacion": "Zona", 
        "Fecha_Entrega": "Entrega"
    }
    
    for viejo, nuevo in renombres.items():
        if viejo in df.columns:
            if nuevo not in df.columns:
                df.rename(columns={viejo: nuevo}, inplace=True)
            else:
                df.drop(columns=[viejo], inplace=True)

    # 3. Completar faltantes
    for c in COLS:
        if c not in df.columns: 
            df[c] = ""

    # --- PARCHE DE SEGURIDAD PARA LINKS Y TEXTOS ---
    df['Link_Maps'] = df['Link_Maps'].fillna("").astype(str)
    df['Link_Maps'] = df['Link_Maps'].replace(['nan', 'NaN'], '')

    # 4. Limpieza de tipos booleanos
    bool_cols = ["Foto", "Video", "Drone", "TikTok", "YouTube", "Insta"]
    for c in bool_cols:
        df[c] = df[c].apply(lambda x: True if str(x).lower() in ['true', '1', 'si', 'sí'] else False)

    # MIGRACIÓN DE "N/A" a "No Aplica"
    df.replace("N/A", "No Aplica", inplace=True)

    if df["Edicion_Foto"].dtype == object:
        df["Edicion_Foto"] = df["Edicion_Foto"].replace("", "Pendiente")
    
    if df["Edicion_Video"].dtype == object:
        df["Edicion_Video"] = df["Edicion_Video"].replace("", "No Aplica")
    
    return df[COLS]

def get_asesoras(df):
    if 'Asesora' in df.columns:
        nombres_crudos = df['Asesora'].fillna("").astype(str).unique().tolist()
        lista = [nombre.strip() for nombre in nombres_crudos if nombre.strip() != "" and nombre.strip().lower() != "nan"]
        lista.sort()
        return lista
    return []

# --- INTERFAZ PRINCIPAL ---

st.title("📷 Bitácora de Producción")
menu = st.radio("Navegación:", ["📝 Nueva Captura", "✏️ Editar Registros", "⚡ Pendientes", "📊 Estadísticas"], horizontal=True)
st.markdown("---")

# ---------------------------------------------------------
# 1. NUEVA CAPTURA
# ---------------------------------------------------------
if menu == "📝 Nueva Captura":
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
                e_foto, e_video = "No Aplica", "No Aplica"
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
            df_final = pd.concat([cargar_y_limpiar(), df_new], ignore_index=True)
            df_final.to_csv(ARCHIVO_CSV, index=False)
            st.success(f"✅ Guardado correctamente.")
            time.sleep(1)
            st.rerun()

# ---------------------------------------------------------
# 2. EDITAR
# ---------------------------------------------------------
elif menu == "✏️ Editar Registros":
    st.info("💡 Edita directo en la tabla. Recuerda presionar 'Enter' tras un cambio antes de guardar.")
    df = cargar_y_limpiar()
    
    opciones_foto = ["Pendiente", "Editando", "Entregado", "No Aplica"]
    opciones_video = ["Pendiente", "Montado", "Entregado", "No Aplica"]

    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True, hide_index=True,
        column_config={
            "Foto": st.column_config.CheckboxColumn(width="small"),
            "Video": st.column_config.CheckboxColumn(width="small"),
            "Drone": st.column_config.CheckboxColumn(width="small"),
            # Cambiado a TextColumn para evitar errores de validación
            "Link_Maps": st.column_config.TextColumn("Link Maps"),
            "Edicion_Foto": st.column_config.SelectboxColumn(options=opciones_foto),
            "Edicion_Video": st.column_config.SelectboxColumn(options=opciones_video),
            "Estatus": st.column_config.SelectboxColumn(options=["Realizada", "Cancelada", "Reprogramada"]),
            "ID": st.column_config.TextColumn(disabled=True)
        }
    )

    if st.button("💾 ACTUALIZAR BASE DE DATOS", type="primary"):
        edited.loc[(edited['Video'] == False) & (~edited['Edicion_Video'].isin(['Entregado', 'Montado'])) , 'Edicion_Video'] = 'No Aplica'
        edited.loc[(edited['Foto'] == False) & (~edited['Edicion_Foto'].isin(['Entregado', 'Editando'])), 'Edicion_Foto'] = 'No Aplica'
        
        mask_cancel = edited['Estatus'] == 'Cancelada'
        edited.loc[mask_cancel, 'Edicion_Foto'] = 'No Aplica'
        edited.loc[mask_cancel, 'Edicion_Video'] = 'No Aplica'

        edited = edited.loc[:, ~edited.columns.duplicated()]
        edited.to_csv(ARCHIVO_CSV, index=False)
        st.success("✅ Base de datos actualizada.")
        time.sleep(1)
        st.rerun()

# ---------------------------------------------------------
# 3. PENDIENTES
# ---------------------------------------------------------
elif menu == "⚡ Pendientes":
    st.header("⚡ Tablero de Trabajo")
    st.info("💡 Cambia el estado a 'Entregado' aquí mismo y pulsa 'Guardar Avances'.")
    
    df = cargar_y_limpiar()
    
    filtro_foto_estado = ~df['Edicion_Foto'].isin(['Entregado', 'No Aplica'])
    filtro_foto_si = df['Foto'] == True
    p_foto = df[filtro_foto_estado & filtro_foto_si].copy()
    
    filtro_video_estado = ~df['Edicion_Video'].isin(['Entregado', 'No Aplica'])
    filtro_video_si = df['Video'] == True
    p_video = df[filtro_video_estado & filtro_video_si].copy()
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.subheader(f"📸 Fotos ({len(p_foto)})")
        if not p_foto.empty:
            edited_p_foto = st.data_editor(
                p_foto, key="ed_foto", use_container_width=True, hide_index=True,
                column_config={
                    "ID": st.column_config.TextColumn(disabled=True),
                    "Propiedad": st.column_config.TextColumn(disabled=True),
                    "Asesora": st.column_config.TextColumn(disabled=True),
                    "Fecha": st.column_config.TextColumn(disabled=True),
                    "Edicion_Foto": st.column_config.SelectboxColumn("Estado (Cambiar aquí)", options=["Pendiente", "Editando", "Entregado"]),
                    "Mes": None, "Año": None, "Tipo": None, "Zona": None, "Link_Maps": None,
                    "Estatus": None, "Motivo_Cancel": None, "Foto": None, "Video": None, "Drone": None,
                    "Edicion_Video": None, "Entrega": None, "TikTok": None, "YouTube": None, "Insta": None,
                    "Comentarios": None, "Condicion": None
                }
            )
        else:
            edited_p_foto = None
            st.success("✅ ¡Todo al día en Fotos!")

    with col_p2:
        st.subheader(f"🎬 Videos ({len(p_video)})")
        if not p_video.empty:
            edited_p_video = st.data_editor(
                p_video, key="ed_video", use_container_width=True, hide_index=True,
                column_config={
                    "ID": st.column_config.TextColumn(disabled=True),
                    "Propiedad": st.column_config.TextColumn(disabled=True),
                    "Asesora": st.column_config.TextColumn(disabled=True),
                    "Fecha": st.column_config.TextColumn(disabled=True),
                    "Edicion_Video": st.column_config.SelectboxColumn("Estado (Cambiar aquí)", options=["Pendiente", "Montado", "Entregado"]),
                    "Mes": None, "Año": None, "Tipo": None, "Zona": None, "Link_Maps": None,
                    "Estatus": None, "Motivo_Cancel": None, "Foto": None, "Video": None, "Drone": None,
                    "Edicion_Foto": None, "Entrega": None, "TikTok": None, "YouTube": None, "Insta": None,
                    "Comentarios": None, "Condicion": None
                }
            )
        else:
            edited_p_video = None
            st.success("✅ ¡Todo al día en Videos!")

    st.markdown("---")
    
    if st.button("💾 GUARDAR AVANCES Y LIMPIAR LISTA", type="primary"):
        cambios = False
        df_master = cargar_y_limpiar()
        
        if edited_p_foto is not None:
            for index, row in edited_p_foto.iterrows():
                df_master.loc[df_master['ID'] == row['ID'], 'Edicion_Foto'] = row['Edicion_Foto']
            cambios = True

        if edited_p_video is not None:
            for index, row in edited_p_video.iterrows():
                df_master.loc[df_master['ID'] == row['ID'], 'Edicion_Video'] = row['Edicion_Video']
            cambios = True
            
        if cambios:
            df_master.to_csv(ARCHIVO_CSV, index=False)
            st.balloons()
            st.success("✅ Estados actualizados. Limpiando lista...")
            time.sleep(1)
            st.rerun()

# ---------------------------------------------------------
# 4. ESTADÍSTICAS
# ---------------------------------------------------------
elif menu == "📊 Estadísticas":
    df = cargar_y_limpiar()
    
    if df.empty:
        st.warning("No hay datos registrados aún.")
    else:
        df['Fecha_DT'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha_DT'])
        
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
            df_realizadas = df_view[df_view['Estatus'] == 'Realizada']
            df_canceladas = df_view[df_view['Estatus'] == 'Cancelada']

            k1, k2, k3, k4 = st.columns(4)
            total_real = len(df_realizadas)
            k1.metric("Sesiones Realizadas", total_real)
            k2.metric("Canceladas", len(df_canceladas))
            
            pendientes = df_realizadas[df_realizadas['Edicion_Foto'].isin(['Pendiente', 'Editando'])]
            k3.metric("Fotos Pendientes", len(pendientes))
            
            entregadas = df_realizadas[df_realizadas['Edicion_Foto'] == 'Entregado']
            k4.metric("Fotos Entregadas", len(entregadas))

            st.markdown("---")

            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.subheader("🏆 Top Asesoras (Solo Realizadas)")
                if not df_realizadas.empty and 'Asesora' in df_realizadas.columns:
                    conteo_asesoras = df_realizadas['Asesora'].value_counts()
                    st.bar_chart(conteo_asesoras, color="#4CAF50")
                else:
                    st.info("No hay sesiones realizadas.")
            
            with col_g2:
                st.subheader("📊 Paquetes de Servicios")
                if total_real > 0:
                    mask_f_true = df_realizadas['Foto'] == True
                    mask_f_false = df_realizadas['Foto'] == False
                    mask_v_true = df_realizadas['Video'] == True
                    mask_v_false = df_realizadas['Video'] == False
                    mask_d_true = df_realizadas['Drone'] == True
                    mask_d_false = df_realizadas['Drone'] == False
                    
                    solo_foto = len(df_realizadas[mask_f_true & mask_v_false & mask_d_false])
                    foto_video = len(df_realizadas[mask_f_true & mask_v_true & mask_d_false])
                    foto_video_drone = len(df_realizadas[mask_f_true & mask_v_true & mask_d_true])
                    solo_video = len(df_realizadas[mask_f_false & mask_v_true & mask_d_false])
                    
                    otros = total_real - (solo_foto + foto_video + foto_video_drone + solo_video)
                    
                    data_paquetes = pd.DataFrame({
                        'Paquete': ['Solo Foto', 'Foto + Video', 'Foto + Video + Drone', 'Solo Video', 'Otras Mezclas'],
                        'Cantidad': [solo_foto, foto_video, foto_video_drone, solo_video, otros]
                    })
                    
                    data_paquetes = data_paquetes[data_paquetes['Cantidad'] > 0]
                    
                    fig = px.bar(data_paquetes, x='Paquete', y='Cantidad',
                                 title="Combinaciones realizadas (Cantidad exacta)",
                                 text_auto=True,
                                 color='Paquete')
                    
                    fig.update_layout(showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos suficientes.")

            if not df_canceladas.empty:
                st.markdown("---")
                st.subheader("🚨 Cancelaciones")
                c_can1, c_can2 = st.columns(2)
                with c_can1:
                    st.bar_chart(df_canceladas['Asesora'].value_counts(), color="#FF4B4B")
                with c_can2:
                    st.dataframe(df_canceladas[['Fecha', 'Asesora', 'Propiedad', 'Motivo_Cancel']], hide_index=True)
