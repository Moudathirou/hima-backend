from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.auth import get_current_agent, require_admin
from database import get_db
from models.stock import Stock
from schemas.stock import StockCreate, StockRead, StockUpdate

router = APIRouter()


@router.get("", response_model=List[StockRead])
def list_stock(db: Session = Depends(get_db), _=Depends(get_current_agent)):
    return db.query(Stock).order_by(Stock.categorie, Stock.nom).all()


@router.get("/alerts", response_model=List[StockRead])
def stock_alerts(db: Session = Depends(get_db), _=Depends(get_current_agent)):
    return db.query(Stock).filter(Stock.quantite <= Stock.seuil_alerte).all()


@router.post("", response_model=StockRead, status_code=201)
def create_stock(data: StockCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    item = Stock(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{stock_id}", response_model=StockRead)
def update_stock(stock_id: int, data: StockUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    item = db.query(Stock).filter(Stock.id == stock_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Article introuvable")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item
