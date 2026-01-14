import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Visor Inmobiliario", layout="wide")
st.title("🏙️ Dataset Inmobiliario (2007-2025)")

# ------------------------------------------------------
# 1. CARGA DE DATOS
# ------------------------------------------------------
@st.cache_data
def load_data(file):
    # Detectar si es CSV o Excel
    if file.name.endswith('.csv'):
        # IMPORTANTE: Definimos separador ';' y decimal ',' por el formato español de tu imagen
        df = pd.read_csv(file, sep=';', decimal=',', encoding='utf-8')
    else:
        df = pd.read_excel(file)
    
    # Normalizar nombres de columnas (quitar espacios extra si los hay)
    df.columns = df.columns.str.strip()
    
    # Crear una columna de FECHA real para que los gráficos entiendan el tiempo
    # Convertimos Trimestre a Mes (T1=Marzo, T2=Junio...) para graficar
    df['mes_aprox'] = df['trim'] * 3
    df['periodo_dt'] = pd.to_datetime(df['ano'].astype(str) + '-' + df['mes_aprox'].astype(str) + '-01')
    
    # Crear etiqueta legible "2007-T1"
    df['periodo_lbl'] = df['ano'].astype(str) + "-T" + df['trim'].astype(str)
    
    return df

# ------------------------------------------------------
# 2. BARRA LATERAL (CONTROLES)
# ------------------------------------------------------
st.sidebar.header("Filtros")

uploaded_file = st.sidebar.file_uploader("Sube tu archivo (CSV/XLS)", type=['csv', 'xlsx', 'ods'])

if uploaded_file is not None:
    try:
        df = load_data(uploaded_file)
        
        # A. SELECTOR DE PRODUCTO (Vivienda, Garaje, Trastero)
        # Usamos los prefijos de tus columnas: viv, gar, tras
        tipo_producto = st.sidebar.radio(
            "¿Qué quieres analizar?",
            options=['Vivienda', 'Garaje', 'Trastero'],
            index=0
        )
        
        # Mapeo para saber qué prefijo usar según la selección
        prefijo = {'Vivienda': 'viv', 'Garaje': 'gar', 'Trastero': 'tras'}[tipo_producto]
        
        # B. SELECTOR DE NIVEL GEOGRÁFICO (geo)
        # Filtramos las opciones únicas de la columna 'geo'
        niveles_geo = df['geo'].unique()
        nivel_seleccionado = st.sidebar.selectbox("Nivel Geográfico", niveles_geo, index=0) # Por defecto Nacional o el 1º
        
        # Filtrar el dataframe por el nivel seleccionado
        df_nivel = df[df['geo'] == nivel_seleccionado]
        
        # C. SELECTOR DE LUGAR ESPECÍFICO
        lugares_seleccionados = []
        
        if nivel_seleccionado == 'Nacional':
            # Si es nacional, no hay que elegir provincia, cogemos todo
            df_filtered = df_nivel
            st.sidebar.info("Mostrando datos Nacionales")
        
        elif nivel_seleccionado == 'Comunidad':
            # Usamos la columna 'ca' (Comunidad Autónoma)
            lista_lugares = sorted(df_nivel['ca'].unique())
            seleccion = st.sidebar.multiselect("Selecciona CC.AA.", lista_lugares, default=lista_lugares[:1])
            df_filtered = df_nivel[df_nivel['ca'].isin(seleccion)]
            
        else: # Provincia
            # Usamos la columna 'prv' (Provincia)
            lista_lugares = sorted(df_nivel['prv'].unique())
            seleccion = st.sidebar.multiselect("Selecciona Provincias", lista_lugares, default=['Madrid', 'Barcelona'] if 'Madrid' in lista_lugares else lista_lugares[:1])
            df_filtered = df_nivel[df_nivel['prv'].isin(seleccion)]

        # D. RANGO DE FECHAS
        min_year = int(df['ano'].min())
        max_year = int(df['ano'].max())
        years = st.sidebar.slider("Periodo", min_year, max_year, (min_year, max_year))
        df_filtered = df_filtered[(df_filtered['ano'] >= years[0]) & (df_filtered['ano'] <= years[1])]

        # ------------------------------------------------------
        # 3. VISUALIZACIÓN
        # ------------------------------------------------------
        
        # Definimos qué columnas pintar según el prefijo elegido
        col_num = f"{prefijo}-num"   # ej: viv-num
        col_precio = f"{prefijo}-imp" # ej: viv-imp (Importe total)
        col_pm2 = f"{prefijo}-pm2"   # ej: viv-pm2
        
        # Definir qué columna usar para la leyenda (Color)
        if nivel_seleccionado == 'Comunidad':
            color_col = 'ca'
        elif nivel_seleccionado == 'Provincia':
            color_col = 'prv'
        else:
            color_col = None # Nacional solo tiene un color

        st.markdown(f"### 📊 Evolución de {tipo_producto}s ({nivel_seleccionado})")

        # Pestañas para organizar gráficos
        tab1, tab2, tab3 = st.tabs(["Número de Operaciones", "Precio m²", "Datos Crudos"])

        with tab1:
            st.subheader("Volumen de Transacciones")
            fig1 = px.line(
                df_filtered, 
                x='periodo_dt', 
                y=col_num, 
                color=color_col,
                hover_data=['periodo_lbl'],
                labels={col_num: 'Nº Operaciones', 'periodo_dt': 'Fecha'},
                markers=True
            )
            st.plotly_chart(fig1, use_container_width=True)

        with tab2:
            st.subheader("Evolución del Precio por m²")
            # Verificamos si existe la columna pm2 (A veces garajes no tienen pm2 limpio)
            if col_pm2 in df_filtered.columns:
                fig2 = px.line(
                    df_filtered, 
                    x='periodo_dt', 
                    y=col_pm2, 
                    color=color_col,
                    hover_data=['periodo_lbl'],
                    labels={col_pm2: 'Precio €/m²', 'periodo_dt': 'Fecha'},
                    markers=True
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning(f"No se encontró la columna de precio m2 ({col_pm2})")

        with tab3:
            st.dataframe(df_filtered.sort_values(['ano', 'trim'], ascending=False))

    except Exception as e:
        st.error(f"Hubo un error al procesar el archivo. Asegúrate de que es un CSV separado por punto y coma (;) o un Excel estándar.")
        st.error(f"Detalle del error: {e}")

else:
    st.info("Esperando archivo... Súbelo en el menú de la izquierda.")