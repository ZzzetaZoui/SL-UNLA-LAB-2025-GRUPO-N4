from sqlalchemy.orm import Session
import models, schemas

def crear_persona(db: Session, persona: schemas.PersonaCreate):
    db_persona = models.Persona(**persona.dict())
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
