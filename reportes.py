from fastapi import APIRouter, Query, Depends 
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from calendar import monthrange
from database import get_db
import schemas, models, crud

router = APIRouter() # Crear un router para los reportes

#Reporte 1: Obtener todos los turnos de una fecha específica.

@router.get("/turnos-por-fecha", response_model=list[schemas.TurnoOut])
def turnos_por_fecha(fecha: date, db: Session = Depends(get_db)):
    return db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.fecha == fecha).order_by(models.Turno.hora).all() 

#Reporte 2: Obtener la cantidad de turnos cancelados por mes.

@router.get("/turnos-cancelados-por-mes", response_model=list[schemas.TurnoOut])
def turnos_cancelados_por_mes(db: Session = Depends(get_db)):
    today = date.today()
    primer_dia = today.replace(day=1)
    ultimo_dia = today.replace(day=monthrange(today.year, today.month)[1])
    turnos = ( 
        db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(
        models.Turno.estado == "cancelado", models.Turno.fecha.between(primer_dia, ultimo_dia).all())
    )

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return schemas.ReporteCanceladosMes(anio = today.year, mes = meses[today.month - 1], cantidad = len(turnos), turnos = turnos)

#Reporte 3: Turnos confirmados 

@router.get("/turnos-confirmados", response_model=list[schemas.TurnoOut])
def turnos_confirmados(desde : date, hasta, page : int = 1, size : int = 5, db : Session = Depends(get_db)): 
    skip = (page - 1) * size
    return crud.buscar_turnos(db, fecha_desde = desde, fecha_hasta = hasta, estado = "confirmado", skip = skip, limit = size)


#Reporte 4: Personas por estado (habilitadas o deshabilitadas)

@router.get("/estado-personas", response_model=list[schemas.PersonaOut]) 
def personas_por_estado(habilitada: bool, db: Session = Depends(get_db)):
    return db.query(models.Persona).filter(models.Persona.activo == habilitada).order_by(models.Persona.apellido).all()

