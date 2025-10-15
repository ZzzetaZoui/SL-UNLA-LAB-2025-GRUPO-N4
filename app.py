from fastapi import FastAPI, HTTPException, status, Query, Depends
from datetime import date, time
from typing import List, Optional
from sqlalchemy.orm import Session
import schemas, crud
from database import engine, get_db
from models import Base, ReprogramarTurnoIn, CambiarEstadoTurnoIn

# Crea tablas en SQLite si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ========================= RAÍZ =========================
@app.get("/")
def read_root():
    return {"mensaje": "API funcionando. Usa /docs para probar la API."}

# ========================= HELPERS ======================
def calcular_edad(fecha_nacimiento: date) -> int:
    today = date.today()
    age = today.year - fecha_nacimiento.year - (
        (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )
    return age

# ========================= PERSONAS =====================
@app.post("/personas", response_model=schemas.PersonaOut, status_code=status.HTTP_201_CREATED)
def personas_create(body: schemas.PersonaCreate, db: Session = Depends(get_db)):
    if calcular_edad(body.fecha_nacimiento) < 18:
        raise HTTPException(status_code=400, detail="Debe ser mayor de 18 años")
    return crud.crear_persona(db, body)

@app.get("/personas", response_model=List[schemas.PersonaOut])
def personas_list(db: Session = Depends(get_db)):
    return crud.listar_personas(db)

@app.get("/personas/{persona_id}", response_model=schemas.PersonaOut)
def personas_get(persona_id: int, db: Session = Depends(get_db)):
    p = crud.obtener_persona(db, persona_id)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

@app.put("/personas/{persona_id}", response_model=schemas.PersonaOut)
def personas_update(persona_id: int, body: schemas.PersonaCreate, db: Session = Depends(get_db)):
    p = crud.actualizar_persona(db, persona_id, body)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

@app.delete("/personas/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def personas_delete(persona_id: int, db: Session = Depends(get_db)):
    p = crud.obtener_persona(db, persona_id)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    crud.eliminar_persona(db, persona_id)
    return

# ===== Subrecurso: turnos de una persona =====
@app.get("/personas/{persona_id}/turnos", response_model=List[schemas.TurnoOut])
def turnos_por_persona(persona_id: int, db: Session = Depends(get_db)):
    if not crud.obtener_persona(db, persona_id):
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return crud.buscar_turnos(db, persona_id=persona_id)

# ========================== TURNOS ======================
@app.post("/turnos", response_model=schemas.TurnoOut, status_code=status.HTTP_201_CREATED)
def turnos_create(body: schemas.TurnoCreate, db: Session = Depends(get_db)):
    return crud.crear_turno(db, body)

@app.get("/turnos", response_model=List[schemas.TurnoOut])
def turnos_list(db: Session = Depends(get_db)):
    return crud.listar_turnos(db)

@app.get("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def turnos_get(turno_id: int, db: Session = Depends(get_db)):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t

@app.put("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def turnos_update(turno_id: int, body: schemas.TurnoCreate, db: Session = Depends(get_db)):
    t = crud.actualizar_turno(db, turno_id, body)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t

@app.delete("/turnos/{turno_id}", status_code=status.HTTP_204_NO_CONTENT)
def turnos_delete(turno_id: int, db: Session = Depends(get_db)):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    crud.eliminar_turno(db, turno_id)
    return None

# ===== ENDPOINT 1: Buscador de turnos (filtros combinables) =====
@app.get("/turnos/buscar", response_model=List[schemas.TurnoOut])
def turnos_search(
    persona_id: Optional[int] = Query(default=None, description="Filtra por persona"),
    fecha_desde: Optional[date] = Query(default=None, description="Incluye esta fecha"),
    fecha_hasta: Optional[date] = Query(default=None, description="Incluye esta fecha"),
    # En schemas.py el estado es str; si usás Enum en schemas, cambialo aquí.
    estado: Optional[str] = Query(default=None, description="pendiente/cancelado/confirmado/asistido"),
    db: Session = Depends(get_db)
):
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(status_code=400, detail="fecha_desde no puede ser mayor que fecha_hasta")

    return crud.buscar_turnos(
        db,
        persona_id=persona_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        estado=estado
    )

# ===== ENDPOINT 3: Reprogramar turno (fecha/hora) con control de conflictos =====
@app.patch("/turnos/{turno_id}/reprogramar", response_model=schemas.TurnoOut)
def turnos_reprogramar(
    turno_id: int,
    body: ReprogramarTurnoIn,
    db: Session = Depends(get_db)
):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if crud.existe_conflicto_turno(
        db=db,
        persona_id=t.persona_id,
        fecha=body.fecha,
        hora=body.hora,
        excluir_turno_id=turno_id
    ):
        raise HTTPException(status_code=409, detail="Conflicto: la persona ya tiene un turno en esa fecha y hora")

    t_actualizado = crud.reprogramar_turno(db, turno_id, body.fecha, body.hora)
    return t_actualizado

# ===== EXTRA: Cambiar estado del turno (confirmar/cancelar/asistido/pendiente) =====
@app.patch("/turnos/{turno_id}/estado", response_model=schemas.TurnoOut)
def turnos_cambiar_estado(
    turno_id: int,
    body: CambiarEstadoTurnoIn,
    db: Session = Depends(get_db)
):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    # Validación simple de valores permitidos (ajusta si usás Enum en models/schemas)
    if body.estado not in {"pendiente", "cancelado", "confirmado", "asistido"}:
        raise HTTPException(status_code=400, detail="Estado inválido")

    # Reusar tu CRUD de actualización construyendo el TurnoCreate con el mismo turno pero nuevo estado
    nuevo = schemas.TurnoCreate(
        fecha=t.fecha,
        hora=t.hora,
        estado=body.estado,
        persona_id=t.persona_id
    )
    actualizado = crud.actualizar_turno(db, turno_id, nuevo)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return actualizado
