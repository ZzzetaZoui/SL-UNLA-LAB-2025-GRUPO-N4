from datetime import date, time
from typing import Optional
from pydantic import BaseModel, EmailStr

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

class PersonaBase(BaseModel):
    nombre: str
    apellido: str
    dni: int
    email: EmailStr
    telefono: str
    fecha_nacimiento: date

class PersonaIn(PersonaBase):
    pass

class PersonaOut(PersonaBase):
    id: int
    activo: bool

class TurnoIn(BaseModel):
    persona_id: int
    fecha: date
    hora: time
    estado: str = "pendiente"

class TurnoOut(BaseModel):
    fecha: date
    hora: str
    persona_id: int

class Estado(BaseModel):
    hora: str
    disponible: bool

