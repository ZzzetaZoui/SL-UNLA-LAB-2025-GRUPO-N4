from fastapi import FastAPI, HTTPException, status, Query, Depends
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Base
import schemas
import crud
import reportes  # <-- Rutas de reportes
import reportes_pdf # <-- exportaciones (nuevoo)
import reportes_csv
import models
from config import ESTADO_TURNO_CANCELADO, ESTADO_TURNO_ASISTIDO, ESTADO_TURNO_CONFIRMADO, ESTADO_TURNO_PENDIENTE


#from fastapi.middleware.cors import CORSMiddleware

# Crear tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API de Turnos", version="1.0") 

# ------------------- RAÍZ -------------------
@app.get("/")
def root():
    return {"mensaje": "API funcionando. Visita /docs para probar."}

# ========================= HELPERS ======================
def calcular_edad(fecha_nacimiento: date) -> int:
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - (
        (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day) #valida para q sea mayor de edad
    )
#
# ========================= PERSONAS =====================
@app.post("/personas", response_model=schemas.PersonaOut, status_code=status.HTTP_201_CREATED)
def crear_persona(body: schemas.PersonaCreate, db: Session = Depends(get_db)):
    if calcular_edad(body.fecha_nacimiento) < 18:
        raise HTTPException(status_code=400, detail="Debe ser mayor de 18 años")
    return crud.crear_persona(db, body)

@app.get("/personas", response_model=List[schemas.PersonaOut])
def listar_personas(db: Session = Depends(get_db)):
    return crud.listar_personas(db)

@app.get("/personas/{dni}", response_model=schemas.PersonaOut)
def obtener_persona(dni: int, db: Session = Depends(get_db)):
    p = crud.obtener_persona(db, dni)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

@app.put("/personas/{dni}", response_model=schemas.PersonaOut)
def actualizar_persona(dni: int, body: schemas.PersonaCreate, db: Session = Depends(get_db)):
    p = crud.actualizar_persona(db, dni, body)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

@app.delete("/personas/{dni}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_persona(dni: int, db: Session = Depends(get_db)):
    if not crud.eliminar_persona(db, dni):
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return

@app.get("/personas/{dni}/turnos", response_model=List[schemas.TurnoOut])
def turnos_de_persona(dni: int, db: Session = Depends(get_db)):
    return crud.buscar_turnos(db, dni=dni)
# ===================== DASHBOARD ========================
@app.get("/turnos/proximos", response_model=List[schemas.TurnoOut])
def proximos_turnos(
    dias: int = Query(1, ge=1, le=30),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    fecha_hoy = date.today()
    fecha_fin = fecha_hoy + timedelta(days=dias - 1)
    return crud.buscar_turnos(db, fecha_desde=fecha_hoy, fecha_hasta=fecha_fin, estado=estado)

# ========================= TURNOS =======================
@app.post("/turnos", response_model=schemas.TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(body: schemas.TurnoCreate, db: Session = Depends(get_db)):
    if crud.existe_conflicto_turno(db, body.persona_id, body.fecha, body.hora):
        raise HTTPException(status_code=400, detail="Conflicto de horario")
    return crud.crear_turno(db, body)

@app.get("/turnos", response_model=List[schemas.TurnoListOut])
def listar_turnos(db: Session = Depends(get_db)):
    turnos = crud.listar_turnos(db)
    return [schemas.TurnoListOut.from_orm(t) for t in turnos]

@app.get("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t

@app.put("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def actualizar_turno(turno_id: int, body: schemas.TurnoCreate, db: Session = Depends(get_db)):
    t = crud.actualizar_turno(db, turno_id, body)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t

@app.delete("/turnos/{turno_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_turno(turno_id: int, db: Session = Depends(get_db)):
    if not crud.eliminar_turno(db, turno_id):
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return

# ===================== GESTIÓN DE ESTADO (Punto D) =====================

@app.put("/turnos/{turno_id}/cancelar", response_model=schemas.TurnoOut)
def cancelar_turno(turno_id: int, db: Session = Depends(get_db)):

    turno = crud.obtener_turno(db, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno.estado in [ESTADO_TURNO_CANCELADO, ESTADO_TURNO_ASISTIDO]:
        raise HTTPException(status_code=400, detail="No se puede modificar un turno cancelado o asistido")


    cancelados = (
        db.query(models.Turno)
        .filter(
            models.Turno.persona_id == turno.persona_id,
            models.Turno.estado == ESTADO_TURNO_CANCELADO
        )
        .count()
    )

    if cancelados >= 5:
        raise HTTPException(status_code=400, detail="La persona ya alcanzó el máximo de 5 turnos cancelados")

    return crud.cambiar_estado_turno(db, turno_id, ESTADO_TURNO_CANCELADO)

@app.put("/turnos/{turno_id}/confirmar", response_model=schemas.TurnoOut)
def confirmar_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = crud.obtener_turno(db, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if turno.estado in [ESTADO_TURNO_CANCELADO, ESTADO_TURNO_ASISTIDO]:
        raise HTTPException(status_code=400, detail="No se puede modificar un turno cancelado o asistido")
    return crud.cambiar_estado_turno(db, turno_id, ESTADO_TURNO_CONFIRMADO)

# ===================== TURNOS DISPONIBLES =========================
@app.get("/turnos-disponibles", response_model=List[schemas.SlotDisponible])
def turnos_disponibles(fecha: date = Query(...), db: Session = Depends(get_db)):
    return crud.obtener_turnos_disponibles(db, fecha)


# ===================== REPORTES =========================
#app.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])

app.include_router(reportes.router, prefix="/reportes", tags=["Reportes JSON/PDF"])
app.include_router(reportes_csv.router, prefix="/reportes-csv", tags=["Reportes CSV"])

#qr
@app.get("/turnos/{turno_id}/confirmar")
def confirmar_turno_via_qr(turno_id: int, db: Session = Depends(get_db)):
    turno = crud.obtener_turno(db, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno.estado == ESTADO_TURNO_CONFIRMADO:
        return {"mensaje": f"El turno {turno.id} ya estaba confirmado"}

    turno.estado = ESTADO_TURNO_CONFIRMADO
    db.commit()
    db.refresh(turno)

    return {"mensaje": f"Turno {turno.id} confirmado correctamente"}
