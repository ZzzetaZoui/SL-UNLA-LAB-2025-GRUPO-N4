from fastapi import FastAPI, status, HTTPException, Query
from datetime import date, datetime, timedelta, time
from pydantic import BaseModel, EmailStr
from models import (
    Usuario, Login, USUARIOS, buscar_usuario_por_email,
    PersonaIn, PersonaOut, listar_personas, obtener_persona,
    crear_persona, modificar_persona, eliminar_persona, calcular_edad, TurnoIn,
    TurnoOut, TURNOS, estado, PERSONAS)
from typing import List
from fastapi.responses import JSONResponse
from starlette.requests import Request

app = FastAPI()

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
    if buscar_usuario_por_email(usuario.email):
        raise HTTPException(status_code=400, detail="El mail ya esta registrado")
    
    nuevo = Usuario(**usuario.model_dump())
    USUARIOS.append(nuevo)
    return {"mensaje": "Usuario registrado con exito"}

@app.post("/login")
def login(data: Login):
    usuario = buscar_usuario_por_email(data.email)
    if not usuario or usuario.password != data.password:
        raise HTTPException(status_code=401, detail="Datos erroneos")
    
    return {"mensaje": f"Bienvenido {usuario.nombre}"}

@app.get("/usuarios")
def listar_usuarios():
    return USUARIOS

#si queremos buscar por mail
@app.get("/usuarios/{email}")
def obtener_usuario_por_email(email: str):
    u = buscar_usuario_por_email(email)
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return u

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

@app.delete("/personas/{pid}", status_code=status.HTTP_200_OK)
def personas_delete(pid: int):
    if not eliminar_persona(pid):
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return {"mensaje": f"Persona con ID {pid} eliminada"}

#SIRVE PARA ELIMINAR LA PERSONA
@app.delete("/personas", status_code=status.HTTP_200_OK)
def eliminar_todas_personas():
    PERSONAS.clear()
    return {"mensaje": "Todas las personas fueron eliminadas"}

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
    return TurnoOut(
        fecha=turno.fecha,
        hora=turno.hora.strftime("%H:%M"),
        persona_id=turno.persona_id
    )

#PARA LISTAR EL TURNO
@app.get("/turnos", response_model=List[TurnoOut])
def listar_turnos():
    return [
        TurnoOut(
            fecha=t.fecha,
            hora=t.hora.strftime("%H:%M"),
            persona_id=t.persona_id
        )
        for t in TURNOS
    ]

# PARA CANCELAR TURNO
@app.put("/turnos/cancelar")
def cancelar_turno(fecha: date, hora: str):
    for t in TURNOS:
        if t.fecha == fecha and t.hora.strftime("%H:%M") == hora:
            setattr(t, "estado", "cancelado")
            return {"mensaje": f"Turno de {hora} en {fecha} cancelado"}
    raise HTTPException(status_code=404, detail="Turno no encontrado")


@app.get("/turnos-disponibles", response_model=List[estado])
def turnos_disponibles(fecha: date = Query(..., description="Fecha para consultar turnos")):
    inicio = time(9, 0)
    fin = time(17, 0)
    delta = timedelta(minutes=30)

    horarios = []
    actual = datetime.combine(fecha, inicio)
    fin_datetime = datetime.combine(fecha, fin)

    while actual <= fin_datetime:
        horarios.append(actual.time())
        actual += delta

        #AYUDA A LOS ESTADOS DE LOS TURNOS DE ESE DIA

    turnos_del_dia = [t for t in TURNOS if t.fecha == fecha]

    cancelados = {t.hora for t in turnos_del_dia
                  if getattr(t, "estado", None) == "cancelado"}

    ocupados = {t.hora for t in turnos_del_dia
                if getattr(t, "estado", None) != "cancelado"}
    
    @app.get("/personas/{pid}/edad")
    def edad_persona(pid: int):
        p = obtener_persona(pid)
        if not p:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return {"edad": calcular_edad(p.fecha_nacimiento)}
    

    # SIRVE PARA EL ARMADO DEL JSON SE REFLEJE 
    return [
        estado(
            hora=h.strftime("%H:%M"),
            # disponible = True si NO está ni ocupado ni cancelado
            disponible=(h not in ocupados and h not in cancelados)
        )
        for h in horarios
    ]