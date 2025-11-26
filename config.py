from dotenv import load_dotenv 
import os

load_dotenv() # Cargar variables de entorno desde el archivo .env

# Estados de turno desde variables de entorno

ESTADO_TURNO_CANCELADO = os.getenv("ESTADO_TURNO_CANCELADO", "cancelado")
ESTADO_TURNO_CONFIRMADO = os.getenv("ESTADO_TURNO_CONFIRMADO", "confirmado")
ESTADO_TURNO_ASISTIDO = os.getenv("ESTADO_TURNO_ASISTIDO", "asistido")
ESTADO_TURNO_PENDIENTE = os.getenv("ESTADO_TURNO_PENDIENTE", "pendiente")
