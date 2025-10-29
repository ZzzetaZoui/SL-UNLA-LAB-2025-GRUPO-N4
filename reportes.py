from fastapi import APIRouter, Query, Depends 
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from calendar import month_name
from database import get_db
import schemas, models, crud

router = APIRouter() # Crear un router para los reportes

#Reporte 1: Obtener todos los turnos de una fecha específica.

@router.get("/turnos-por-fecha", response_model=list[schemas.TurnoOut])
def turnos_por_fecha(fecha: date = Query(...), db: Session = Depends(get_db)):
    turnos = (
       
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .filter(models.Turno.fecha == fecha)
        .order_by(models.Turno.hora)
        .all()
    )

    return turnos

#Reporte 2: Obtener la cantidad de turnos cancelados por mes.

@router.get("/turnos-cancelados-por-mes", response_model= schemas.ReporteCanceladosMes)
def turnos_cancelados_por_mes(db: Session = Depends(get_db)):
    today = date.today()
    anio = today.year
    mes = today.month
    primer_dia = date(anio, mes, 1)

    if mes < 12:
        primer_dia_sgte = date(anio, mes + 1, 1)
    else:
        primer_dia_sgte = date(anio + 1, 1, 1)

    turnos = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .filter(
            models.Turno.estado == "cancelado",
            models.Turno.fecha >= primer_dia,
            models.Turno.fecha < primer_dia_sgte,
        )
        .order_by(models.Turno.fecha, models.Turno.hora)
        .all()
    )

    return schemas.ReporteCanceladosMes(
        anio = today.year, 
        mes = month_name[mes].lower(), 
        cantidad = len(turnos), 
        turnos = turnos
    )

#Reporte 3: Obtener todos los turnos de una persona por su DNI.

@router.get("/turnos-por-persona", response_model=list[schemas.TurnoOut])
def turnos_por_persona(dni: int = Query(...), db: Session = Depends(get_db)):
    turnos = (

        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .join(models.Persona)
        .filter(models.Persona.dni == dni)
        .order_by(models.Turno.fecha, models.Turno.hora)
        .all()
    )
    return turnos

#Reporte 4: Personas con más de N turnos cancelados
@router.get("/turnos-cancelados", response_model=list[schemas.ReportePersonaCancelados])
def peronas_con_cancelados(min: int = Query(5, ge=1), db: Session = Depends(get_db)):
    subq = (
        db.query(
            models.Turno.persona_id,
            func.count(models.Turno.id).label("total_cancelados")
        )
        .filter(models.Turno.estado == "cancelado")
        .group_by(models.Turno.persona_id)
        .having(func.count(models.Turno.id) >= min)
        .subquery()
    )

    resultados = (
        db.query(models.Persona, subq.c.total_cancelados)
        .join(subq, models.Persona.id == subq.c.persona_id)
        .all()
    )

    reportes = []
    for persona, total in resultados:
        
        turnos = (
            db.query(models.Turno)
            .filter(models.Turno.persona_id == persona.id, models.Turno.estado == "cancelado")
            .order_by(models.Turno.fecha, models.Turno.hora)
            .all()
        )

        reportes.append(
            schemas.ReportePersonaCancelados(
                persona=persona,
                total_cancelados=total,
                turnos=turnos
            )
        )

    return reportes

#Reporte 5: Turnos confirmados 

@router.get("/turnos-confirmados", response_model=list[schemas.TurnoOut])
def turnos_confirmados(desde : date, hasta, page : int = 1, size : int = 5, db : Session = Depends(get_db)): 
    skip = (page - 1) * size
    return crud.buscar_turnos(db, fecha_desde = desde, fecha_hasta = hasta, estado = "confirmado", skip = skip, limit = size)


#Reporte 6: Personas por estado (habilitadas o deshabilitadas)

@router.get("/estado-personas", response_model=list[schemas.PersonaOut]) 
def personas_por_estado(habilitada: bool, db: Session = Depends(get_db)):
    return db.query(models.Persona).filter(models.Persona.activo == habilitada).order_by(models.Persona.apellido).all()

