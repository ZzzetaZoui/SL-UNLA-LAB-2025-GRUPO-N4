from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from calendar import month_name
from database import get_db
import schemas, models, crud
from reportes_pdf import (
    generar_pdf_personas,
    generar_pdf_turnos_cancelados, 
    generar_pdf_turnos_confirmados
)
from typing import Tuple
from io import BytesIO
from config import ESTADO_TURNO_CANCELADO, ESTADO_TURNO_CONFIRMADO

router = APIRouter()

# Reporte 1: Obtener todos los turnos de una fecha específica
@router.get("/turnos-por-fecha", response_model=list[schemas.ReportePersonaConTurnos])
def turnos_por_fecha(fecha: date = Query(...), db: Session = Depends(get_db)):
    turnos = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .filter(models.Turno.fecha == fecha)
        .order_by(models.Turno.hora)
        .all()
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos para esa fecha")

    # Agrupar por persona
    agrupado = {}
    for t in turnos:
        pid = t.persona.id
        
        if pid not in agrupado:
            agrupado[pid] = {
                "persona": schemas.PersonaOut.from_orm(t.persona),
                "turnos": []
            }

        agrupado[pid]["turnos"].append(
            schemas.TurnoSimpleOut.from_orm(t)
        )

    return [schemas.ReportePersonaConTurnos(**data) for data in agrupado.values()]

