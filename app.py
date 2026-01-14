import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Visor Inmobiliario España", layout="wide")

# ------------------------------------------------------
# 2. FUNCIÓN DE CARGA DE DATOS (LECTURA DIRECTA)
# ------------------------------------------------------
@st.cache_data
def load_data(file_path):
    # Verificamos si el archivo existe en el repositorio
    if not os.path.exists(file_path):
        st.error(f"No se encontró el archivo '{file_path}' en el repositorio.")
        return None

    # Leemos el CSV con el formato español (punto y coma y decimales con coma)
    df = pd.read_csv(file_path, sep=';', decimal=',', encoding='utf-8')
    
    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Crear una columna de FECHA real para los gráficos
    df['mes_aprox'] = df['trim'] * 3
    df['periodo_dt'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes_aprox'].astype(str) + '-01')
    
    # Etiqueta legible
    df['periodo_lbl'] = df['ano'].astype(str) + "-T" + df['trim'].astype(str)
    
    return df

# ------------------------------------------------------
# 3. PROCESO DE CARGA AUTOMÁTICA
# ------------------------------------------------------
# Nombre del archivo tal cual está en tu GitHub
NOMBRE_ARCHIVO = "datos.csv"

df = load_data(NOMBRE_ARCHIVO)

if df is not None:
    st.title("🏙️ Análisis Inmobiliario (2007-2025)")
    
    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Análisis")
    
    # A. Selector de Producto
    tipo_producto = st.sidebar.radio(
        "Activo a analizar:",
        options=['Vivienda', 'Garaje', 'Trastero'],
        index=0
    )
    prefijo = {'Vivienda': 'viv', 'Garaje': 'gar', 'Trastero': 'tras'}[tipo_producto]
    
    # B. Selector de Nivel Geográfico
    niveles_geo = df['geo'].unique()
    nivel_seleccionado = st.sidebar.selectbox("Nivel Geográfico", niveles_geo, index=0)
    
    df_nivel = df[df['geo'] == nivel_seleccionado]
    
    # C. Selector de Lugar Específico
    if nivel_seleccionado == 'Nacional':
        df_filtered = df_nivel
        st.sidebar.info("Mostrando datos totales de España")
    
    elif nivel_seleccionado == 'Comunidad':
        lista_lugares = sorted(df_nivel['ca'].unique())
        seleccion = st.sidebar.multiselect("Selecciona CC.AA.", lista_lugares, default=lista_lugares[:2])
        df_filtered = df_nivel[df_nivel['ca'].isin(seleccion)]
        
    else: # Provincia
        lista_lugares = sorted(df_nivel['prv'].unique())
        # Intentamos pre-seleccionar Madrid y Barcelona si existen
        default_provincias = [p for p in ['Madrid', 'Barcelona'] if p in lista_lugares]
        seleccion = st.sidebar.multiselect("Selecciona Provincias", lista_lugares, default=default_provincias if default_provincias else lista_lugares[:1])
        df_filtered = df_nivel[df_nivel['prv'].isin(seleccion)]

    # D. Rango de Fechas
    min_year, max_year = int(df['ano'].min()), int(df['ano'].max())
    years = st.sidebar.slider("Rango de Años", min_year, max_year, (min_year, max_year))
    df_filtered = df_filtered[(df_filtered['ano'] >= years[0]) & (df_filtered['ano'] <= years[1])]

    # ------------------------------------------------------
    # 4. VISUALIZACIONES
    # ------------------------------------------------------
    col_num = f"{prefijo}-num"
    col_pm2 = f"{prefijo}-pm2"
    
    # Determinar columna para la leyenda
    color_col = 'ca' if nivel_seleccionado == 'Comunidad' else ('prv' if nivel_seleccionado == 'Provincia' else None)

    st.markdown(f"### 📈 Evolución en el mercado de {tipo_producto}s")

    tab1, tab2, tab3 = st.tabs(["🔢 Volumen de Ventas", "💰 Precio por m²", "📋 Tabla de Datos"])

    with tab1:
        fig1 = px.line(
            df_filtered, 
            x='periodo_dt', 
            y=col_num, 
            color=color_col,
            title=f"Número de compraventas de {tipo_producto}s",
            labels={col_num: 'Nº Operaciones', 'periodo_dt': 'Fecha'},
            markers=True,
            template="plotly_white"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        if col_pm2 in df_filtered.columns:
            fig2 = px.line(
                df_filtered, 
                x='periodo_dt', 
                y=col_pm2, 
                color=color_col,
                title=f"Precio medio m² de {tipo_producto}s",
                labels={col_pm2: 'Precio €/m²', 'periodo_dt': 'Fecha'},
                markers=True,
                template="plotly_white"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("No hay datos de precio m² para esta selección.")

    with tab3:
        st.dataframe(df_filtered.sort_values(['ano', 'trim'], ascending=False), use_container_width=True)

else:
    st.warning("Cargando datos... Si el error persiste, comprueba que 'datos.csv' esté en la carpeta principal de tu GitHub.")
