from datetime import date
from pydantic import EmailStr

class Usuario:
    def __init__(self, email: str, password: str, telefono: int, nombre: str, apellido: str, dni: int, fechaNacimiento: date):
        self.email = email
        self.password = password
        self.telefono = telefono
        self.nombre = nombre
        self.apellido = apellido
        self.dni = dni
        self.fechaNacimiento = fechaNacimiento

USUARIOS=[]

#BUSCAR USUARIO POR EMAIL ES LA UNICA MANERA QUE SEA DIFERENTE
def buscar_usuario_por_email(email: str):
    for i in USUARIOS:
        if i.email == email:
            return i
    return None

def registrar_usuario(usuario: Usuario):
    if buscar_usuario_por_email(usuario.email):
        return False
    USUARIOS.append(usuario)
    return True

