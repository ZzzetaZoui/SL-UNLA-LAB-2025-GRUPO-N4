from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from calendar import month_name
from database import get_db
import schemas, models, crud
from config import ESTADO_TURNO_CANCELADO, ESTADO_TURNO_CONFIRMADO
#from reportes_pdf import generar_pdf_turnos_cancelados
#from reportes_pdf import generar_pdf_reportes
from reportes_pdf import generar_pdf_personas
from reportes_pdf import generar_pdf_turnos_cancelados, generar_pdf_turnos_confirmados
import os

router = APIRouter()

# 🟩 Reporte 1: Obtener todos los turnos de una fecha específica
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
            schemas.TurnoSimpleOut.from_orm(t)  # sin repetir persona
        )

    return [schemas.ReportePersonaConTurnos(**data) for data in agrupado.values()]


# 🟩 Reporte 2 (corregido): Obtener los turnos cancelados del mes agrupados por persona
@router.get("/turnos-cancelados-por-mes", response_model=list[schemas.ReportePersonaConTurnos])
def turnos_cancelados_por_mes(db: Session = Depends(get_db)):
    today = date.today()
    anio, mes = today.year, today.month

    primer_dia = date(anio, mes, 1)
    primer_dia_sgte = date(anio + (mes // 12), (mes % 12) + 1, 1)

    # 1️⃣ Obtener turnos cancelados del mes con su persona
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
        raise HTTPException(status_code=404, detail="No hay turnos cancelados este mes")

    # 2️⃣ Agrupar por persona
    agrupado = {}  # persona_id → { persona, turnos }

    for t in turnos:
        pid = t.persona.id

        if pid not in agrupado:
            agrupado[pid] = {
                "persona": schemas.PersonaOut.from_orm(t.persona),
                "turnos": []
            }

        agrupado[pid]["turnos"].append(
            schemas.TurnoSimpleOut.from_orm(t)  # ❗ sin repetir persona dentro del turno
        )

    # 3️⃣ Convertir a lista
    return [schemas.ReportePersonaConTurnos(**data) for data in agrupado.values()]


# 🟩 Reporte 3: Obtener una persona por DNI y todos sus turnos
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


# 🟩 Reporte 4: Personas con más de N turnos cancelados
@router.get("/turnos-cancelados", response_model=list[schemas.ReportePersonaCancelados])
def personas_con_cancelados(min: int = Query(5, ge=1), db: Session = Depends(get_db)):
    subq = (
        db.query(
            models.Turno.persona_id,
            func.count(models.Turno.id).label("total_cancelados")
        )
        .filter(models.Turno.estado == ESTADO_TURNO_CANCELADO)
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
        # ✅ SOLO turnos cancelados de esa persona
        turnos = (
            db.query(models.Turno)
            .options(joinedload(models.Turno.persona))
            .filter(
                models.Turno.persona_id == persona.id,
                models.Turno.estado == "cancelado"
            )
            .order_by(models.Turno.fecha, models.Turno.hora)
            .all()
        )

        reportes.append(
            schemas.ReportePersonaCancelados(
                persona=schemas.PersonaOut.from_orm(persona),
                total_cancelados=total,
                turnos=[schemas.TurnoOut.from_orm(t) for t in turnos]
            )
        )

    return reportes


# 🟩 Reporte 5: Turnos confirmados
@router.get("/turnos-confirmados", response_model=list[schemas.TurnoOut])
def turnos_confirmados(desde: date, hasta: date, page: int = 1, size: int = 5, db: Session = Depends(get_db)):
    skip = (page - 1) * size
    # 🔹 Se asume que dentro de crud.buscar_turnos se usa joinedload(Turno.persona)
    return crud.buscar_turnos(db, fecha_desde=desde, fecha_hasta=hasta, estado=ESTADO_TURNO_CONFIRMADO, skip=skip, limit=size)


# 🟩 Reporte 6: Personas por estado (habilitadas o deshabilitadas)
@router.get("/estado-personas", response_model=list[schemas.PersonaConTurnosOut])
def personas_por_estado(habilitada: bool, db: Session = Depends(get_db)):
    personas = (
        db.query(models.Persona)
        .options(joinedload(models.Persona.turnos))  # carga turnos de una sola vez
        .filter(models.Persona.activo == habilitada)
        .order_by(models.Persona.apellido)
        .all()
    )
    return personas


# 🟩 Reporte 7: PDF de turnos cancelados del mes actual
# 🟩 Reporte 7: PDF de turnos cancelados del mes seleccionado
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
        if pid not in agrupado:
            agrupado[pid] = []
        agrupado[pid].append(t)

    mes_nombre = month_name[mes].lower()

    nombre_archivo = generar_pdf_turnos_cancelados(
        agrupado=agrupado,
        anio=anio,
        mes=mes_nombre,
    )

    ruta_archivo = os.path.join("pdf", nombre_archivo)

    return FileResponse(
        ruta_archivo,
        media_type="application/pdf",
        filename=nombre_archivo
    )


    ruta_archivo = os.path.join("pdf", nombre_archivo)
    return FileResponse(ruta_archivo, media_type="application/pdf", filename=nombre_archivo)

# 🟩 Reporte 8: PDF de turnos confirmados del mes actual
@router.get("/turnos-confirmados-pdf")
def descargar_pdf_turnos_confirmados(db: Session = Depends(get_db)):
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

    for t in turnos:
        if not t.persona:
            raise HTTPException(status_code=500, detail=f"Turno {t.id} no tiene persona asociada")

    try:
        nombre_archivo = generar_pdf_turnos_confirmados(turnos, anio, month_name[mes].lower(), len(turnos))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")

    ruta_archivo = os.path.join("pdf", nombre_archivo)
    if not os.path.exists(ruta_archivo):
        raise HTTPException(status_code=500, detail="El archivo PDF no fue creado")

    return FileResponse(path=ruta_archivo, media_type="application/pdf", filename=nombre_archivo)


#PDF de personas
from reportes_pdf import generar_pdf_personas

# 🟩 Reporte 9: PDF de listado de personas
@router.get("/personas-pdf")
def personas_pdf(db: Session = Depends(get_db)):
    personas = crud.listar_personas(db)
    if not personas:
        raise HTTPException(status_code=404, detail="No hay personas registradas")

    nombre_archivo = generar_pdf_personas(personas)
    ruta_archivo = os.path.join("pdf", nombre_archivo)

    return FileResponse(ruta_archivo, media_type="application/pdf", filename=nombre_archivo)


#pruebas de Qr
# pruebas de QR
@router.get("/qr/confirmar/{turno_id}")
def confirmar_turno_via_qr(turno_id: int, db: Session = Depends(get_db)):
    turno = db.query(models.Turno).filter(models.Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")

    if turno.estado == ESTADO_TURNO_CONFIRMADO:
        return {"mensaje": f"El turno {turno.id} ya estaba confirmado"}

    turno.estado = ESTADO_TURNO_CONFIRMADO
    db.commit()
    db.refresh(turno)

    return {"mensaje": f"Turno {turno.id} confirmado correctamente"}
#por si quiero implementar en postman http://127.0.0.1:8000/reportes/qr/confirmar/3