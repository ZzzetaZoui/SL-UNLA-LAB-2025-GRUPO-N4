from pydantic import BaseModel, EmailStr
from datetime import date, time
from typing import List, Optional

# ---- Persona ----
class PersonaBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    dni: int
    telefono: str
    fecha_nacimiento: date

class PersonaCreate(PersonaBase):
    pass

class PersonaOut(PersonaBase):
    id: int
    activo: Optional[bool] = True
    edad: Optional[int] = None

    class Config:
        orm_mode = True

# ---- Turno ----
class TurnoBase(BaseModel):
    fecha: date
    hora: time
    estado: Optional[str] = "pendiente"

class TurnoCreate(TurnoBase):
    persona_id: int

class TurnoOut(TurnoBase):
    id: int
    persona: PersonaOut

    class Config:
        orm_mode = True

# ---- Slot disponible (para /turnos-disponibles) ----
class SlotDisponible(BaseModel):
    hora: time
    estado: str  # "disponible" o "ocupado"

    class Config:
        orm_mode = True

# ---- Inputs especiales ----
class ReprogramarTurnoIn(BaseModel):
    fecha: date
    hora: time

class CambiarEstadoTurnoIn(BaseModel):
    estado: str  # "pendiente"|"cancelado"|"confirmado"|"asistido"

# ---- Reportes ----
class ReporteCanceladosMes(BaseModel):
    anio: int
    mes: str
    cantidad: int
    turnos: List[TurnoOut]

    class Config:
        orm_mode = True

# Para el endpoint de personas con >= min cancelados:
class ReportePersonaCancelados(BaseModel):
    persona: PersonaOut
    total_cancelados: int
    turnos: List[TurnoOut]

    class Config:
        orm_mode = True
# ---- Nuevo esquema para Reporte 3 ----
class TurnoSimpleOut(BaseModel): #evita repetir el objeto persona dentro de cada turno
    id: int
    fecha: date
    hora: time
    estado: str

    class Config:
        orm_mode = True

class ReportePersonaConTurnos(BaseModel):
    persona: PersonaOut
    turnos: List[TurnoSimpleOut]

    class Config:
        
        orm_mode = True
# ---- Persona con Turnos (para /estado-personas) ----
class PersonaConTurnosOut(PersonaOut):
    turnos: List[TurnoSimpleOut] = []

    class Config:
        orm_mode = True
#específico para el listado
class TurnoListOut(BaseModel):
    id: int
    fecha: date
    hora: time
    estado: str
    persona_id: int   # solo el ID de la persona

    class Config:
        orm_mode = True
