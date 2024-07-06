import geopandas as gpd

# Cargar el archivo GeoJSON
gdf = gpd.read_file("data/INE/zonas_nac_old.geojson")

# Simplificar la geometría
gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.0001, preserve_topology=True)

# Guardar el archivo simplificado
gdf.to_file("data/INE/zonas_nac.geojson", driver='GeoJSON')
