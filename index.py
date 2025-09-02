from fastapi import FastAPI

app = FastAPI()

#PARA BUSCAR ESTO TENEMOS QUE PONER EL PUERTO+"/equipo" en este caso
#ESTE ES UN EJEMPLO PARA VERIFICAR QUE SIRVE 
@app.get("/equipo")
def equipo():
    return "Somos el mejor equipo del mundo"

#DEFINO PRIMERO USUARIOS
class Usuario:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password


#ACA SE VA A GENERAR LISTA DE USUARIO
USUARIOS=[]

#TENDREMOS QUE HACER YN ERIFICADOR DE QUE EL EMAIL ESTE CORRECTO Y NO REPETIDO EN LOS DATOS

#BUSCAR USUARIO POR EMAIL ES LA UNICA MANERA QUE SEA DIFERENTE
def buscar_usuario_por_email(email: str):
    for i in USUARIOS:
        if i.email == email:
            return i
    return None

#ACA SE VA A GENERAR LISTA DE USUARIO
#APARTADO PARA REGISTER

#APARTADO DE LOGIN

#APARTADO PARA CORROBORAR SI ESTAMOS HABILITADOS PARA OBTENER UN TURNO