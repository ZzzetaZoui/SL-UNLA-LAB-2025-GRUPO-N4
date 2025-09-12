from fastapi import FastAPI, status, HTTPException
from datetime import date, datetime
from pydantic import BaseModel, EmailStr
from models import Usuario, Login, USUARIOS, buscar_usuario_por_email, registrar_usuario
from fastapi.responses import JSONResponse
from starlette.requests import Request

app = FastAPI()

#PARA BUSCAR ESTO TENEMOS QUE PONER EL PUERTO+"/equipo" en este caso
#ESTE ES UN EJEMPLO PARA VERIFICAR QUE SIRVE 
@app.get("/equipo")
def equipo():
    return "Somos el mejor equipo del mundo"


#Incluirá para errores genericos, para poder encapsular si el 400 u otro fallara. atte:ZOE
#También modifique que los models se trasladen a models.py para mayor organizacion y que
#se visualice más ordenado
@app.exception_handler(Exception)
async def generic_500_handler(request: Request, e: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "error": str(e)},
    )


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(usuario: Usuario):
    #verifico si ya existe
    if buscar_usuario_por_email(usuario.email):
        raise HTTPException(status_code=400, detail="El mail ya esta registrado")
    
    nuevo = Usuario(**usuario.dict()) #Esto despues lo tengo que chequear :P
    USUARIOS.append(nuevo)

    return {"mensaje": "Usuario registrado con exito"}

@app.post("/login")
def login(data: Login):
    usuario = buscar_usuario_por_email(data.email)
    if not usuario or usuario.password != data.password:
        raise HTTPException(status_code=401, detail="Datos erroneos")
    
    return {"mensaje": f"Bienvenido {usuario.nombre}"}


#Ordene un poco las files y organicé algunas cosas ATTE: Nico

#APARTADO PARA CORROBORAR SI ESTAMOS HABILITADOS PARA OBTENER UN TURNO