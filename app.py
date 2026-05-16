import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# Configuración de la página de Streamlit
st.set_page_config(layout="wide", page_title="Mapa de Población Mundial")

st.title("🗺️ Mapa Demográfico Mundial")
st.markdown("Visualiza la población total y la distribución de género (Hombres/Mujeres) por país.")

# 1. Cargar datos geográficos del mundo (incluidos en geopandas)
@st.cache_data
def cargar_datos():
    # Cargar el mapa del mundo de baja resolución
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    
    # Filtrar la Antártida para que el mapa se vea más limpio
    world = world[world['name'] != "Antarctica"]
    
    # Para este ejemplo, simularemos datos realistas de distribución de género.
    # En un entorno real, aquí cruzarías los datos con un CSV del Banco Mundial o la ONU.
    import numpy as np
    np.random.seed(42)
    
    # Añadir columnas de ejemplo para porcentaje de hombres y mujeres
    # La mayoría de los países rondan el 48%-51% de hombres/mujeres
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
# Centrado en coordenadas globales estándar
m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

# Añadir capa Choropleth (mapa de calor por país)
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

# Añadir popups interactivos al pasar el cursor o hacer clic
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
    # Mostramos el mapa interactivo
    st_data = st_folium(m, width=1000, height=600)

with col2:
    st.subheader("Países con más Población")
    # Top 10 países más poblados en la tabla lateral
    top_paises = df_mundo[['name', 'pop_est', 'pct_hombres', 'pct_mujeres']].sort_values(by='pop_est', ascending=False).head(10)
    
    # Formatear números para que sean legibles
    top_paises['pop_est'] = top_paises['pop_est'].apply(lambda x: f"{x:,.0f}")
    
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
