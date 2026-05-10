"""
Migration one-shot : introduire le concept de Campagne.

À exécuter une fois après mise à jour du code :
    cd backend && python -m migrations.add_campaigns

Ce script est idempotent : on peut le re-lancer, il vérifie l'état avant chaque modif.

Étapes :
1. Créer les tables `campaigns` et `campaign_stocks` (Base.metadata.create_all les crée déjà au démarrage,
   mais on les garde explicites ici en cas d'exécution sans démarrage de l'app).
2. Ajouter les colonnes manquantes aux tables existantes :
   - distributions.campaign_id
   - distributions.stock_item
   - distributions.signature_data
   - distribution_tokens.campaign_id
   - foyers.created_during_campaign_id
   - beneficiaires.created_during_campaign_id
3. Créer une campagne "Historique (avant migration)" avec status='closed' et y rattacher
   toutes les distributions et tokens existants.
"""
from datetime import datetime, timezone

from sqlalchemy import inspect, text

from database import Base, SessionLocal, engine
import models  # noqa: F401 - enregistre tous les modèles


def column_exists(connection, table: str, column: str) -> bool:
    insp = inspect(connection)
    return any(c["name"] == column for c in insp.get_columns(table))


def add_column(connection, table: str, column: str, ddl_type: str) -> None:
    if column_exists(connection, table, column):
        print(f"  · {table}.{column} déjà présent — ok")
        return
    print(f"  + ajout {table}.{column}")
    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))


def main() -> None:
    print("→ Création des tables manquantes (campaigns, campaign_stocks)...")
    Base.metadata.create_all(bind=engine)

    print("→ Ajout des colonnes manquantes...")
    with engine.begin() as conn:
        add_column(conn, "distributions", "campaign_id", "INTEGER")
        add_column(conn, "distributions", "stock_item", "VARCHAR")
        add_column(conn, "distributions", "signature_data", "TEXT")
        add_column(conn, "distribution_tokens", "campaign_id", "INTEGER")
        add_column(conn, "foyers", "created_during_campaign_id", "INTEGER")
        add_column(conn, "beneficiaires", "created_during_campaign_id", "INTEGER")

    print("→ Backfill : campagne 'Historique' pour les anciennes données...")
    db = SessionLocal()
    try:
        from models.campaign import Campaign
        from models.distribution import Distribution
        from models.distribution_token import DistributionToken

        # Y a-t-il des distributions ou tokens orphelins ?
        nb_orphan_dist = db.query(Distribution).filter(Distribution.campaign_id.is_(None)).count()
        nb_orphan_tok = db.query(DistributionToken).filter(DistributionToken.campaign_id.is_(None)).count()

        if nb_orphan_dist == 0 and nb_orphan_tok == 0:
            print("  · Aucune donnée orpheline — rien à backfiller.")
            return

        # Récupère ou crée la campagne historique
        hist = db.query(Campaign).filter(Campaign.name == "Historique (avant migration)").first()
        if not hist:
            hist = Campaign(
                name="Historique (avant migration)",
                type="autre",
                status="closed",
                closed_at=datetime.now(timezone.utc),
            )
            db.add(hist)
            db.flush()
            print(f"  + campagne historique créée (id={hist.id})")
        else:
            print(f"  · campagne historique existante (id={hist.id})")

        if nb_orphan_dist:
            db.query(Distribution).filter(Distribution.campaign_id.is_(None)).update(
                {Distribution.campaign_id: hist.id}, synchronize_session=False
            )
            print(f"  + {nb_orphan_dist} distributions rattachées")
        if nb_orphan_tok:
            db.query(DistributionToken).filter(DistributionToken.campaign_id.is_(None)).update(
                {DistributionToken.campaign_id: hist.id}, synchronize_session=False
            )
            print(f"  + {nb_orphan_tok} tokens rattachés")

        db.commit()
    finally:
        db.close()

    print("✓ Migration terminée.")


if __name__ == "__main__":
    main()
