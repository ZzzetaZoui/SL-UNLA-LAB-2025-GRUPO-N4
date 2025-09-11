from fastapi import FastAPI, status, HTTPException
from datetime import date, datetime
from pydantic import BaseModel, EmailStr
from models import Usuario, USUARIOS, buscar_usuario_por_email, registrar_usuario

app = FastAPI()

#PARA BUSCAR ESTO TENEMOS QUE PONER EL PUERTO+"/equipo" en este caso
#ESTE ES UN EJEMPLO PARA VERIFICAR QUE SIRVE 
@app.get("/equipo")
def equipo():
    return "Somos el mejor equipo del mundo"

class UsuarioIn(BaseModel):
    email: EmailStr
    password: str
    telefono: int
    nombre: str
    apellido: str
    dni: int
    fechaNacimiento: date

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(usuario: UsuarioIn):
    #verifico si ya existe
    if buscar_usuario_por_email(usuario.email):
        raise HTTPException(status_code=400, detail="El mail ya esta registrado")
    
    nuevo = Usuario(**usuario.dict()) #Esto despues lo tengo que chequear :P
    USUARIOS.append(nuevo)

    return {"mensaje": "Usuario registrado con exito"}

@app.post("/login")
def login(data: LoginIn):
    usuario = buscar_usuario_por_email(data.email)
    if not usuario or usuario.password != data.password:
        raise HTTPException(status_code=401, detail="Datos erroneos")
    
    return {"mensaje": f"Bienvenido {usuario.nombre}"}


#Ordene un poco las files y organicé algunas cosas ATTE: Nico

#APARTADO PARA CORROBORAR SI ESTAMOS HABILITADOS PARA OBTENER UN TURNO