from datetime import date
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