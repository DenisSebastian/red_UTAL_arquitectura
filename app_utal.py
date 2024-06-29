# Importar bibliotecas

import streamlit as st
import geopandas as gpd
import pandas as pd
#import folium
#from streamlit_folium import st_folium
#import matplotlib.pyplot as plt
#import matplotlib.colors as mcolors
#import branca
import numpy as np
from streamlit_option_menu import option_menu
import altair as alt
import plotly.express as px
from streamlit_plotly_mapbox_events import plotly_mapbox_events
from st_aggrid import AgGrid, GridOptionsBuilder

# variables
APP_TITLE = 'Universidad de Talca'
APP_SUB_TITLE = 'Red de Ex-alumnos'
name_comunas = "data/INE/comunas_nac.geojson"
name_zonas = "data/INE/zonas_nac.geojson"
drop_cols = ["OBJECTID", "COMUNA", "PROVINCIA", "NOM_REGION" , "NOM_PROVIN", 
             "REGION", "geometry", "id"]
path_csv = "originales/dataraw.csv"
col_names = [
"Dirección de correo electrónico",
"NOMBRE ",
"APELLIDO PATERNO",
"APELLIDO MATERNO",
"AÑO DE EGRESO DE LA ESCUELA DE ARQUITECTURA ",
"POSTITULO SUPERIOR",
"ESPECIALIDAD",
"SECTOR",
"ESTADO",
"INSTITUCIÓN",
"CARGO",
]

var_count = "Ex-Alumnos"

# Configuración de la página
st.set_page_config(
    page_title = APP_TITLE, 
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Styles
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 280px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Funciones
@st.cache_data
def read_csv(csv_path):
    df = pd.read_csv(csv_path)
    return df 

@st.cache_data
def csv2gdf(csv_path):
    df = pd.read_csv(csv_path)
    df = df[df['Coordenadas'].notna()]
    df[['Latitude', 'Longitude']] = df['Coordenadas'].str.split(',', expand=True)
    # Convertir las columnas de latitud y longitud a float
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    gdf_file = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude))
    return gdf_file

def read_geojson(geojson_path):
    gpd_file = gpd.read_file(geojson_path)
    return(gpd_file)

@st.cache_data
def read_and_count(geojson_path, csv_path, name_count = "Cantidad"):
    gdf_polygons = read_geojson(geojson_path)
    gdf_points = csv2gdf(csv_path)
    gdf_end = count_points_in_polygons(gdf_points, gdf_polygons, col_name = name_count)
    return gdf_end


def select_col(data_frame, column_names):
    """
    Selecciona columnas específicas de un DataFrame o GeoDataFrame.

    Args:
    data_frame (pd.DataFrame or gpd.GeoDataFrame): El DataFrame del cual seleccionar columnas.
    column_names (list): Una lista de nombres de columnas para seleccionar.

    Returns:
    pd.DataFrame or gpd.GeoDataFrame: Un nuevo DataFrame con solo las columnas seleccionadas.
    """
    # Verificar si es un GeoDataFrame y si contiene la columna de geometría
    is_geodf = isinstance(data_frame, gpd.GeoDataFrame)
    geometry_column = data_frame.geometry.name if is_geodf else None

    # Seleccionar las columnas y retornar el nuevo DataFrame o GeoDataFrame
    try:
        selected_columns = data_frame[column_names]
        if is_geodf:
            # Si es un GeoDataFrame, asegurarse de que la columna de geometría se preserve
            if geometry_column in column_names:
                return gpd.GeoDataFrame(selected_columns, geometry=geometry_column)
            else:
                return gpd.GeoDataFrame(selected_columns)
        return selected_columns
    except KeyError as e:
        # Manejar el error en caso de que alguna columna no exista en el DataFrame
        print(f"Error: Una o más columnas no existen en el DataFrame. {e}")
        return None  # O podrías retornar un DataFrame vacío dependiendo de tu caso de uso

def count_points_in_polygons(points_gdf, polygons_gdf, col_name = "Cantidad"):
    """
    Agrega una columna a un GeoDataFrame de polígonos que cuenta cuántos puntos están contenidos en cada polígono.

    Args:
    points_gdf (gpd.GeoDataFrame): GeoDataFrame de puntos.
    polygons_gdf (gpd.GeoDataFrame): GeoDataFrame de polígonos.

    Returns:
    gpd.GeoDataFrame: GeoDataFrame de polígonos con una nueva columna que muestra el recuento de puntos dentro de cada polígono.
    """
    # Inicializar la columna de conteo en el GeoDataFrame de polígonos
    polygons_gdf[col_name] = 0

    # Para cada polígono, contar los puntos que caen dentro de él
    for index, polygon in polygons_gdf.iterrows():
        # Utiliza el método within de GeoPandas para comprobar si los puntos están dentro del polígono
        points_in_polygon = points_gdf.within(polygon['geometry'])
        # Sumar el total de puntos dentro del polígono
        polygons_gdf.at[index, col_name] = points_in_polygon.sum()

    return polygons_gdf

