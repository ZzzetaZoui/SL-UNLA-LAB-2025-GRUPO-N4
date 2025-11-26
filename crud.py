from sqlalchemy.orm import Session, joinedload
import models, schemas
from typing import Optional, List
from datetime import date, time, datetime, timedelta
from config import ESTADO_TURNO_CANCELADO, ESTADO_TURNO_ASISTIDO, ESTADO_TURNO_CONFIRMADO, ESTADO_TURNO_PENDIENTE

# --------------> Personas <------------

def crear_persona(db: Session, persona: schemas.PersonaCreate):
    db_persona = models.Persona(**persona.dict())  # usa .dict() (Pydantic v1)
    db.add(db_persona)
    db.commit()
    db.refresh(db_persona)
    return db_persona

def listar_personas(db: Session):
    return db.query(models.Persona).all()

def obtener_persona(db: Session, dni: int):
    return db.query(models.Persona).filter(models.Persona.dni == dni).first()

def actualizar_persona(db: Session, dni: int, persona_data: schemas.PersonaCreate):
    p = obtener_persona(db, dni)
    if p:
        for key, value in persona_data.dict().items():
            setattr(p, key, value)
        db.commit()
        db.refresh(p)
    return p

def eliminar_persona(db: Session, dni: int) -> bool:
    p = obtener_persona(db, dni)
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
    # Cargamos la relación 'persona' para que se muestre en el JSON
    return db.query(models.Turno).options(joinedload(models.Turno.persona)).all()

def obtener_turno(db: Session, turno_id: int) -> Optional[models.Turno]:
    # Cargamos la relación 'persona'
    return (
        db.query(models.Turno)
          .options(joinedload(models.Turno.persona))
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

def cambiar_estado_turno(db: Session, turno_id: int, nuevo_estado: str) -> Optional[models.Turno]:
    """
    Busca un turno por ID y actualiza solo su campo 'estado'.
    """
    t = obtener_turno(db, turno_id)
    if t:
        t.estado = nuevo_estado
        db.commit()
        db.refresh(t)
    return t

def eliminar_turno(db: Session, turno_id: int) -> bool:
    t = obtener_turno(db, turno_id)
    if t:
        db.delete(t)
        db.commit()
        return True
    return False


# === ÚNICA MODIFICACIÓN: Añadimos skip y limit para paginación (Reporte 5) ===
def buscar_turnos(
    db: Session,
    dni: Optional[int] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    estado: Optional[str] = None,
    skip: int = 0, # <-- NUEVO
    limit: Optional[int] = None, # <-- NUEVO
) -> List[models.Turno]:
    
    # Cargamos la relación 'persona' (joinedload)
    # para que esté disponible en los reportes
    q = db.query(models.Turno).options(joinedload(models.Turno.persona))

    if dni is not None:
        q = q.filter(models.Turno.dni == dni)
    if estado is not None:
        q = q.filter(models.Turno.estado == estado)
    if fecha_desde is not None:
        q = q.filter(models.Turno.fecha >= fecha_desde)
    if fecha_hasta is not None:
        q = q.filter(models.Turno.fecha <= fecha_hasta)

    q = q.order_by(models.Turno.fecha.asc(), models.Turno.hora.asc())
    
    # === LÓGICA DE PAGINACIÓN AÑADIDA ===
    q = q.offset(skip)
    if limit is not None:
        q = q.limit(limit)
    # === FIN DE LA MODIFICACIÓN ===

    return q.all()


def existe_conflicto_turno(
    db: Session,
    dni: int,
    fecha: date,
    hora: time,
    excluir_turno_id: Optional[int] = None
) -> bool:
    q = (
        db.query(models.Turno)
        .join(models.Persona)
        .filter(
            models.Persona.dni == dni,
            models.Turno.fecha == fecha,
            models.Turno.hora == hora,
            models.Turno.estado != ESTADO_TURNO_CANCELADO
        )
    )
    if excluir_turno_id is not None:
        q = q.filter(models.Turno.id != excluir_turno_id)
    return db.query(q.exists()).scalar()

def reprogramar_turno(db: Session, turno_id: int, nueva_fecha: date, nueva_hora: time):
    t = obtener_turno(db, turno_id)
    if not t:
        return None
    t.fecha = nueva_fecha
    t.hora = nueva_hora
    t.estado = ESTADO_TURNO_PENDIENTE # Un turno reprogramado vuelve a pendiente
    db.commit()
    db.refresh(t)
    return t

def obtener_turnos_disponibles(db: Session, fecha: date):
   inicio, fin = time(9, 0), time(17, 0)
   intervalo = timedelta(minutes=30)
   ocupados = {t.hora for t in buscar_turnos(db, fecha_desde=fecha, fecha_hasta=fecha) if t.estado != ESTADO_TURNO_CANCELADO}
   slots, actual = [], datetime.combine(fecha, inicio)
   while actual.time() < fin:
      hora = actual.time()
      slots.append(schemas.SlotDisponible(hora=hora, estado="ocupado" if hora in ocupados else "disponible"))
      actual += intervalo
   return slots 