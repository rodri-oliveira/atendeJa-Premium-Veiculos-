from fastapi import APIRouter, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.repositories.db import SessionLocal
from app.repositories import models as m

router = APIRouter()


@router.get("/veiculos")
def list_vehicles(
    categoria: Optional[str] = None,
    marca: Optional[str] = None,
    modelo: Optional[str] = None,
    ano_min: Optional[int] = None,
    ano_max: Optional[int] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
    limit: int = 12,
    offset: int = 0,
):
    try:
        with SessionLocal() as db:  # type: Session
            stmt = select(m.Vehicle).where(m.Vehicle.active == True)  # noqa: E712
            if categoria:
                stmt = stmt.where(m.Vehicle.category == categoria.upper())
            if marca:
                stmt = stmt.where(m.Vehicle.brand.ilike(f"%{marca}%"))
            if modelo:
                stmt = stmt.where(m.Vehicle.model.ilike(f"%{modelo}%"))
            if ano_min is not None:
                stmt = stmt.where(m.Vehicle.year >= int(ano_min))
            if ano_max is not None:
                stmt = stmt.where(m.Vehicle.year <= int(ano_max))
            if preco_min is not None:
                stmt = stmt.where(m.Vehicle.price >= float(preco_min))
            if preco_max is not None:
                stmt = stmt.where(m.Vehicle.price <= float(preco_max))
            stmt = stmt.order_by(m.Vehicle.id.desc()).limit(max(1, min(limit, 48))).offset(max(0, offset))
            rows = db.execute(stmt).scalars().all()
            return [
                {
                    "id": r.id,
                    "titulo": r.title,
                    "marca": r.brand,
                    "modelo": r.model,
                    "ano": r.year,
                    "categoria": r.category,
                    "preco": r.price,
                    "imagem": r.image_url,
                }
                for r in rows
            ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/veiculos/{vehicle_id}")
def get_vehicle(vehicle_id: int):
    try:
        with SessionLocal() as db:  # type: Session
            v = db.get(m.Vehicle, vehicle_id)
            if not v:
                raise HTTPException(status_code=404, detail="vehicle_not_found")
            return {
                "id": v.id,
                "titulo": v.title,
                "marca": v.brand,
                "modelo": v.model,
                "ano": v.year,
                "categoria": v.category,
                "preco": v.price,
                "imagem": v.image_url,
                "ativo": v.active,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