def add_attributes_to_points(points_gdf, polygons_gdf):
    """
    Asigna los atributos de los polígonos a los puntos contenidos dentro de ellos.

    Args:
    points_gdf (gpd.GeoDataFrame): GeoDataFrame de puntos.
    polygons_gdf (gpd.GeoDataFrame): GeoDataFrame de polígonos.

    Returns:
    gpd.GeoDataFrame: GeoDataFrame de puntos con los atributos de los polígonos en los que se ubican.
    """
    # Realizar una unión espacial (spatial join) entre puntos y polígonos
    # Esto asignará a cada punto los atributos del polígono en el que se encuentra
    joined_gdf = gpd.sjoin(points_gdf, polygons_gdf, how="left", op="within")

    return joined_gdf


def region_filter(gdf):
    regiones = gdf["NOM_REGION"].unique()
    selected_region =  st.sidebar.selectbox("Selecciona una región", 
      regiones, index = 6)
    # st.header(f'Región: {selected_region}')
    return selected_region

def com_filter(gdf_reg, selected_region):      
    comunas_region = gdf_reg[gdf_reg["NOM_REGION"] == selected_region]["NOM_COMUNA"].unique()
    com_options = ["Todas"] + list(comunas_region)
    selected_comuna = st.sidebar.selectbox("Selecciona una comuna", com_options)
    # st.header(f'Comuna: {selected_comuna}')
    return selected_comuna
  
def selection_com(reg_selected, com_selected, df_com, df_zon):
    # Filtrar los datos según la selección
    if com_selected == "Todas":
        filtered_gdf = df_com[df_com["NOM_REGION"] == reg_selected]
    else: filtered_gdf = df_zon[df_zon["NOM_COMUNA"] == com_selected] 
    return filtered_gdf 

def point2tab(points_gdf, polygons_gdf, com_selected, col_names):
    # Asegúrate de que ambos GeoDataFrame tengan la misma proyección
    if points_gdf.crs is None:
        points_gdf.set_crs('epsg:4326', inplace=True)    
    points_gdf = points_gdf.to_crs(polygons_gdf.crs)
    
    # Agregar atributos del polígono a los puntos
    df_table = add_attributes_to_points(points_gdf, polygons_gdf)
    
    # Filtrar por la comuna seleccionada si no es "Todas"
    if com_selected != "Todas":
        table = df_table[df_table["NOM_COMUNA"] == com_selected]
    else:
        table = df_table  

    # Insertar "NOM_COMUNA" al principio de la lista de nombres de columnas
    col_names.insert(0, "NOM_COMUNA")
    
    # Seleccionar las columnas especificadas
    table = table[col_names]
    
    # Eliminar duplicados
    table = table.drop_duplicates()

    return table

# Calcular un nivel de zoom aproximado basado en el tamaño del bounding box 
def calculate_zoom_level(bbox): 
    max_dim = max(bbox[2] - bbox[0], bbox[3] - bbox[1]) 
    val_zoom = (8 - np.log(max_dim)).round() 
    return val_zoom 

def add_ranInt(gdf, name_col): 
    gdf[name_col] = np.random.randint(1, 101, size=len(gdf)) 
    return gdf 

def add_unique_id(gdf, id_col='id'): 
    gdf[id_col] = range(1, len(gdf) + 1) 
    gdf[id_col] = gdf[id_col].astype(str) 
    return gdf

def gdf_to_geojson_with_str_id(gdf, id_col='id'):
    if gdf[id_col].dtype != 'O':
        gdf[id_col] = gdf[id_col].astype(str)
    return gdf.to_json()


