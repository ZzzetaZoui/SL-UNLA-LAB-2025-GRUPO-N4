from fastapi import FastAPI, HTTPException, status, Query
from datetime import date, datetime, timedelta, time
from fastapi.responses import JSONResponse
from starlette.requests import Request
from typing import List
from schemas import Usuario, Login, PersonaIn, PersonaOut, TurnoIn, TurnoOut, Estado, EstadoTurno
from crud import USUARIOS, PERSONAS, TURNOS, buscar_usuario_por_email, crear_persona, listar_personas, obtener_persona, demasiados_cancelados, calcular_edad

app = FastAPI()

@app.exception_handler(Exception)
async def generic_500_handler(request: Request, e: Exception):
    return JSONResponse( status_code=500, content={"detail": "Error interno del servidor", "error": str(e)})

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

@app.get("/personas/{pid}", response_model=PersonaOut)
def personas_get(pid: int):
    p = obtener_persona(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

@app.put("/personas/{pid}", response_model=PersonaOut)
def personas_update(pid: int, body: PersonaIn):
    p = obtener_persona(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    actualizado = p.copy(update=body.dict())
    PERSONAS[PERSONAS.index(p)] = actualizado
    return actualizado

@app.delete("/personas/{pid}", status_code=204)
def personas_delete(pid: int):
    p = obtener_persona(pid)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    PERSONAS.remove(p)

_next_tid = 1  

@app.post("/turnos", response_model=TurnoOut, status_code=201)
def crear_turno(turno: TurnoIn):
    global _next_tid

    persona = obtener_persona(turno.persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    if not persona.activo:
        raise HTTPException(status_code=400, detail="La persona no está habilitada para sacar turno")

    if not (time(9, 0) <= turno.hora <= time(17, 0)):
        raise HTTPException(status_code=400, detail="Hora fuera de rango permitido (09:00-17:00)")
    if turno.hora.minute not in [0, 30]:
        raise HTTPException(status_code=400, detail="La hora debe ser múltiplo de 30 minutos")

    if demasiados_cancelados(turno.persona_id, turno.fecha):
        raise HTTPException(
            status_code=400,
            detail="La persona tiene 5 o más turnos cancelados en los últimos 6 meses"
        )
    
    for t in TURNOS:
        if t.fecha == turno.fecha and t.hora == turno.hora and t.estado != EstadoTurno.cancelado:
            raise HTTPException(status_code=400, detail="Turno ocupado")


    nuevo_turno = TurnoOut(
        id=_next_tid,
        fecha=turno.fecha,
        hora=turno.hora.strftime("%H:%M"),
        persona_id=turno.persona_id,
        estado=turno.estado
    )
    _next_tid += 1
    TURNOS.append(nuevo_turno)
    return nuevo_turno

@app.get("/turnos", response_model=List[TurnoOut])
def turnos_list():
    return TURNOS

@app.get("/turnos/{tid}", response_model=TurnoOut)
def obtener_turno(tid: int):
    t = next((t for t in TURNOS if t.id == tid), None)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t

@app.put("/turnos/{tid}", response_model=TurnoOut)
def actualizar_turno(tid: int, data: TurnoIn):
    t = next((t for t in TURNOS if t.id == tid), None)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    # Validaciones como en crear_turno
    persona = obtener_persona(data.persona_id)
    if not persona or not persona.activo:
        raise HTTPException(status_code=400, detail="Persona inválida o no habilitada")
    if not (time(9, 0) <= data.hora <= time(17, 0)) or data.hora.minute not in [0, 30]:
        raise HTTPException(status_code=400, detail="Hora inválida")
    if demasiados_cancelados(data.persona_id, data.fecha):
        raise HTTPException(status_code=400, detail="La persona tiene 5 o más turnos cancelados")

    t.fecha = data.fecha
    t.hora = data.hora.strftime("%H:%M")
    t.persona_id = data.persona_id
    t.estado = data.estado
    return t

@app.delete("/turnos/{tid}", status_code=204)
def eliminar_turno(tid: int):
    t = next((t for t in TURNOS if t.id == tid), None)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    TURNOS.remove(t)

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
    cancelados = {t.hora for t in turnos_dia if t.estado == EstadoTurno.cancelado}
    ocupados = {t.hora for t in turnos_dia if t.estado != EstadoTurno.cancelado}

    return [
        Estado(
            hora=h.strftime("%H:%M"),
            disponible=(h not in ocupados and h not in cancelados)
        )
        for h in horarios
    ]
