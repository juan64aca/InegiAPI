
import os
import pickle
import base64
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email.mime.text import MIMEText

class GoogleSessionYP():
    """Este módulo está diseñado para trabajar con las apis de google, incluidos métodos para 
        enviar correos, subir archivos a drive, leer y escribir sobre las hojas de cálculo de G 
        sheets, etc.    
            
            Importante: tener en cuenta que: Al parecer ya no se estan permitiendo nuevos proyectos en GCP, 
            es necesario colgarse de uno existente dando de alta los usuarios.        """

    def __init__(self, credentials, scopes):
        """Este paquete está considerado para un proyecto de google del desarrollador principal, si necesita
           usar el desarrollo en otro proyecto es necesario modificar scopes y credenciales
           
           Parametros
           ----------
           scopes=list.
                Lisita de strings. Los scopes son los permisos que se dan sobre una cuenta de google y se dande alta al incluir las 
                páginas de internet listadas en: https://developers.google.com/identity/protocols/oauth2/scopes. 
           
           credentials=str.
                Ruta del archivo (json) que contiene las credenciales; tipicamente 'credentials.json'
                Las credenciales es información clave para que la aplicación pueda encontrar el proyecto que se 
                dió de alta. Si se hace alguna modificación en los scopes es necesario borrar el 
                archivo token.pickle.       """
        
        self.scopes=scopes
        self.credentials=credentials
        self.__creds=None
        self.mimeTypeExt={'txt':'text/plain','xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'xlsm':'application/vnd.ms-excel.sheet.macroenabled.12','png':'image/png','csv':'text/csv',
                'pdf':'application/pdf','docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '7z':'application/x-7z-compressed','zip':'application/zip'}
        self.__Authentication()   
        
    def __Authentication(self):
        """El proceso de autenticación es necesario para poder ejecutar cualquier operación con las apis de google.
           
           Parametros
           ----------
           token = str. 
                Si fue necesario hacer cambios en los scopes el nuevo archivo token.pickle se generará de manera 
                automática en la ruta que se haya epecificado para token  
           Returns    
           -------
            0       """
            
        token='./yogaprocess/token.pickle'
        creds = None
        if os.path.exists(token):
            print("Cargando credenciales de token...")
            with open(token, 'rb') as tk:
                creds = pickle.load(tk)
                print("Credenciales cargadas.")
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Las credenciales expiraron, haciendo el request... ")
                creds.refresh(Request())
                print("Terminó el request, se actalizaron las credenciales")
            else:
                print("No hay credenciales, no se encontro el archivo pickle, solicitando aceptacion de los Scopes")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials, self.scopes)
                print("Generando las nuevas credenciales")
                creds = flow.run_local_server(port=0)
            with open(token, 'wb') as tk:
                print("Guardando las credenciales..")
                pickle.dump(creds, tk)
                print("Credenciales guardadas y actualizadas.")
        self.__creds=creds
        return 0

    def GsheetRead(self, book, sheetRange, header=False):
        """Lector de hojas de calculo de gsheets.
           
           Parametros
           ----------
           book = str. 
                Id del libro del que se extraerá la info  
           
           sheetRange = str.
                Nombre de la hoja con rango incluido, si no se especifica el rango se tomara toda la hoja.
                Ejemplo: 'Hoja1!A5:D20'
           header = boolean
                True si deseas la primer linea, false en otro caso.
           Returns    
           -------
                lista de listas.        """
        service = build('sheets', 'v4', credentials=self.__creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=book,range=sheetRange).execute()
        values = result.get('values', [])[0:] 
        if header:
            cols = len(values[0])
        else :
            cols = len(values.pop(0)) #quita la cabecera
        [j.extend(['']*(cols-len(j))) if len(j) < cols else j  for j in values]
        return values 
    
    def GsheetWrite(self, book, sheetRange, values, mode='RAW'):
        """Escritor de hojas de calculo de gsheets.
           
           Parametros
           ----------
           book = str. 
                Id del libro en el que se depositará la info  
           sheetRange = str.
                Nombre de la hoja con rango incluido, si no se especifica el rango se tomara toda la hoja.
                Ejemplo: 'Hoja1!A5:D20'
           values = lista de listas
                ejemplo: values = ['[columna1','columna2','columna3'],['1','2','3'],['4','5','6'],['7','8','9']].
           mode = tipo de escritura en gsheets dos tipos: RAW, USER_ENTERED
           Returns    
           -------
            0       """                
        
        service = build('sheets', 'v4', credentials=self.__creds)
        sheet = service.spreadsheets()
        body = {'values': values} 
        body_clear={}
        result_clear = sheet.values().clear(spreadsheetId=book, 
            range=sheetRange, 
            body=body_clear).execute()
        result = sheet.values().update(spreadsheetId=book, 
            range=sheetRange,valueInputOption=mode, 
            body=body).execute()
        return 0
    
    def clearSheet(self, book, sheetName, borrar_header):
        service = build('sheets', 'v4', credentials=self.__creds)
        sheet = service.spreadsheets()
        
        if borrar_header:
            # Limpiar toda la hoja
            body_clear = {}
            result_clear = sheet.values().clear(spreadsheetId=book, range=sheetName, body=body_clear).execute()
        else:
            # Obtener la cantidad de columnas para mantener el rango de encabezado
            sheet_info = sheet.get(spreadsheetId=book, ranges=sheetName, includeGridData=True).execute()
            num_columns = len(sheet_info['sheets'][0]['data'][0]['rowData'][0]['values'])
            header_range = f"{sheetName}!A2:{chr(64 + num_columns)}"
            
            # Limpiar toda la hoja excepto la primera fila (el encabezado)
            body_clear = {}
            result_clear = sheet.values().clear(spreadsheetId=book, range=header_range, body=body_clear).execute()
        
        return 0
    
    def generadorRango(self,data_final, hoja, celdaInicio='A1'):
        registros = len(data_final)
        columnas = len(data_final[0])
        #Mapeo columnas columnas a letras sheet
        mapeosimple = {num: chr(65 + (num - 1) % 26) for num in range(1, 27)}
        extended_dict = {num: (mapeosimple[(num - 1) // 26] + mapeosimple[(num - 1) % 26 + 1]) if num > 26 else mapeosimple[num] for num in range(1, columnas + 1)}
        #Construccion rango
        rango = hoja + '!'+ celdaInicio + ':' + str(extended_dict[columnas]) + str(registros)
        return rango


class GoogleSessionGmail():
    """Este módulo está diseñado para trabajar con las apis de google, incluidos métodos para 
        enviar correos, subir archivos a drive, leer y escribir sobre las hojas de cálculo de G 
        sheets, etc.    
            
            Importante: tener en cuenta que: Al parecer ya no se estan permitiendo nuevos proyectos en GCP, 
            es necesario colgarse de uno existente dando de alta los usuarios.        """

    def __init__(self, credentials, scopes):
        """Este paquete está considerado para un proyecto de google del desarrollador principal, si necesita
           usar el desarrollo en otro proyecto es necesario modificar scopes y credenciales
           
           Parametros
           ----------
           scopes=list.
                Lisita de strings. Los scopes son los permisos que se dan sobre una cuenta de google y se dande alta al incluir las 
                páginas de internet listadas en: https://developers.google.com/identity/protocols/oauth2/scopes. 
           
           credentials=str.
                Ruta del archivo (json) que contiene las credenciales; tipicamente 'credentials.json'
                Las credenciales es información clave para que la aplicación pueda encontrar el proyecto que se 
                dió de alta. Si se hace alguna modificación en los scopes es necesario borrar el 
                archivo token.pickle.       """
        
        self.scopes=scopes
        self.credentials=credentials
        self.__creds=None
        self.mimeTypeExt={'txt':'text/plain','xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'xlsm':'application/vnd.ms-excel.sheet.macroenabled.12','png':'image/png','csv':'text/csv',
                'pdf':'application/pdf','docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '7z':'application/x-7z-compressed','zip':'application/zip'}
        self.__Authentication()
        
        
    def __Authentication(self):
        """El proceso de autenticación es necesario para poder ejecutar cualquier operación con las apis de google.
           
           Parametros
           ----------
           token = str. 
                Si fue necesario hacer cambios en los scopes el nuevo archivo token.pickle se generará de manera 
                automática en la ruta que se haya epecificado para token  
           Returns    
           -------
            0       """
            
        token='token.pickle'
        creds = None
        if os.path.exists(token):
            print("Cargando credenciales de token...")
            with open(token, 'rb') as tk:
                creds = pickle.load(tk)
                print("Credenciales cargadas.")
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Las credenciales expiraron, haciendo el request... ")
                creds.refresh(Request())
                print("Terminó el request, se actalizaron las credenciales")
            else:
                print("No hay credenciales, no se encontro el archivo pickle, solicitando aceptacion de los Scopes")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials, self.scopes)
                print("Generando las nuevas credenciales")
                creds = flow.run_local_server(port=0)
            with open(token, 'wb') as tk:
                print("Guardando las credenciales..")
                pickle.dump(creds, tk)
                print("Credenciales guardadas y actualizadas.")
        self.__creds=creds
        return 0

    def send_html_mail(self, to, subject, body, cc=None, bcc=None):
        try:
            service = build("gmail", "v1", credentials=self.__creds)
            
            message = MIMEText(body, 'html')
            
            # Mail parameters
            message["to"] = to
            if cc:
                message["cc"] = cc
            if bcc:
                message["bcc"] = bcc
            message["subject"] = subject
            
            # encoded message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            create_message = {"raw": encoded_message}
            # pylint: disable=E1101
            send_message = (
                service
                .users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )
            print(f'Message Id: {send_message["id"]}')
        except HttpError as error:
            print(f"An error occurred: {error}")
            send_message = None
      
if __name__ == "__main__":
    print('Falta hacer las pruebas con el modulo doctest')
