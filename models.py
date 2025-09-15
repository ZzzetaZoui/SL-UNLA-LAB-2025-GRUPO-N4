from datetime import date, time
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Date, Time, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Persona(Base):
    __tablename__ = "personas"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    dni = Column(Integer, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefono = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    activo = Column(Integer, default=1)  # 1 para activo, 0 para inactivo
    turnos = relationship("Turno", back_populates="persona")

class Usuario(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    fecha_nacimiento: date
    email: EmailStr
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str


USUARIOS: List[Usuario] = []

def buscar_usuario_por_email(email: str) -> Optional[Usuario]:
    for u in USUARIOS:                        
        if u.email.lower() == email.lower():
            return u
    return None

#ABM/CRUD PARA EL REGISTRO DE LOS USUARIOS Y MODIFICACIONES SI ES NECESARIO

class PersonaIn(BaseModel):
    nombre: str
    apellido: str
    dni: int
    email: EmailStr
    telefono: str
    fecha_nacimiento: date

class PersonaOut(PersonaIn):
    id: int
    activo: bool = True

PERSONAS: List[PersonaOut] = []
_next_pid = 1

class TurnoIn(BaseModel):
    persona_id: int
    fecha: date
    hora: time 

class TurnoOut(BaseModel):
    fecha: date
    hora: str
    persona_id: int
TURNOS: List[TurnoIn] = []


class Turno(Base):
    __tablename__ = "turnos"
    id = Column(Integer, primary_key=True)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    estado = Column(Enum("pendiente", "cancelado", "confirmado", "asistido", name="estado_turno"), default="pendiente")
    persona_id = Column(Integer, ForeignKey("personas.id"))
    persona = relationship("Persona", back_populates="turnos")


def _dump(model: BaseModel) -> dict:
    """Compat: Pydantic v2 (model_dump) / v1 (dict)."""
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()

#CORROBORA SI EL EMAIL ESTÁ DUPLICADO Y EN CASO DE QUE SI, SI TIRA EL MENSAJE QUE ESTA DUPLICADO
def crear_persona(data: PersonaIn) -> PersonaOut:
    global _next_pid
    if any(p.email.lower() == data.email.lower() for p in PERSONAS):
        raise ValueError("El email está duplicado")
    p = PersonaOut(id=_next_pid, **_dump(data))
    _next_pid += 1
    PERSONAS.append(p)
    return p

def obtener_persona(pid: int) -> Optional[PersonaOut]:
    return next((p for p in PERSONAS if p.id == pid), None)

def listar_personas() -> List[PersonaOut]:
    return PERSONAS

def modificar_persona(pid: int, data: PersonaIn) -> Optional[PersonaOut]:
    p = obtener_persona(pid)
    if not p:
        return None
    actualizado = PersonaOut(id=p.id, activo=p.activo, **_dump(data)) #TAMBIEN MANTIENE EL ID AL MODIFICA
    PERSONAS[PERSONAS.index(p)] = actualizado
    return actualizado

def eliminar_persona(pid: int) -> bool:
    p = obtener_persona(pid)
    if not p:
        return False
    PERSONAS.remove(p)
    return True

