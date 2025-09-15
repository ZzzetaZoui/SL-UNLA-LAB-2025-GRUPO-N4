from fastapi import FastAPI, status, HTTPException, Query
from datetime import date, datetime, timedelta, date
from pydantic import BaseModel, EmailStr
from models import (
    Usuario, Login, USUARIOS, buscar_usuario_por_email,
    PersonaIn, PersonaOut, listar_personas, obtener_persona,
    crear_persona, modificar_persona, eliminar_persona, TurnoIn,
    TurnoOut, TURNOS)
from typing import List
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

#ABM/CRUD EN APP.PY
@app.get("/personas", response_model=list[PersonaOut])
def personas_list():
    return listar_personas()

@app.get("/personas/{pid}", response_model=PersonaOut)
def personas_get(pid: int):
    p = obtener_persona(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

@app.post("/personas", status_code=status.HTTP_201_CREATED, response_model=PersonaOut)
def personas_create(body: PersonaIn):
    try:
        return crear_persona(body)
    except ValueError as e:
        #AYUDA A SI HAY UN MAIL DUPLICADO
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/personas/{pid}", response_model=PersonaOut)
def personas_put(pid: int, body: PersonaIn):
    try:
        p = modificar_persona(pid, body)
        if not p:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return p
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/personas/{pid}", status_code=status.HTTP_204_NO_CONTENT)
def personas_delete(pid: int):
    if not eliminar_persona(pid):
        raise HTTPException(status_code=404, detail="Persona no encontrada")

def registrar_usuario(u: Usuario) -> Usuario:
    if buscar_usuario_por_email(u.email):
        raise ValueError("El email ya está registrado")
    USUARIOS.append(u)
    return u

@app.post("/turnos", response_model=TurnoOut, status_code=201)
def crear_turno(turno: TurnoIn):
    for t in TURNOS:
        if t.fecha == turno.fecha and t.hora == turno.hora:
            raise HTTPException(status_code=400, detail="Turno ocupado")
        TURNOS.append(turno)
        return TurnoOut(fecha=turno.fecha, hora=turno.hora.strftime("%H:M%"), persona_id=turno.persona_id)


