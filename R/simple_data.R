# Objetivos: simplificar gemetrías
# fecha: 17-05-2024
# autor: denisberreota@gmail.com

# Librerias ---------------------------------------------------------------
library(sf)
library(dplyr)
library(mapview)

# functions ---------------------------------------------------------------
simplify_polygons <-  function(sf_polygon, keep =  0.05){
  pol_simple <- rmapshaper::ms_simplify(sf_polygon, keep = keep)
  return(pol_simple)
}
remove_island <-  function(sf_polygon, min_area = 3e6){
  pol <- rmapshaper::ms_filter_islands(sf_polygon, min_area = min_area)
  return(pol)
}

export_geojson <-  function(sf_polygon, path_out){
  gjson_file <- geojsonio::geojson_json(sf_polygon)
  geojsonio::geojson_write(gjson_file, file = path_out)
}

# Leer archivos -----------------------------------------------------------
comunas <-  st_read("originales/Comunas_Chile.shp") %>% 
  st_transform(4326)

zonas <- st_read("originales/zonas_nacional.shp")%>% 
  st_transform(4326)

# Limpieza comuna ---------------------------------------------------------


# scaremos las islas de la 5 región
# comunas %>% filter(REGION == "05") %>% mapview()
avoid_com <- c("ISLA DE PASCUA", "JUAN FERNÁNDEZ")
r_archipielagos <-  c("11", "12")

comunas_f <- comunas %>% 
  filter(!NOM_COMUNA %in% avoid_com) %>% 
  filter(!REGION %in% r_archipielagos)

comunas_arch <- comunas %>% 
  filter(REGION %in% r_archipielagos) %>% 
  remove_island(min_area = 5e6) %>% 
  simplify_polygons(keep = .4)

# mapview(comunas_arch)
#unir
comunas_all <- comunas_f %>% 
  rbind(comunas_arch) %>% 
  mutate(id = 1:nrow(.)) %>% 
  select(-Shape_Leng, -Shape_Area)
  

# Limpieza Zonas ----------------------------------------------------------
geo_zc_consolidate <- readRDS("originales/geo_zc_consolidate.rds") %>% 
  st_transform(4326) %>% 
  mutate(GEOCODIGO = as.character(COD_INE_16),
         COMUNA = as.character(COMUNA)) %>% 
  select(GEOCODIGO, COMUNA )

data_zonas <- zonas %>% st_drop_geometry() %>% 
  select(1:6) %>% 
  distinct()
geo_zc <- geo_zc_consolidate%>% 
  left_join(data_zonas, by = "COMUNA") %>% 
  filter(!GEOCODIGO %in% data_zonas$GEOCODIGO)

zonas_nac <- zonas %>% 
  select(GEOCODIGO, 1:6) %>% 
  rbind(geo_zc)

zonas_f <- zonas_nac %>% 
  filter(!NOM_COMUNA %in% avoid_com) 

zonas_f <- zonas_f %>% 
  mutate(REGION  = sprintf("%02d", as.numeric(REGION))) %>% 
  mutate(id = 1:nrow(.)) 
  
# Región del Maule --------------------------------------------------------

comunas_maule <- comunas_all %>% 
  filter(REGION == "07")

zonas_maule <- zonas_f %>% 
  filter(REGION == "07")

# guardar geojson ---------------------------------------------------------
export_geojson(comunas_all, path_out = "data/INE/comunas_nac.geojson")
export_geojson(zonas_f, path_out = "data/INE/zonas_nac.geojson")
export_geojson(comunas_maule, path_out = "data/INE/comunas_maule.geojson")
export_geojson(zonas_maule, path_out = "data/INE/zonas_maule.geojson")

