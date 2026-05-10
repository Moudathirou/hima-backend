from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.stock import Stock

CATEGORIE_MAP = {
    "fournitures_scolaires": "fournitures_scolaires",
    "vetements": "vetements",
    "medicaments": "medicaments",
}


def decrement_stock(db: Session, categorie: str, quantite: int) -> None:
    items = (
        db.query(Stock)
        .filter(Stock.categorie == categorie, Stock.quantite > 0)
        .order_by(Stock.quantite.desc())
        .all()
    )
    if not items:
        return  # Pas de stock configuré — on autorise quand même la distribution

    remaining = quantite
    for item in items:
        if remaining <= 0:
            break
        deduct = min(item.quantite, remaining)
        item.quantite -= deduct
        remaining -= deduct

    if remaining > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuffisant pour la catégorie '{categorie}'. Manque {remaining} unité(s).",
        )
    db.flush()
