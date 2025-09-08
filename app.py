from fastapi import FastAPI, status, HTTPException
from datetime import date, datetime
from pydantic import BaseModel, EmailStr

app = FastAPI()

#PARA BUSCAR ESTO TENEMOS QUE PONER EL PUERTO+"/equipo" en este caso
#ESTE ES UN EJEMPLO PARA VERIFICAR QUE SIRVE 
@app.get("/equipo")
def equipo():
    return "Somos el mejor equipo del mundo"

#DEFINO PRIMERO USUARIOS
class Usuario:
    def __init__(self, email: str, password: str, telefono: int, nombre: str, apellido: str, dni: int, fechaNacimiento: date):
        self.email = email
        self.password = password
        self.telefono = telefono
        self.nombre = nombre
        self.apellido = apellido
        self.dni = dni
        self.fechaNacimiento = fechaNacimiento


#ACA SE VA A GENERAR LISTA DE USUARIO
USUARIOS=[]

#TENDREMOS QUE HACER YN ERIFICADOR DE QUE EL EMAIL ESTE CORRECTO Y NO REPETIDO EN LOS DATOS

#BUSCAR USUARIO POR EMAIL ES LA UNICA MANERA QUE SEA DIFERENTE
def buscar_usuario_por_email(email: str):
    for i in USUARIOS:
        if i.email == email:
            return i
    return None

#REGISTRAR USUARIO

class UsuarioIn(BaseModel):
    email: EmailStr
    password: str
    telefono: int
    nombre: str
    apellido: str
    dni: int
    fechaNacimiento: date

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(usuario: UsuarioIn):
    #verifico si ya existe
    if buscar_usuario_por_email(usuario.email):
        raise HTTPException(status_code=400, detail="El mail ya esta registrado")
    
    nuevo = Usuario(**usuario.dict()) #Esto despues lo tengo que chequear :P
    USUARIOS.append(nuevo)

    return {"mensaje": "Usuario registrado con exito"}



#APARTADO DE LOGIN (Despues lo armo, toy estudiando arquitectura jsjsjs. Atte: Nico)

#APARTADO PARA CORROBORAR SI ESTAMOS HABILITADOS PARA OBTENER UN TURNO