def display_map(gdf_filtered, var_col):
    df = gdf_filtered.copy() 
    
    bbox = gdf_filtered.total_bounds
    center_lat = (bbox[1] + bbox[3]) / 2
    center_lon = (bbox[0] + bbox[2]) / 2
    
    zoom_level = calculate_zoom_level(bbox)

    utalmap = folium.Map(location=[center_lat, center_lon], 
          zoom_start=zoom_level, scrollWheelZoom=True, 
          tiles='CartoDB Dark Matter')
          
    folium.Choropleth(
        geo_data=gdf_filtered,
        name="geometry",
        data=gdf_filtered,
        columns=['id', var_col],
        key_on="feature.properties.id",
        fill_color='YlGnBu',
        fill_opacity=0.8,
        line_opacity=0.2,
        legend_name='Cantidad Ex-Alumnos',
        reset = True,
    ).add_to(utalmap)

    st_map = st_folium(utalmap, width=600, height=300)
    return st_map


def express_mapbox(gdf_filtered, var_col):
    df = gdf_filtered.copy() 
    df = df.set_index('id')
    
    bbox = gdf_filtered.total_bounds
    center_lat = (bbox[1] + bbox[3]) / 2
    center_lon = (bbox[0] + bbox[2]) / 2
    
    zoom_level = calculate_zoom_level(bbox)

    #https://plotly.com/python/mapbox-county-choropleth/
    #https://plotly.github.io/plotly.py-docs/generated/plotly.express.choropleth_mapbox.html
    fig = px.choropleth_mapbox(df, geojson=df.geometry, locations=df.index, 
                               color=var_col, 
                               #featureidkey='properties.id',
                               hover_data={"NOM_COMUNA": True},
                               center={"lat": center_lat, "lon": center_lon},
                               mapbox_style="carto-darkmatter",
                               zoom=zoom_level,
                               opacity=0.7,
                               color_continuous_scale="Viridis"
                               #projection="mercator"
                               )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, 
                      legend=dict(yanchor="top", y=0.9, xanchor="left", x=0.4))

    st_map = st.plotly_chart(fig, width= 500, height=300)
    return st_map 



def express_map(gdf_filtered, var_col):
    df = gdf_filtered.copy() 
    df = df.set_index('id')
    fig = px.choropleth(df, geojson=df.geometry, locations=df.index, 
                        color=var_col, color_continuous_scale="Viridis",
                        projection="mercator")
    fig.update_geos(fitbounds="locations", visible=False)
    st_map = st.plotly_chart(fig)
    return st_map

def table_info(df, drop_cols, h = 200, name_col = "Cantidad"):
    df_new = df.drop(columns=drop_cols, errors='ignore').reset_index(drop=True)
    df_new = df_new.sort_values(name_col, ascending=False)
    gb = GridOptionsBuilder.from_dataframe(df_new)
    gb.configure_default_column(enablePivot=True, enableValue=True, 
                                enableRowGroup=True, editable=True, filter=True)
    gb.configure_grid_options(domLayout='normal', autoSizeAllColumns=True)
    gridOptions = gb.build()
    ag_df = AgGrid(df_new, theme = "streamlit", height = h,
                   fit_columns_on_grid_load=False,
                   gridOptions=gridOptions, enable_enterprice_modules= True)
#    st_df = st.dataframe(df_display,
#            use_container_width = True,
#            hide_index=True,
#            width=None,
#            height = h)
    return ag_df
  
def tab_bars(df_com, reg_selected, cols_2):
    df_display = df_com[df_com["NOM_REGION"] == reg_selected]
    df_display = df_display.drop(columns="geometry", errors='ignore').reset_index(drop=True)
    df_display = df_display.sort_values(cols_2[1], ascending=False)
    
    st_tab_bar = st.dataframe(df_display, 
                  column_order=(cols_2),
                  hide_index=True,
                  width=250,
                  # use_container_width = True, 
                  column_config={
                    cols_2[0]: st.column_config.TextColumn(
                      "Comunas",
                       width = "small", 
                      ),
                      cols_2[1]: st.column_config.ProgressColumn(
                        "Ex-Alumnos",
                        format="%f",
                        min_value=0,
                        width = "small", 
                        max_value=max(df_display[cols_2[1]],
                        ),
                      )}
                  )
    return st_tab_bar
    
