# reportes_csv.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from calendar import month_name
import pandas as pd
import os

import models
from database import get_db
from config import ESTADO_TURNO_CANCELADO, ESTADO_TURNO_CONFIRMADO

router = APIRouter()

# -------------------------------------------------------------------
# Función auxiliar para guardar CSV
# -------------------------------------------------------------------
def guardar_csv(data: list[dict], nombre_archivo: str):
    os.makedirs("csv", exist_ok=True)  # crea carpeta si no existe
    ruta_csv = os.path.join("csv", nombre_archivo)
    df = pd.DataFrame(data)
    df.to_csv(ruta_csv, index=False)
    print(f"✅ CSV generado: {ruta_csv}")
    return ruta_csv

# -------------------------------------------------------------------
# REPORTE 7 - TURNOS CANCELADOS (CSV)
# -------------------------------------------------------------------
@router.get("/turnos-cancelados-csv")
def turnos_cancelados_csv(
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
    ruta_csv = guardar_csv(data, nombre_archivo)

    return FileResponse(ruta_csv, media_type="text/csv", filename=nombre_archivo)

# -------------------------------------------------------------------
# REPORTE 5 - TURNOS CONFIRMADOS (CSV)
# -------------------------------------------------------------------
@router.get("/turnos-confirmados-csv")
def turnos_confirmados_csv(db: Session = Depends(get_db)):
    today = date.today()
    anio, mes = today.year, today.month

    turnos = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona))
        .filter(models.Turno.estado == ESTADO_TURNO_CONFIRMADO)
        .filter(func.strftime("%Y-%m", models.Turno.fecha) == f"{anio}-{mes:02d}")
        .all()
    )

    if not turnos:
        raise HTTPException(status_code=404, detail="No hay turnos confirmados este mes")

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

    nombre_archivo = f"reporte_confirmados_{month_name[mes].lower()}_{anio}.csv"
    ruta_csv = guardar_csv(data, nombre_archivo)

    return FileResponse(ruta_csv, media_type="text/csv", filename=nombre_archivo)
