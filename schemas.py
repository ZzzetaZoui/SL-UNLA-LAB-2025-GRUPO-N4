from datetime import date, time
from typing import List
from pydantic import BaseModel, EmailStr, ConfigDict

class PersonaBase(BaseModel):
    nombre: str
    apellido: str
    dni: int
    email: EmailStr
    telefono: str
    fecha_nacimiento: date
    activo: bool = True

class PersonaCreate(PersonaBase):
    pass

class PersonaOut(PersonaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class TurnoBase(BaseModel):
    fecha: date
    hora: time
    estado: str = "pendiente"
    persona_id: int

class TurnoCreate(TurnoBase):
    pass

class TurnoOut(TurnoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
