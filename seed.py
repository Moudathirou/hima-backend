"""
Script d'initialisation — à exécuter une seule fois.
Crée les 2 comptes administrateurs de l'association.

Usage : python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
import models  # noqa — enregistre tous les modèles

from core.security import hash_password
from models.agent import Agent

Base.metadata.create_all(bind=engine)

# ── Modifiez ces valeurs avant le premier lancement ──
ADMINS = [
    {
        "username": "Mouda",
        "full_name": "Moudathirou Ben Saindou",   # Remplacez par le vrai nom
        "password": "HimaChababi2024!",    # À changer après la première connexion
        "island": "Anjouan",
        "village": "Ngandzale",
    },
    {
        "username": "Safaoui",
        "full_name": "Safaoui Abderemane",   # Remplacez par le vrai nom
        "password": "HimaChababi2024!",    # À changer après la première connexion
        "island": "Anjouan",
        "village": "Ngandzale",
    },
]


def seed():
    db = SessionLocal()
    try:
        created = 0
        for data in ADMINS:
            existing = db.query(Agent).filter(Agent.username == data["username"]).first()
            if existing:
                print(f"  [OK] '{data['username']}' existe déjà — ignoré")
                continue
            agent = Agent(
                username=data["username"],
                hashed_password=hash_password(data["password"]),
                full_name=data["full_name"],
                role="admin",
                island=data["island"],
                village=data["village"],
                is_active=True,
            )
            db.add(agent)
            created += 1
            print(f"  [+] Admin '{data['username']}' ({data['full_name']}) créé")

        db.commit()
        print(f"\nTerminé : {created} compte(s) créé(s).")
        if created > 0:
            print("  ⚠️  Changez les mots de passe après la première connexion !")
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Hima Chababi — Initialisation des comptes admin ===\n")
    seed()
