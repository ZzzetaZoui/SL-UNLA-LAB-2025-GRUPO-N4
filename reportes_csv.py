# reportes_csv.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from calendar import month_name
import pandas as pd
import os

import models
from database import get_db
from config import ESTADO_TURNO_CANCELADO, ESTADO_TURNO_CONFIRMADO

from io import BytesIO
from fastapi.responses import StreamingResponse

router = APIRouter()

# -------------------------------------------------------------------
# Función para CSV
# -------------------------------------------------------------------
def csv_en_memoria(data: list[dict]):
    buffer = BytesIO()
    df = pd.DataFrame(data)
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    buffer.seek(0)
    return buffer

# -------------------------------------------------------------------
# REPORTE 7 - TURNOS CANCELADOS (CSV)
# -------------------------------------------------------------------
@router.get("/turnos-cancelados-csv")
def turnos_cancelados_csv(
    mes: int = Query(..., ge=1, le=12), #recibe como parametros.
    anio: int = Query(..., ge=2000),
    db: Session = Depends(get_db)
):
    primer_dia = date(anio, mes, 1)
    primer_dia_sgte = date(anio + (mes // 12), (mes % 12) + 1, 1) #basic crea el incio del rango empezando por la fecha seleccionada

    turnos = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona)) #asegyrar q el turno venga con cada persona
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

    data = [
        {
            "persona_apellido": t.persona.apellido,
            "persona_nombre": t.persona.nombre,
            "dni": t.persona.dni,
            "fecha": t.fecha.strftime("%d/%m/%Y"),
            "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado,
        }
        for t in turnos
    ]

    nombre_archivo = f"reporte_cancelados_{month_name[mes].lower()}_{anio}.csv"
    buffer = csv_en_memoria(data)

    return StreamingResponse(
        buffer,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
            }
    )

# -------------------------------------------------------------------
# REPORTE 5 - TURNOS CONFIRMADOS (CSV)
# -------------------------------------------------------------------
@router.get("/turnos-confirmados-csv")
def turnos_confirmados_csv(
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
        raise HTTPException(status_code=404, detail="No hay turnos confirmados en ese mes")

    data = [
        {
            "persona_apellido": t.persona.apellido,
            "persona_nombre": t.persona.nombre,
            "dni": t.persona.dni,
            "fecha": t.fecha.strftime("%d/%m/%Y"),
            "hora": t.hora.strftime("%H:%M"),
            "estado": t.estado,
        }
        for t in turnos
    ]

    nombre_archivo = f"reporteconfirmados_{month_name[mes].lower()}_{anio}.csv"
    buffer = csv_en_memoria(data)

    return StreamingResponse(
        buffer,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"'
            }
    )