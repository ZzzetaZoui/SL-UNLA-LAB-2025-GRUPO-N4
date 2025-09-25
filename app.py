from fastapi import FastAPI, HTTPException, status, Query, Depends
from datetime import date, time, datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
import schemas, crud
from database import engine, get_db
from models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

def calcular_edad(fecha_nacimiento: date) -> int:
    today = date.today()
    age = today.year - fecha_nacimiento.year - ((today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    return age

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
