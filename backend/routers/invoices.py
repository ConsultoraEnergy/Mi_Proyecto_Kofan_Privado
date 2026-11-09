from fastapi import APIRouter, Depends, HTTPException, status
from backend.db.client import db
from bson import ObjectId
from datetime import datetime
from backend.dependencies.auth import required_admin
from backend.models.invoice_models import InvoiceCreate, AddExtraCharge, InvoiceSyncUpdate
from backend.schemas.invoice_schema import invoice_schema

# 5.1: la dependencia DEBE ir dentro de APIRouter(...) para aplicarse a todas las rutas.
router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
    dependencies=[Depends(required_admin)],
)

# ==========================================
# RUTAS
# ==========================================

# Buscar factura por ID de reserva
@router.get("/by-booking/{booking_id}")
async def get_invoice_by_booking(booking_id: str):
    invoice = await db.invoices.find_one({"booking_id": booking_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada para esta reserva")
    return invoice_schema(invoice)

# Crear una factura nueva
@router.post("/")
async def create_invoice(invoice: InvoiceCreate):
    invoice_dict = invoice.dict()
    invoice_dict["total_amount"] = invoice_dict["room_subtotal"] 
    
    result = await db.invoices.insert_one(invoice_dict)
    new_invoice = await db.invoices.find_one({"_id": result.inserted_id})
    return invoice_schema(new_invoice)

# Agregar un consumo extra individual
@router.put("/{invoice_id}/extra-charges")
async def add_extra_charge(invoice_id: str, charge: AddExtraCharge):
    invoice = await db.invoices.find_one({"_id": ObjectId(invoice_id)})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
        
    if invoice.get("status") == "closed":
        raise HTTPException(status_code=400, detail="No se pueden agregar consumos a una factura cerrada")

    new_charge = {
        "description": charge.description,
        "amount": charge.amount,
        "date": datetime.utcnow()
    }

    new_total = invoice.get("total_amount", 0) + charge.amount

    await db.invoices.update_one(
        {"_id": ObjectId(invoice_id)},
        {
            "$push": {"extra_charges": new_charge},
            "$set": {"total_amount": new_total}
        }
    )

    updated_invoice = await db.invoices.find_one({"_id": ObjectId(invoice_id)})
    return invoice_schema(updated_invoice)

# Sincronización Masiva desde el Modal
@router.put("/sync-by-booking/{booking_id}")
async def sync_invoice_with_booking(booking_id: str, update_data: InvoiceSyncUpdate):
    invoice = await db.invoices.find_one({"booking_id": booking_id})
    
    if not invoice:
        return {"message": "No invoice exists yet. Skipping sync."}
        
    if invoice.get("status") == "closed":
        raise HTTPException(status_code=400, detail="No se puede modificar una factura que ya está cerrada/pagada.")

    formatted_charges = []
    for charge in update_data.extra_charges:
        formatted_charges.append({
            "description": charge.get("concepto", charge.get("description", "")),
            "amount": float(charge.get("valor", charge.get("amount", 0))),
            "date": charge.get("fecha", charge.get("date", datetime.utcnow()))
        })

    await db.invoices.update_one(
        {"booking_id": booking_id},
        {
            "$set": {
                "check_out_date": update_data.check_out_date,
                "room_subtotal": update_data.room_subtotal,
                "total_amount": update_data.total_amount,
                "extra_charges": formatted_charges
            }
        }
    )

    updated_invoice = await db.invoices.find_one({"booking_id": booking_id})
    return invoice_schema(updated_invoice)

# Cerrar Factura (Check-out)
@router.put("/close-by-booking/{booking_id}")
async def close_invoice_by_booking(booking_id: str):
    invoice = await db.invoices.find_one({"booking_id": booking_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada para esta reserva")
    
    await db.invoices.update_one(
        {"booking_id": booking_id},
        {"$set": {"status": "closed"}}
    )
    
    return {"message": "Factura cerrada exitosamente"}