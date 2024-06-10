# Importar bibliotecas

import streamlit as st
import geopandas as gpd
import pydeck as pdk
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
from streamlit_option_menu import option_menu

# Configuración de la página
st.set_page_config(
    page_title="Mapas de Chile",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cargar datos
name_comunas = "data/INE/comunas_nac.geojson"
name_zonas = "data/INE/zonas_nac.geojson"

    
@st.cache_data
def read_geojson(geojson_path):
    gpd_file = gpd.read_file(geojson_path)
    return(gpd_file)

# Leer el shapefile utilizando geopandas
gdf_comunas = read_geojson(name_comunas)
gdf_zonas = read_geojson(name_zonas)


#######################
# Sidebar
with st.sidebar:
    st.title('🏂 Información Territorial')
    # st.logo("images/logo_utal.png")
    
    # Selector de región
    regiones = gdf_comunas["NOM_REGION"].unique()
    selected_region = st.selectbox("Selecciona una región", regiones, index = 6)
    
    # Filtrar las comunas según la región seleccionada
    comunas_region = gdf_comunas[gdf_comunas["NOM_REGION"] == selected_region]["NOM_COMUNA"].unique()
    selected_comuna = st.selectbox("Selecciona una comuna", ["Todas"] + list(comunas_region))


# Filtrar los datos según la selección
if selected_comuna == "Todas":
    filtered_gdf = gdf_comunas[gdf_comunas["NOM_REGION"] == selected_region]
else:
    filtered_gdf = gdf_zonas[gdf_zonas["NOM_COMUNA"] == selected_comuna]

# Normalizar los valores para la paleta de colores
values = filtered_gdf["id"].values
norm = plt.Normalize(vmin=values.min(), vmax=values.max())
cmap = plt.get_cmap('viridis')
colors = [cmap(norm(value))[:3] for value in values]  # Obtener valores RGB

# Convertir colores a formato que pydeck entienda (0-255)
colors = [(int(r * 255), int(g * 255), int(b * 255), 140) for r, g, b in colors]
# Añadir los colores al GeoDataFrame
filtered_gdf["colors"] = colors


# Calcular el bounding box y el centro de la geometría filtrada
bbox = filtered_gdf.total_bounds
center_lat = (bbox[1] + bbox[3]) / 2
center_lon = (bbox[0] + bbox[2]) / 2

# Calcular un nivel de zoom aproximado basado en el tamaño del bounding box
def calculate_zoom_level(bbox):
    max_dim = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
    val_zoom = (8 - np.log(max_dim)).round()
    return val_zoom

zoom_level = calculate_zoom_level(bbox)


# Dashboard Main Panel
col = st.columns((1.5, 5, 1.5), gap = "medium")

with col[0]:
    st.subheader("Columna 1")

with col[1]:
    st.subheader('Mapa de Territorial')

    # Configuración de la capa de pydeck para multipolígonos
    layer = pdk.Layer(
        "GeoJsonLayer",
        filtered_gdf,
        opacity=0.9,
        stroked=True,
        # auto_highlight=True,
        filled=True,
        extruded=True,
        wireframe=True,
        pickable=True,
        get_line_width=25,
        line_width_units='common',
        line_width_scale=0,
        line_width_min_pixels=1,
        get_line_color=[0, 0, 0],
        get_fill_color="colors",
        # get_fill_color="properties.colors",
        tooltip={"text": "{NOM_COMUNA}"},
    )

    # Configuración del mapa
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom_level,
        pitch=0
    )

    # Renderizar el mapa en la aplicación de Streamlit
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
          "html": "<b>Comuna:</b> {NOM_COMUNA}<br><b>ID:</b> {id}",
          "style": {
              "backgroundColor": "#02818a",
              "color": "white"}
          }
    )

    st.pydeck_chart(deck)

    # st.divider()

    # Mostrar una tabla de datos del shapefile
    st.subheader("Datos del Shapefile")
    drop_cols = ["OBJECTID","GEOCODIGO", "COMUNA", "PROVINCIA", "REGION", "geometry", "colors"]
    filtered_gdf_display = filtered_gdf.drop(columns=drop_cols, errors='ignore').reset_index(drop=True)
    st.dataframe(filtered_gdf_display,
                 # column_order=("NOM_COMUNA"),
                 use_container_width = True,
                 hide_index=True,
                 width=None,
                 height = 200)
                 

with col[2]:
    st.subheader('Información')
    with st.expander('About', expanded=True):
        st.write('''
            - [:blue[**Diagrama Miro**]](https://miro.com/app/board/uXjVNDBK62g=/).
            - :orange[**Gains/Losses**]: states with high inbound/ outbound migration for selected year
            - :orange[**States Migration**]: percentage of states with annual inbound/ outbound migration > 50,000
            ''')
