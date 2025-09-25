from sqlalchemy import Column, Integer, String, Date, Time, Enum, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    dni = Column(Integer, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefono = Column(String, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    activo = Column(Boolean, default=True)
    turnos = relationship("Turno", back_populates="persona")

class Turno(Base):
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    estado = Column(
        Enum("pendiente", "cancelado", "confirmado", "asistido",
             name="estado_turno"),
        default="pendiente"
    )
    persona_id = Column(Integer, ForeignKey("personas.id"))
    persona = relationship("Persona", back_populates="turnos")
