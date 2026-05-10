import random
from sqlalchemy.orm import Session

from models.foyer import Foyer


def generate_fc_code(db: Session) -> str:
    for _ in range(100):
        code = f"FC-{random.randint(1000, 9999)}"
        if not db.query(Foyer).filter(Foyer.code == code).first():
            return code
    raise RuntimeError("Impossible de générer un code FC unique après 100 tentatives")
