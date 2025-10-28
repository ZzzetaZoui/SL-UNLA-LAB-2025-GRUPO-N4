from pydantic import BaseModel, EmailStr
from datetime import date, time
from typing import Optional, Literal, List

# --- Tipos Personalizados ---

# Definimos los estados válidos para un turno, basados en tu models.py
EstadoTurno = Literal["pendiente", "cancelado", "confirmado", "asistido"]


# =========================
# === SCHEMAS PERSONA ===
# =========================

# Campos base de una Persona
class PersonaBase(BaseModel):
    nombre: str
    apellido: str
    dni: int
    email: EmailStr
    telefono: str
    fecha_nacimiento: date

# Schema para la CREACIÓN (POST /personas)
class PersonaCreate(PersonaBase):
    pass  # Hereda todos los campos base

# Schema para la RESPUESTA (GET /personas/1)
class PersonaOut(PersonaBase):
    id: int
    activo: bool

    class Config:
        # Permite que Pydantic lea los datos desde el modelo de SQLAlchemy
        orm_mode = True # Para Pydantic v1 (como indica crud.py)


# =========================
# === SCHEMAS TURNO ===
# =========================

# Campos base de un Turno
class TurnoBase(BaseModel):
    fecha: date
    hora: time
    persona_id: int

# Schema para la CREACIÓN (POST /turnos)
class TurnoCreate(TurnoBase):
    # El estado tiene un default "pendiente" en el modelo
    # Lo hacemos opcional para que al crear/actualizar no sea obligatorio enviarlo
    estado: Optional[EstadoTurno] = "pendiente"

# Schema para la RESPUESTA (GET /turnos/1)
class TurnoOut(TurnoBase):
    id: int
    estado: EstadoTurno

    class Config:
        orm_mode = True


class SlotDisponible(BaseModel):
    hora: time
    estado: str  # Será "disponible" u "ocupado"

# =========================
# === SCHEMAS ESPECIALES ===
# =========================

# Schema para el ENDPOINT 3 (Reprogramar)
class ReprogramarTurnoIn(BaseModel):
    fecha: date
    hora: time

# Schema para el EXTRA (Cambiar Estado)
class CambiarEstadoTurnoIn(BaseModel):
    estado: EstadoTurno

"""""
#--------------REPORTES OBLIGATORIOS---------------

# Schema para Reporte 2: /reportes/turnos-cancelados-por-mes
class ReporteCanceladosMes(BaseModel):
    anio: int
    mes: str
    cantidad: int
    turnos: List[TurnoOut] # Lista de los turnos cancelados

# Schema para Reporte 4: /reportes/turnos-cancelados?min=5
class ReportePersonaCancelados(BaseModel):
    persona: PersonaOut
    total_cancelados: int
"""
