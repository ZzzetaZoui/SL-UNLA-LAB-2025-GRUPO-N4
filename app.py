from fastapi import FastAPI, HTTPException, status, Query, Depends
from datetime import date, time, timedelta, datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func # <-- Importamos 'func' para conteos
from database import engine, get_db
from models import Base, Persona, Turno # <-- Importamos los Modelos
import schemas
import crud
import calendar # <-- Para el nombre del mes
from calendar import monthrange # <-- Para el último día del mes

# Crea tablas en SQLite si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ========================= RAÍZ =========================
@app.get("/docs")
def read_root():
    return {"mensaje": "API funcionando. Usa /docs para probar la API."}

# ========================= HELPERS ======================
def calcular_edad(fecha_nacimiento: date) -> int:
    today = date.today()
    age = today.year - fecha_nacimiento.year - (
        (today.month, today.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
    )
    return age

# ========================= PERSONAS =====================
@app.post("/personas", response_model=schemas.PersonaOut, status_code=status.HTTP_201_CREATED)
def personas_create(body: schemas.PersonaCreate, db: Session = Depends(get_db)):
    if calcular_edad(body.fecha_nacimiento) < 18:
        raise HTTPException(status_code=400, detail="Debe ser mayor de 18 años")
    return crud.crear_persona(db, body)

@app.get("/personas", response_model=List[schemas.PersonaOut])
def personas_list(db: Session = Depends(get_db)):
    return crud.listar_personas(db)

@app.get("/personas/{persona_id}", response_model=schemas.PersonaOut)
def personas_get(persona_id: int, db: Session = Depends(get_db)):
    p = crud.obtener_persona(db, persona_id)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

@app.put("/personas/{persona_id}", response_model=schemas.PersonaOut)
def personas_update(persona_id: int, body: schemas.PersonaCreate, db: Session = Depends(get_db)):
    p = crud.actualizar_persona(db, persona_id, body)
    if not p:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return p

@app.delete("/personas/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def personas_delete(persona_id: int, db: Session = Depends(get_db)):
    result = crud.eliminar_persona(db, persona_id)
    if not result:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return

# ===== Subrecurso: turnos de una persona =====
@app.get("/personas/{persona_id}/turnos", response_model=List[schemas.TurnoOut])
def persona_turnos(persona_id: int, db: Session = Depends(get_db)):
    return crud.buscar_turnos(db, persona_id=persona_id)

# ===== ENDPOINT 1: Buscador de turnos (filtros combinables) =====
@app.get("/turnos/buscar", response_model=List[schemas.TurnoOut])
def buscar_turnos(
    persona_id: Optional[int] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return crud.buscar_turnos(db, persona_id=persona_id, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, estado=estado)

# ========================== TURNOS ======================
@app.post("/turnos", response_model=schemas.TurnoOut, status_code=status.HTTP_201_CREATED)
def turnos_create(body: schemas.TurnoCreate, db: Session = Depends(get_db)):
    if hasattr(crud, "existe_conflicto_turno") and crud.existe_conflicto_turno(db, body.persona_id, body.fecha, body.hora):
        raise HTTPException(status_code=400, detail="Conflicto de horario")
    return crud.crear_turno(db, body)

@app.get("/turnos", response_model=List[schemas.TurnoOut])
def turnos_list(db: Session = Depends(get_db)):
    return crud.listar_turnos(db)

@app.get("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def turnos_get(turno_id: int, db: Session = Depends(get_db)):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t

@app.put("/turnos/{turno_id}", response_model=schemas.TurnoOut)
def turnos_update(turno_id: int, body: schemas.TurnoCreate, db: Session = Depends(get_db)):
    t = crud.actualizar_turno(db, turno_id, body)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return t

@app.delete("/turnos/{turno_id}", status_code=status.HTTP_204_NO_CONTENT)
def turnos_delete(turno_id: int, db: Session = Depends(get_db)):
    result = crud.eliminar_turno(db, turno_id)
    if not result:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return

# ===== ENDPOINT 2: Ver disponibilidad de turnos en una fecha =====
@app.get("/turnos-disponibles", response_model=List[schemas.SlotDisponible])
def turnos_disponibles(fecha: date = Query(...), db: Session = Depends(get_db)):
    
    # 1. Definir el rango de trabajo
    inicio_jornada = time(9, 0)
    fin_jornada = time(17, 0) # 5 PM (último turno es a las 16:30)
    intervalo = timedelta(minutes=30)

    # 2. Obtener TODOS los turnos ya reservados para esa fecha
    # Usamos la función de crud que ya existe
    turnos_reservados_db = crud.buscar_turnos(db, fecha_desde=fecha, fecha_hasta=fecha)
    
    # 3. Crear un "set" (para búsqueda rápida) de las horas ocupadas
    # Ignoramos los "cancelados", ya que SÍ están disponibles
    horas_ocupadas = {
        t.hora for t in turnos_reservados_db 
        if t.estado != "cancelado"
    }

    # 4. Generar la lista de todos los slots posibles y verificar
    slots_del_dia = []
    slot_actual_dt = datetime.combine(fecha, inicio_jornada)
    fin_jornada_dt = datetime.combine(fecha, fin_jornada)

    while slot_actual_dt < fin_jornada_dt:
        hora_actual = slot_actual_dt.time()
        
        if hora_actual in horas_ocupadas:
            slots_del_dia.append(schemas.SlotDisponible(hora=hora_actual, estado="ocupado"))
        else:
            slots_del_dia.append(schemas.SlotDisponible(hora=hora_actual, estado="disponible"))
        
        # Avanzar al siguiente slot
        slot_actual_dt += intervalo

    return slots_del_dia
  


# ===== ENDPOINT 3: Reprogramar turno (fecha/hora) con control de conflictos =====
@app.patch("/turnos/{turno_id}/reprogramar", response_model=schemas.TurnoOut)
def reprogramar_turno(turno_id: int, body: schemas.ReprogramarTurnoIn, db: Session = Depends(get_db)):
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    if hasattr(crud, "existe_conflicto_turno") and crud.existe_conflicto_turno(db, t.persona_id, body.fecha, body.hora, excluir_turno_id=turno_id):
        raise HTTPException(status_code=400, detail="Conflicto de horario")
    if not hasattr(crud, "reprogramar_turno"):
        raise HTTPException(status_code=501, detail="Función reprogramar_turno no implementada en crud")
    return crud.reprogramar_turno(db, turno_id, body.fecha, body.hora)

# ===== EXTRA: Cambiar estado del turno (confirmar/cancelar/asistido/pendiente) =====
@app.patch("/turnos/{turno_id}/estado", response_model=schemas.TurnoOut)
def cambiar_estado_turno(turno_id: int, body: schemas.CambiarEstadoTurnoIn, db: Session = Depends(get_db)):
    # Verificamos primero que el turno exista
    t = crud.obtener_turno(db, turno_id)
    if not t:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    
    # Llamamos a la función de crud que SÍ existe (la que agregamos)
    # Esta función también busca el turno, lo actualiza y guarda.
    return crud.cambiar_estado_turno(db, turno_id, body.estado)

# ===== ENDOPOINT 4: Dashboard de Próximos Turnos (Agenda) =====
@app.get("/turnos/proximos", response_model=List[schemas.TurnoOut])
def get_proximos_turnos(
    dias: int = Query(1, ge=1, le=30, description="Número de días a consultar (1 = hoy)"),
    estado: Optional[schemas.EstadoTurno] = Query(None, description="Filtrar por estado (ej: 'confirmado')"),
    db: Session = Depends(get_db)
):
    """
    Obtiene los turnos para los próximos 'dias' (por defecto 1, solo hoy).
    Ideal para un dashboard o agenda.
    """
    # 1. Calcular el rango de fechas
    fecha_hoy = date.today()
    # Si dias=1, fecha_fin es hoy. Si dias=7, es hoy + 6 dias.
    fecha_fin = fecha_hoy + timedelta(days=dias - 1)
    
    # 2. Reutilizar la función de búsqueda existente
    return crud.buscar_turnos(
        db=db,
        fecha_desde=fecha_hoy,
        fecha_hasta=fecha_fin,
        estado=estado
        # La función buscar_turnos ya ordena por fecha y hora
    )

""""

# ------------ SECCIÓN DE REPORTES OBLIGATORIOS -------------

# 1. Turnos de una fecha
@app.get("/reportes/turnos-por-fecha", response_model=List[schemas.TurnoOut])
def reporte_turnos_por_fecha(
    fecha: date = Query(...),
    db: Session = Depends(get_db)
):

    #Reporte 1: Devuelve todos los turnos de una fecha específica
    #con la información de la persona.

    # Lógica de la consulta DENTRO del endpoint
    turnos = (
        db.query(Turno)
          .options(joinedload(Turno.persona)) # Carga la info de persona
          .filter(Turno.fecha == fecha)
          .order_by(Turno.hora.asc())
          .all()
    )
    return turnos

# 2. Turnos cancelados mes actual
@app.get("/reportes/turnos-cancelados-por-mes", response_model=schemas.ReporteCanceladosMes)
def reporte_turnos_cancelados_mes(db: Session = Depends(get_db)):

    #Reporte 2: Devuelve los turnos cancelados en el mes en curso.
    # Lógica de la consulta DENTRO del endpoint
    today = date.today()
    primer_dia = today.replace(day=1)
    ultimo_dia_num = monthrange(today.year, today.month)[1]
    ultimo_dia = today.replace(day=ultimo_dia_num)

    turnos_cancelados = (
        db.query(Turno)
          .options(joinedload(Turno.persona))
          .filter(
              Turno.estado == "cancelado",
              Turno.fecha >= primer_dia,
              Turno.fecha <= ultimo_dia
          )
          .order_by(Turno.fecha.asc())
          .all()
    )
    
    # Nombres de meses en español
    nombres_meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    return schemas.ReporteCanceladosMes(
        anio=today.year,
        mes=nombres_meses_es.get(today.month, "Desconocido"),
        cantidad=len(turnos_cancelados),
        turnos=turnos_cancelados
    )

# 3. Turnos de una persona
@app.get("/reportes/turnos-por-persona", response_model=List[schemas.TurnoOut])
def reporte_turnos_por_persona(
    dni: int = Query(..., description="DNI de la persona a buscar"),
    db: Session = Depends(get_db)
):

    #Reporte 3: Devuelve todos los turnos de una persona, buscada por DNI.

    # Lógica de la consulta DENTRO del endpoint
    turnos = (
        db.query(Turno)
          .options(joinedload(Turno.persona))
          .join(Persona, Turno.persona_id == Persona.id) # Une con la tabla Persona
          .filter(Persona.dni == dni) # Filtra por DNI
          .order_by(Turno.fecha.asc())
          .all()
    )
    return turnos

# 4. Personas con 5 turnos cancelados como mínimo
@app.get("/reportes/turnos-cancelados", response_model=List[schemas.ReportePersonaCancelados])
def reporte_personas_con_turnos_cancelados(
    min: int = Query(5, ge=1, description="Número mínimo de turnos cancelados"),
    db: Session = Depends(get_db)
):

    #Reporte 4: Devuelve personas que tengan 'min' o más turnos cancelados.

    # Lógica de la consulta DENTRO del endpoint
    resultados = (
        db.query(
            Persona,
            func.count(Turno.id).label("total_cancelados")
        )
        .join(Turno, Turno.persona_id == Persona.id)
        .filter(Turno.estado == "cancelado")
        .group_by(Persona.id)
        .having(func.count(Turno.id) >= min)
        .order_by(func.count(Turno.id).desc())
        .all()
    )
    
    # Convertimos la lista de tuplas (Persona, total) al schema
    reporte = [
        schemas.ReportePersonaCancelados(
            persona=persona_obj,
            total_cancelados=total
        )
        for persona_obj, total in resultados
    ]
    return reporte

# 5. Turnos confirmados en un período de tiempo (Paginado)
@app.get("/reportes/turnos-confirmados", response_model=List[schemas.TurnoOut])
def reporte_turnos_confirmados_paginado(
    desde: date = Query(..., description="Fecha de inicio (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha de fin (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Número de página"),
    size: int = Query(5, ge=1, le=100, description="Tamaño de la página"),
    db: Session = Depends(get_db)
):

    #Reporte 5: Devuelve turnos confirmados en un rango de fechas.
    #Los resultados están paginados (5 por página por defecto).

    # Este SÍ usa crud.buscar_turnos por la paginación
    skip = (page - 1) * size
    return crud.buscar_turnos(
        db,
        fecha_desde=desde,
        fecha_hasta=hasta,
        estado="confirmado",
        skip=skip,
        limit=size
    )

# 6. Personas habilitadas o inhabilitadas
@app.get("/reportes/estado-personas", response_model=List[schemas.PersonaOut])
def reporte_estado_personas(
    habilitada: bool = Query(..., description="True para habilitadas, False para inhabilitadas"),
    db: Session = Depends(get_db)
):

    #Reporte 6: Devuelve personas según su estado 'activo' (habilitada).

    # Lógica de la consulta DENTRO del endpoint
    personas = (
        db.query(Persona)
          .filter(Persona.activo == habilitada)
          .order_by(Persona.apellido.asc())
          .all()
    )
    return personas

"""