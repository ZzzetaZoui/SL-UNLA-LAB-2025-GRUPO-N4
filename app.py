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

@app.post("/turnos", response_model=TurnoOut, status_code=201) #Wanda modifica esto 
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

@app.get("/turnos/{tid}", response_model=TurnoOut)
def obtener_turno(tid: int):
    if tid < 1 or tid > len(TURNOS):
        raise HTTPException(status_code=404, detail= "Turno no encontrado")
    t = TURNOS[tid - 1]
    return TurnoOut(fecha=t.fecha, hora=t.hora.strftime("%H:%H"), persona_id=t.persona_id)

@app.put("/turnos/{tid}", response_model=TurnoOut)
def actualizar_turno(tid: int):
    if tid < 1 or tid > len(TURNOS):
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    if demasiados_cancelados(data.persona_id, data.fecha):
        raise HTTPException(status_code=400, detail="La persona tiene 5 o mas turnos cancelados en los ultimos 6 meses")
    
    TURNOS[tid - 1] = data
    return TurnoOut(fecha=data.fecha, hora=data.fecha.strftime("%H:%H"), persona_id=data.persona_id) #Esto lo vinculamos con lo que arielingui haga

@app.delete("/turnos/{tid}", response_model=204)
def eliminar_turno(tid: int):
    if tid < 1 or tid > len(TURNOS):
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    TURNOS.pop(tid - 1)



