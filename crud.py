from sqlalchemy.orm import Session
import models, schemas
from typing import Optional, List
from datetime import date, time, datetime, timedelta

# --------------> Personas <------------

def crear_persona(db: Session, persona: schemas.PersonaCreate):
    db_persona = models.Persona(**persona.dict())  # usa .dict() (Pydantic v1)
    db.add(db_persona)
    db.commit()
    db.refresh(db_persona)
    return db_persona

def listar_personas(db: Session):
    return db.query(models.Persona).all()

def obtener_persona(db: Session, persona_id: int):
    return db.query(models.Persona).filter(models.Persona.id == persona_id).first()

def eliminar_persona(db: Session, persona_id: int):
    p = obtener_persona(db, persona_id)
    if p:
        db.delete(p)
        db.commit()

def actualizar_persona(db: Session, persona_id: int, persona_data: schemas.PersonaCreate):
    p = obtener_persona(db, persona_id)
    if p:
        for key, value in persona_data.dict().items():
            setattr(p, key, value)
        db.commit()
        db.refresh(p)
    return p

def eliminar_persona(db: Session, persona_id: int) -> bool:
    p = obtener_persona(db, persona_id)
    if p:
        db.delete(p)
        db.commit()
        return True   # Devuelve True si borró algo
    return False      # Devuelve False si no existía


# ---------------> Turnos <------------

def crear_turno(db: Session, turno: schemas.TurnoCreate):
    db_turno = models.Turno(**turno.dict())  # usa .dict() (Pydantic v1)
    db.add(db_turno)
    db.commit()
    db.refresh(db_turno)
    return db_turno

def listar_turnos(db: Session):
    # FIX del typo: era '),all()'
    return db.query(models.Turno).all()

def obtener_turno(db: Session, turno_id: int) -> Optional[models.Turno]:
    # Alternativa: return db.get(models.Turno, turno_id)
    return (
        db.query(models.Turno)
          .filter(models.Turno.id == turno_id)
          .first()
    )

def actualizar_turno(db: Session, turno_id: int, turno_data: schemas.TurnoCreate):
    t = obtener_turno(db, turno_id)
    if t:
        for key, value in turno_data.dict().items():
            setattr(t, key, value)
        db.commit()
        db.refresh(t)
    return t

#def eliminar_turno(db: Session, turno_id: int):
  #  t = obtener_turno(db, turno_id)
  #  if t:
 #       db.delete(t)
 #       db.commit()
def eliminar_turno(db: Session, turno_id: int) -> bool:
    t = obtener_turno(db, turno_id)
    if t:
        db.delete(t)
        db.commit()
        return True
    return False


def buscar_turnos(
    db: Session,
    persona_id: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    estado: Optional[str] = None,  # en schemas el estado es str
) -> List[models.Turno]:
    q = db.query(models.Turno)

    if persona_id is not None:
        q = q.filter(models.Turno.persona_id == persona_id)
    if estado is not None:
        q = q.filter(models.Turno.estado == estado)
    if fecha_desde is not None:
        q = q.filter(models.Turno.fecha >= fecha_desde)
    if fecha_hasta is not None:
        q = q.filter(models.Turno.fecha <= fecha_hasta)

    return q.order_by(models.Turno.fecha.asc(), models.Turno.hora.asc()).all()


def existe_conflicto_turno(
    db: Session,
    persona_id: int,
    fecha: date,
    hora: time,
    excluir_turno_id: Optional[int] = None
) -> bool:
    q = (
        db.query(models.Turno)
          .filter(
              models.Turno.persona_id == persona_id,
              models.Turno.fecha == fecha,
              models.Turno.hora == hora,
          )
    )
    if excluir_turno_id is not None:
        q = q.filter(models.Turno.id != excluir_turno_id)
    return db.query(q.exists()).scalar()

def reprogramar_turno(db: Session, turno_id: int, nueva_fecha: date, nueva_hora: time):
    t = db.query(models.Turno).filter(models.Turno.id == turno_id).first()
    if not t:
        return None
    t.fecha = nueva_fecha
    t.hora = nueva_hora
    db.commit()
    db.refresh(t)
    return t
