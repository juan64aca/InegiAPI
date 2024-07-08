from classes.Inegi import Inegi


token = '561f8f3c-d809-4df5-8772-65e65c1a7257'

inegi = Inegi(token)

lat = '19.424536'
lon = '-99.173900'

respuesta = inegi.buscar_todo(lat, lon, radio=3)

print(respuesta.json())

