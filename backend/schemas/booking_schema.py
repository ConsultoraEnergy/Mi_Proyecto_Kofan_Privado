from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import List, Optional

class EstadoReserva(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    OCUPADA = "ocupada"
    CANCELADA = "cancelada"
    FINALIZADA = "finalizada"

class UpdateEstadoReserva(BaseModel):
    estado: EstadoReserva
    motivo_actualizacion: Optional[str] = None
    
# 1. Estructuras de Listas
class AcompananteSchema(BaseModel):
    nombre_completo: str
    tipo_documento: str 
    numero_documento: str
    parentesco: str

class ConsumoExtraSchema(BaseModel):
    concepto: str 
    valor: float

# 2. ESQUEMA BASE CON CAMPOS DE AUDITORÍA
class ReservaBase(BaseModel):
    habitacion_id: str
    fecha_entrada: date
    fecha_salida: date
    # 5.3: lo calcula SIEMPRE el backend (pricing_service); nunca se toma del cliente.
    monto_total: Optional[float] = None
    
    # 🟢 Toda reserva nace con estas listas vacías por defecto
    acompanantes: List[AcompananteSchema] = [] 
    consumos_extras: List[ConsumoExtraSchema] = []
    
    observaciones: Optional[str] = None
    estado: EstadoReserva = EstadoReserva.PENDIENTE
    # 5.6: clave interna del comprobante en almacenamiento privado (no es una URL pública).
    comprobante_archivo: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    actualizado_por: Optional[str] = None
    motivo_actualizacion: Optional[str] = None

# 3. PARA USUARIOS LOGUEADOS (Sacamos datos del Token)


# 4. PARA INVITADOS (El formulario de tu Vue.js público)
class ReservaPublicCreate(ReservaBase):
    tipo_persona: str 
    cliente_nombre: str 
    cliente_email: EmailStr 
    # 🟢 Valores por defecto para que no estalle si el turista no los envía
    tipo_documento: str = "Pendiente"
    cliente_documento: str = "0"
    cliente_celular: str = "" 

class ReservaCreate(ReservaPublicCreate):
    pass 

# 4b. RESERVA MANUAL DESDE EL PANEL (solo admin, JSON)
class ReservaAdminCreate(BaseModel):
    habitacion_id: str
    fecha_entrada: date
    fecha_salida: date
    cliente_nombre: str = Field(min_length=1)
    cliente_email: EmailStr
    cliente_celular: str = ""
    observaciones: Optional[str] = None
    # Opcional: el admin puede fijar un precio negociado. Si no se envía, se calcula.
    monto_total: Optional[float] = Field(default=None, gt=0)

# 5. ESQUEMA DE RESPUESTA (Lo que se envía al frontend)
class ReservaResponse(ReservaBase):
    id: str
    cliente_id: Optional[str] = None 
    cliente_nombre: Optional[str] = None
    cliente_email: Optional[EmailStr] = None
    cliente_celular: Optional[str] = None

# 6. ESQUEMA PARA EL CHECK-IN Y EDICIÓN (ADMIN)
class UpdateReservaDetalles(BaseModel):
    cliente_nombre: str
    cliente_email: str
    cliente_celular: str
    tipo_documento: str
    cliente_documento: str
    
    # 🟢 En string para que MongoDB lo acepte sin problemas
    fecha_entrada: str
    fecha_salida: str
    monto_total: float
    
    consumos_extras: List[ConsumoExtraSchema] = []
    acompanantes: List[AcompananteSchema] = []

