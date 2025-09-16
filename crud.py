from datetime import date
from typing import List, Optional
from schemas import PersonaIn, PersonaOut, TurnoIn, TurnoOut
from pydantic import BaseModel

USUARIOS: List[BaseModel] = []
PERSONAS: List[PersonaOut] = []
TURNOS: List[TurnoIn] = []
_next_pid = 1

def buscar_usuario_por_email(email: str) -> Optional[BaseModel]:
    return next((u for u in USUARIOS if u.email.lower() == email.lower()), None)

def crear_persona(data: PersonaIn) -> PersonaOut:
    global _next_pid
    if any(p.email.lower() == data.email.lower() for p in PERSONAS):
        raise ValueError("El email está duplicado")
    p = PersonaOut(id=_next_pid, activo=True, **data.dict())
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
    actualizado = PersonaOut(id=p.id, activo=p.activo, **data.dict())
    PERSONAS[PERSONAS.index(p)] = actualizado
    return actualizado

def eliminar_persona(pid: int) -> bool:
    p = obtener_persona(pid)
    if not p:
        return False
    PERSONAS.remove(p)
    return True

def calcular_edad(fecha_nacimiento: date) -> int:
    from datetime import date as d
    hoy = d.today()
    edad = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    return edad
