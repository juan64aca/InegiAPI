import numpy as np
import webbrowser
import requests
import pandas as pd
import folium


class Indicadores:
    def __init__(self, token):
        self.token = token
        self.url = 'https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR'

    def custom(self, consulta: str):
        consulta = consulta.format(token=self.token)
        url = self.url + consulta
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            result = result.get('Series')
            return result
        else:
            print(f"Fallo en la busqueda: {response.status_code} - {response.text}")


class Inegi:
    def __init__(self, token):
        self.token = token
        self.url = 'https://www.inegi.org.mx/app/api/denue/v1/consulta'

    def buscar(self, nombre: str, latitud, longitud, radio: int):
        if radio > 5000:
            raise Exception("La distancia excede el límite de 5,000 metros.")

        endpoint = f"/Buscar/{nombre}/{latitud},{longitud}/{radio}/{self.token}"
        url = self.url + endpoint
        response = requests.get(url)

        if response.status_code == 200:
            establecimientos = response.json()
            establecimientos = [Establecimiento(establecimiento) for establecimiento in establecimientos]
            establecimientos = Establecimientos(establecimientos)
            return establecimientos

        else:
            print(f"Fallo en la busqueda: {response.status_code} - {response.text}")

    def buscar_todo(self, latitud, longitud, radio: int):
        if radio > 5000:
            raise Exception("La distancia excede el límite de 5,000 metros.")

        endpoint = f"/Buscar/todos/{latitud},{longitud}/{radio}/{self.token}"
        url = self.url + endpoint
        response = requests.get(url)

        if response.status_code == 200:
            establecimientos = response.json()
            establecimientos = [Establecimiento(establecimiento) for establecimiento in establecimientos]
            establecimientos = Establecimientos(establecimientos)
            return establecimientos
        else:
            print(f"Fallo en la busqueda: {response.status_code} - {response.text}")


class Establecimiento:
    def __init__(self, data: dict):
        self.data = data
        self.clee = data.get('CLEE')
        self.id = data.get('Id')
        self.nombre = data.get('Nombre')
        self.razon_social = data.get('Razon_social')
        self.clase_actividad = data.get('Clase_actividad')
        self.estrato = data.get('Estrato')
        self.tipo_vialidad = data.get('Tipo_vialidad')
        self.calle = data.get('Calle')
        self.num_exterior = data.get('Num_Exterior')
        self.num_interior = data.get('Num_Interior')
        self.colonia = data.get('Colonia')
        self.cp = data.get('CP')
        self.ubicacion = data.get('Ubicacion')
        self.telefono = data.get('Telefono')
        self.correo_e = data.get('Correo_e')
        self.sitio_internet = data.get('Sitio_internet')
        self.tipo = data.get('Tipo')
        self.longitud = float(data.get('Longitud'))
        self.latitud = float(data.get('Latitud'))
        self.centro_comercial = data.get('CentroComercial')
        self.tipo_centro_comercial = data.get('TipoCentroComercial')
        self.num_local = data.get('NumLocal')

    def mapear(self, zoom: int = 15):
        m = folium.Map(
            location=[self.latitud, self.longitud],
            zoom_start=zoom,
            tiles='cartodb positron'
        )
        folium.Marker(
            [self.latitud, self.longitud],
            popup=self.razon_social,
            tooltip=self.nombre
        ).add_to(m)
        file = 'map.html'
        m.save(file)
        webbrowser.open(file)

        return True


class Establecimientos:
    def __init__(self, establecimientos: list[Establecimiento]):
        self.data = establecimientos

    def mapear(self, zoom: int = 15):
        latitudes = [establecimiento.latitud for establecimiento in self.data]
        longitudes = [establecimiento.longitud for establecimiento in self.data]

        latitud = np.mean(latitudes)
        longitud = np.mean(longitudes)

        m = folium.Map(
            location=[latitud, longitud],
            zoom_start=zoom,
            tiles='cartodb positron'
        )

        for establecimiento in self.data:
            folium.Marker(
                [establecimiento.latitud, establecimiento.longitud],
                popup=establecimiento.razon_social,
                tooltip=establecimiento.nombre
            ).add_to(m)

        file = 'map.html'
        m.save(file)
        webbrowser.open(file)

        return True
