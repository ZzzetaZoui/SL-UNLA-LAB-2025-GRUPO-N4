from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time

# Personas
class PersonaCreate(BaseModel):
    nombre: str
    apellido: str
    dni: int
    email: EmailStr
    telefono: str
    fecha_nacimiento: date

class PersonaOut(PersonaCreate):
    id: int
    activo: Optional[bool] = True

    class Config:
        orm_mode = True

# Turnos
class TurnoCreate(BaseModel):
    fecha: date
    hora: time
    persona_id: int

class TurnoOut(TurnoCreate):
    id: int
    estado: Optional[str] = "pendiente"

    class Config:
        orm_mode = True

# Inputs específicos
class ReprogramarTurnoIn(BaseModel):
    fecha: date
    hora: time

class CambiarEstadoTurnoIn(BaseModel):
    estado: str  # "pendiente" | "cancelado" | "confirmado" | "asistido"
