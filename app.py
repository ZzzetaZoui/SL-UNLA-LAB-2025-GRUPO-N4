from fastapi import FastAPI, HTTPException, status, Query, Depends
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base
import schemas
import crud

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
    result = crud.eliminar_persona(db, persona_id)
    if not result:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return

# ===== Subrecurso: turnos de una persona =====
@app.get("/personas/{persona_id}/turnos", response_model=List[schemas.TurnoOut])
def persona_turnos(persona_id: int, db: Session = Depends(get_db)):
    return crud.buscar_turnos(db, persona_id=persona_id)

# ===== ENDPOINT 1: Buscador de turnos (filtros combinables) =====
@app.get("/turnos/buscar", response_model=List[schemas.TurnoOut])
def buscar_turnos(
    persona_id: Optional[int] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return crud.buscar_turnos(db, persona_id=persona_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, estado=estado)

# ========================== TURNOS ======================
@app.post("/turnos", response_model=schemas.TurnoOut, status_code=status.HTTP_201_CREATED)
def turnos_create(body: schemas.TurnoCreate, db: Session = Depends(get_db)):
    if hasattr(crud, "existe_conflicto_turno") and crud.existe_conflicto_turno(db, body.persona_id, body.fecha, body.hora):
        raise HTTPException(status_code=400, detail="Conflicto de horario")
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
    result = crud.eliminar_turno(db, turno_id)
    if not result:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return
  


# ===== ENDPOINT 3: Reprogramar turno (fecha/hora) con control de conflictos =====
@app.patch("/turnos/{turno_id}/reprogramar", response_model=schemas.TurnoOut)
def reprogramar_turno(turno_id: int, body: schemas.ReprogramarTurnoIn, db: Session = Depends(get_db)):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if hasattr(crud, "existe_conflicto_turno") and crud.existe_conflicto_turno(db, t.persona_id, body.fecha, body.hora, excluir_turno_id=turno_id):
        raise HTTPException(status_code=400, detail="Conflicto de horario")
    if not hasattr(crud, "reprogramar_turno"):
        raise HTTPException(status_code=501, detail="Función reprogramar_turno no implementada en crud")
    return crud.reprogramar_turno(db, turno_id, body.fecha, body.hora)

# ===== EXTRA: Cambiar estado del turno (confirmar/cancelar/asistido/pendiente) =====
@app.patch("/turnos/{turno_id}/estado", response_model=schemas.TurnoOut)
def cambiar_estado_turno(turno_id: int, body: schemas.CambiarEstadoTurnoIn, db: Session = Depends(get_db)):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if not hasattr(crud, "cambiar_estado_turno"):
        # si no existe, intenta usar actualizar_turno si está implementada (opcional)
        raise HTTPException(status_code=501, detail="Función cambiar_estado_turno no implementada en crud")
    return crud.cambiar_estado_turno(db, turno_id, body.estado)
