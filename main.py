import requests
from classes.Inegi import Inegi, Indicadores, Establecimiento, Establecimientos
from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv('TOKEN_INEGI')
token_indicadores = os.getenv('TOKEN_INDICADORES')

termino = 'gasolina'
lat = 21.361904
lon = -101.920412
radio = 3000

inegi = Inegi(token)

# gasolineras = inegi.buscar(termino, lat, lon, radio)

indicadores = Indicadores(token_indicadores)

consulta = f"/6207048973/es/0700/false/BISE/2.0/{token}?type=json"
consulta_salamanca = f"/6207048973/es/070000110020/false/BISE/2.0/{token}?type=json"

response = indicadores.custom(consulta_salamanca)

observations = response[0]['OBSERVATIONS']
for observation in observations:
    print(observation['TIME_PERIOD'], observation['OBS_VALUE'])