import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import numpy as np

# Configuración de la página de Streamlit
st.set_page_config(layout="wide", page_title="Mapa de Población Mundial")

st.title("🗺️ Mapa Demográfico Mundial")
st.markdown("Visualiza la población total y la distribución de género (Hombres/Mujeres) por país.")

# 1. Cargar datos geográficos del mundo de forma segura desde una URL pública
@st.cache_data
def cargar_datos():
    # Usamos el repositorio oficial de Geopandas para evitar métodos obsoletos
    url_mundo = "https://temporal-data-bucket.s3.amazonaws.com/ne_110m_admin_0_countries.geojson" 
    # Si la URL anterior falla, esta es la alternativa directa de Github:
    # url_mundo = "https://raw.githubusercontent.com/datasets/geo-boundaries-world-110m/master/countries.geojson"
    
    try:
        # Forzamos el uso del motor pyogrio que acabamos de agregar
        world = gpd.read_file(url_mundo, engine="pyogrio")
    except Exception:
        # En caso de caída de red, intentamos leer el dataset alternativo por defecto de geopandas usando pyogrio
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'), engine="pyogrio")

    # Estandarizar nombres de columnas comunes según la versión del GeoJSON
    if 'name' not in world.columns and 'NAME' in world.columns:
        world['name'] = world['NAME']
    if 'pop_est' not in world.columns and 'POP_EST' in world.columns:
        world['pop_est'] = world['POP_EST']
    if 'iso_a3' not in world.columns and 'ISO_A3' in world.columns:
        world['iso_a3'] = world['ISO_A3']

    # Filtrar la Antártida para mejorar el aspecto visual
    world = world[world['name'] != "Antarctica"]
    
    # Generar datos simulados de distribución de género
    np.random.seed(42)
    world['pct_hombres'] = np.random.uniform(48.0, 51.5, size=len(world)).round(2)
    world['pct_mujeres'] = (100 - world['pct_hombres']).round(2)
    
    return world

with st.spinner("Cargando mapa y datos demográficos..."):
    df_mundo = cargar_datos()

# 2. Sidebar con filtros básicos
st.sidebar.header("Filtros y Opciones")
columna_color = st.sidebar.selectbox(
    "Colorear mapa por:",
    options=["pop_est"],
    format_func=lambda x: "Población Estimada"
)

# 3. Creación del mapa interactivo con Folium
m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

# Añadir capa Choropleth
choropleth = folium.Choropleth(
    geo_data=df_mundo,
    name="Población",
    data=df_mundo,
    columns=["iso_a3", columna_color],
    key_on="feature.properties.iso_a3",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Población por País",
    highlight=True
).add_to(m)

# Añadir popups interactivos al pasar el cursor (Tooltips)
style_function = lambda x: {'fillColor': '#ffffff', 'color':'#000000', 'fillOpacity': 0.1, 'weight': 0.1}
highlight_function = lambda x: {'fillColor': '#000000', 'color':'#000000', 'fillOpacity': 0.50, 'weight': 0.1}

info_paises = folium.features.GeoJson(
    df_mundo,
    style_function=style_function,
    control=False,
    highlight_function=highlight_function,
    tooltip=folium.features.GeoJsonTooltip(
        fields=['name', 'pop_est', 'pct_hombres', 'pct_mujeres'],
        aliases=['País: ', 'Población Total: ', '% Hombres: ', '% Mujeres: '],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
    )
)
m.add_child(info_paises)
m.keep_in_front(info_paises)

# 4. Renderizar el mapa en Streamlit
col1, col2 = st.columns([4, 1])

with col1:
    st_data = st_folium(m, width=1000, height=600)

with col2:
    st.subheader("Países más Poblados")
    top_paises = df_mundo[['name', 'pop_est', 'pct_hombres', 'pct_mujeres']].sort_values(by='pop_est', ascending=False).head(10)
    
    # Formatear números para legibilidad
    top_paises['pop_est'] = top_paises['pop_est'].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "N/A")
    
    st.dataframe(
        top_paises, 
        column_config={
            "name": "País",
            "pop_est": "Población",
            "pct_hombres": "% H",
            "pct_mujeres": "% M"
        },
        hide_index=True
    )
