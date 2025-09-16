from fastapi import FastAPI, HTTPException, status, Query
from datetime import date, datetime, timedelta, time
from fastapi.responses import JSONResponse
from starlette.requests import Request
from typing import List

from schemas import Usuario, Login, PersonaIn, PersonaOut, TurnoIn, TurnoOut, Estado
from crud import (
    USUARIOS, buscar_usuario_por_email, crear_persona, listar_personas,
    obtener_persona, modificar_persona, eliminar_persona,
    calcular_edad, TURNOS
)

app = FastAPI()

@app.exception_handler(Exception)
async def generic_500_handler(request: Request, e: Exception):
    return JSONResponse(status_code=500,
                        content={"detail": "Error interno del servidor",
                                 "error": str(e)})

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(usuario: Usuario):
    if buscar_usuario_por_email(usuario.email):
        raise HTTPException(status_code=400, detail="El mail ya está registrado")
    USUARIOS.append(usuario)
    return {"mensaje": "Usuario registrado con éxito"}

@app.post("/login")
def login(data: Login):
    u = buscar_usuario_por_email(data.email)
    if not u or u.password != data.password:
        raise HTTPException(status_code=401, detail="Datos erróneos")
    return {"mensaje": f"Bienvenido {u.nombre}"}

@app.get("/personas", response_model=List[PersonaOut])
def personas_list():
    return listar_personas()

@app.post("/personas", response_model=PersonaOut, status_code=201)
def personas_create(body: PersonaIn):
    if calcular_edad(body.fecha_nacimiento) < 18:
        raise HTTPException(status_code=400, detail="Debe ser mayor de 18 años")
    return crear_persona(body)

# ...resto de endpoints para modificar/eliminar etc.

# --- Turnos ---
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

@app.get("/turnos-disponibles", response_model=List[Estado])
def turnos_disponibles(fecha: date = Query(...)):
    inicio, fin = time(9, 0), time(17, 0)
    delta = timedelta(minutes=30)
    actual = datetime.combine(fecha, inicio)
    fin_dt = datetime.combine(fecha, fin)

    horarios = []
    while actual <= fin_dt:
        horarios.append(actual.time())
        actual += delta

    turnos_dia = [t for t in TURNOS if t.fecha == fecha]
    cancelados = {t.hora for t in turnos_dia if getattr(t, "estado", "") == "cancelado"}
    ocupados = {t.hora for t in turnos_dia if getattr(t, "estado", "") != "cancelado"}

    return [
        Estado(
            hora=h.strftime("%H:%M"),
            disponible=(h not in ocupados and h not in cancelados)
        )
        for h in horarios
    ]