def get_max_com(df_com, reg_selected,  vals_col = "Cantidad", id_col = "NOM_COMUNA"):
    df_display = df_com[df_com["NOM_REGION"] == reg_selected]
    df_display = df_display.drop(columns="geometry", errors='ignore').reset_index(drop=True)
    df_display = df_display.sort_values(vals_col, ascending=False)
    df = df_display[[id_col, vals_col]]
    com_1 = df.iloc[0]
    com_2 = df.iloc[1]
    resto = df.iloc[2:].sum()
    suma_cant = df[vals_col].sum()
    com_1_name = [com_1[id_col], com_1[vals_col], (com_1[vals_col]/suma_cant)*100]
    com_2_name = [com_2[id_col], com_2[vals_col],  (com_2[vals_col]/suma_cant)*100]
    resto_name = ["Resto Comunas", resto[vals_col].sum(),  (resto[vals_col]/suma_cant)*100]
    st_metric_1 = make_metrics(com_1_name)
    st_metric_2 = make_metrics(com_2_name)
    st_metric_3 = make_metrics(resto_name)
    return st_metric_1, st_metric_2, st_metric_3

def make_metrics(list_val):
    nom_com = str(list_val[0])
    n_com = str(list_val[1]) + " p."
    n_perc = str(round(list_val[2], 2)) + " %"
    st_metric = st.metric(nom_com, n_com, n_perc)
    return st_metric

def get_max_reg(df_com, reg_selected,  vals_col = "Cantidad"):
    df_reg = df_com[df_com["NOM_REGION"] == reg_selected]
    max_reg = df_reg[vals_col].sum()
    max_nac = df_com[vals_col].sum()
    percent = round((max_reg / max_nac)*100, 1)
    return percent

# Donut chart
def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']
    
  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })
    
  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)
    
  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=25, fontWeight=700,
                        fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text


# Configuración de página

def main():
    # st.title(APP_TITLE)
    
    st.sidebar.title('Selección Territorial')
    st.sidebar.caption(APP_SUB_TITLE)
    
    # Load Data
    gdf_comunas = read_and_count(geojson_path = name_comunas, 
                                 csv_path = path_csv, 
                                 name_count = "Cantidad")
    gdf_zonas = read_and_count(geojson_path = name_zonas, 
                               csv_path = path_csv, 
                               name_count = "Cantidad")
    
    # Simulate data
#    gdf_comunas = add_ranInt(gdf_comunas, name_col = "Cantidad")
#    gdf_zonas = add_ranInt(gdf_zonas, name_col = "Cantidad")

    
    #Display Filters and Map
    reg_selected = region_filter(gdf_comunas)
    com_selected = com_filter(gdf_comunas, selected_region = reg_selected)
    gdf_filtered = selection_com(reg_selected = reg_selected, 
            com_selected = com_selected, 
            df_com = gdf_comunas, 
            df_zon = gdf_zonas)
    # id será reemplzado por el nombre zona
    gdf_filtered = add_unique_id(gdf_filtered)
    
    gdf_points_raw = csv2gdf(path_csv)
#    gdf_filtered = count_points_in_polygons(gdf_points_raw, gdf_filtered)


    df_table = point2tab(points_gdf = gdf_points_raw, 
                         polygons_gdf = gdf_filtered, 
                         com_selected = com_selected,
                         col_names = col_names)
    
    #Display Metrics
    st.caption(f'Region: {reg_selected}, Comuna: {com_selected}')
    
    col1, col2, col3 = st.columns((1, 5, 2), gap = "medium")
    with col1:
        st.markdown("**Datos**")
        data1, data2, data3 = get_max_com(df_com= gdf_comunas, reg_selected = reg_selected,
                                          vals_col = "Cantidad", id_col = "NOM_COMUNA")

        st.write("% Regional")
        percent_reg = get_max_reg(df_com= gdf_comunas, reg_selected = reg_selected,
                                  vals_col = "Cantidad") 
        donut_chart_greater = make_donut(percent_reg, 'Respecto al País', 'blue')
        st.altair_chart(donut_chart_greater)
 

    with col2:
        st.markdown("**Mapas**")
       # st_map = display_map(gdf_filtered = gdf_filtered, var_col = "Cantidad")
        st_map = express_mapbox(gdf_filtered = gdf_filtered, var_col = "Cantidad")

        st.markdown("**Tabla de Datos**")
        tab = table_info(df = df_table, drop_cols = drop_cols, name_col = "NOM_COMUNA")
        
   
    with col3:
      st.markdown("**Informaciones**")
      tabBar = tab_bars(df_com = gdf_comunas, reg_selected = reg_selected, 
                        cols_2 = ["NOM_COMUNA", "Cantidad"])

      with st.expander('About', expanded=True):
          st.write('''
              - [:blue[**Esc. de Arquitectura UTAL**]](http://www.arquitectura.utalca.cl/)
              - [:blue[**Diagrama Miro**]](https://miro.com/app/board/uXjVNDBK62g=/).
              ''')


if __name__ == "__main__":
    main()