# Reporte 2: Obtener los turnos cancelados del mes agrupados por persona
@router.get("/turnos-cancelados-por-mes", response_model=list[schemas.ReportePersonaConTurnos])
def turnos_cancelados_por_mes(
    mes: int = Query(..., ge=1, le=12),
    anio: int = Query(..., ge=2000),
    db: Session = Depends(get_db)
):
    primer_dia = date(anio, mes, 1)
    primer_dia_sgte = date(anio + (mes // 12), (mes % 12) + 1, 1)

    turnos = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .filter(
            models.Turno.estado == ESTADO_TURNO_CANCELADO,
            models.Turno.fecha >= primer_dia,
            models.Turno.fecha < primer_dia_sgte,
            models.Turno.persona_id.isnot(None)
        )
        .order_by(models.Turno.fecha, models.Turno.hora)
        .all()
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos cancelados en ese mes")

    agrupado = {}
    for t in turnos:
        pid = t.persona.id
        if pid not in agrupado:
            agrupado[pid] = {
                "persona": schemas.PersonaOut.from_orm(t.persona),
                "turnos": []
            }
        agrupado[pid]["turnos"].append(schemas.TurnoSimpleOut.from_orm(t))

    return [schemas.ReportePersonaConTurnos(**data) for data in agrupado.values()]

# Reporte 3: Obtener una persona por DNI y todos sus turnos
@router.get("/turnos-por-persona", response_model=schemas.ReportePersonaConTurnos)
def turnos_por_persona(dni: int = Query(...), db: Session = Depends(get_db)):
    persona = db.query(models.Persona).filter(models.Persona.dni == dni).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona no encontrada")

    turnos = (
        db.query(models.Turno)
        .filter(models.Turno.persona_id == persona.id)
        .order_by(models.Turno.fecha, models.Turno.hora)
        .all()
    )

    turnos_out = [schemas.TurnoSimpleOut.from_orm(t) for t in turnos]

    return schemas.ReportePersonaConTurnos(
        persona=schemas.PersonaOut.from_orm(persona),
        turnos=turnos_out
    )

# Reporte 4: Personas con más de N turnos cancelados
@router.get("/turnos-cancelados", response_model=list[schemas.ReportePersonaCancelados])
def personas_con_cancelados(min: int = Query(5, ge=1), db: Session = Depends(get_db)):

    # turnos cancelados junto con persona
    turnos_cancelados = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .filter(models.Turno.estado == ESTADO_TURNO_CANCELADO)
        .order_by(models.Turno.persona_id, models.Turno.fecha, models.Turno.hora)
        .all()
    )

    if not turnos_cancelados:
        raise HTTPException(status_code=404, detail="No hay turnos cancelados")

    # agrupar por persona
    agrupado = {}
    for t in turnos_cancelados:
        pid = t.persona.id
        if pid not in agrupado:
            agrupado[pid] = {
                "persona": t.persona,
                "turnos": []
            }
        agrupado[pid]["turnos"].append(t)

    # filtra unicamente personas con >= min turnos
    resultado = []
    for pid, info in agrupado.items():
        total = len(info["turnos"])
        if total >= min:
            resultado.append(
                schemas.ReportePersonaCancelados(
                    persona=schemas.PersonaOut.from_orm(info["persona"]),
                    total_cancelados=total,
                    turnos=[schemas.TurnoOut.from_orm(t) for t in info["turnos"]]
                )
            )

    return resultado

# Reporte 5: Turnos confirmados
@router.get("/turnos-confirmados", response_model=list[schemas.TurnoOut])
def turnos_confirmados(desde: date, hasta: date, page: int = 1, size: int = 5, db: Session = Depends(get_db)):
    skip = (page - 1) * size
    return crud.buscar_turnos(db, fecha_desde=desde, fecha_hasta=hasta, estado=ESTADO_TURNO_CONFIRMADO, skip=skip, limit=size)

# Reporte 6: Personas por estado (habilitadas o deshabilitadas)
@router.get("/estado-personas", response_model=list[schemas.PersonaConTurnosOut])
def personas_por_estado(habilitada: bool, db: Session = Depends(get_db)):
    personas = (
        db.query(models.Persona)
        .options(joinedload(models.Persona.turnos))
        .filter(models.Persona.activo == habilitada)
        .order_by(models.Persona.apellido)
        .all()
    )
    return personas

# Reporte 7: PDF de turnos cancelados del mes seleccionado
@router.get("/turnos-cancelados-pdf")
def turnos_cancelados_pdf(
    mes: int = Query(..., ge=1, le=12),
    anio: int = Query(..., ge=2000),
    db: Session = Depends(get_db)
):
    primer_dia = date(anio, mes, 1)
    primer_dia_sgte = date(anio + (mes // 12), (mes % 12) + 1, 1)

    turnos = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .filter(
            models.Turno.estado == ESTADO_TURNO_CANCELADO,
            models.Turno.fecha >= primer_dia,
            models.Turno.fecha < primer_dia_sgte,
            models.Turno.persona_id.isnot(None)
        )
        .order_by(models.Turno.fecha, models.Turno.hora)
        .all()
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos cancelados en este mes.")

    # Agrupar por persona
    agrupado = {}
    for t in turnos:
        pid = t.persona.id
        agrupado.setdefault(pid, []).append(t)

    mes_nombre = month_name[mes].lower()

    # Stream - Sin archivos en disco
    pdf_stream, nombre_archivo = generar_pdf_turnos_cancelados(
        agrupado=agrupado,
        anio=anio,
        mes=mes_nombre,
    )

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={nombre_archivo}",
            "Cache-Control": "no-cache"
        }
    )

# Reporte 8: PDF de turnos confirmados del mes
@router.get("/turnos-confirmados-pdf")
def descargar_pdf_turnos_confirmados(
    mes: int = Query(..., ge=1, le=12),
    anio: int = Query(..., ge=2000),
    db: Session = Depends(get_db)
):
    primer_dia = date(anio, mes, 1)
    primer_dia_sgte = date(anio + (mes // 12), (mes % 12) + 1, 1)

    turnos = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .filter(
            models.Turno.estado == ESTADO_TURNO_CONFIRMADO,
            models.Turno.fecha >= primer_dia,
            models.Turno.fecha < primer_dia_sgte
        )
        .all()
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos confirmados en este mes")

    # Stream - Sin archivos en disco
    pdf_stream, nombre_archivo = generar_pdf_turnos_confirmados(
        turnos=turnos, 
        anio=anio, 
        mes=month_name[mes].lower(), 
        cantidad=len(turnos)
    )

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={nombre_archivo}",
            "Cache-Control": "no-cache"
        }
    )

# Reporte 9: PDF de listado de personas
@router.get("/personas-pdf")
def personas_pdf(db: Session = Depends(get_db)):
    personas = crud.listar_personas(db)
    if not personas:
        raise HTTPException(status_code=404, detail="No hay personas registradas")

    # Stream - Sin archivos en disco
    pdf_stream, nombre_archivo = generar_pdf_personas(personas)

    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={nombre_archivo}",
            "Cache-Control": "no-cache"
        }
    )
