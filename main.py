from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import models  # noqa: F401 — force registration of all models
from database import Base, engine
from routers import auth, foyers, beneficiaires, distributions, distribution_tokens, stock, dons, cotisations, rapports, campaigns
from admin.router import router as admin_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hima Chababi API",
    description="Backend de l'association comorienne Hima Chababi",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files pour l'interface admin
app.mount("/admin/static", StaticFiles(directory="admin/static"), name="admin_static")

# API routes
app.include_router(auth.router, prefix="/auth", tags=["Authentification"])
app.include_router(foyers.router, prefix="/foyers", tags=["Foyers"])
app.include_router(beneficiaires.router, prefix="/beneficiaires", tags=["Bénéficiaires"])
app.include_router(distributions.router, prefix="/distributions", tags=["Distributions"])
app.include_router(distribution_tokens.router, prefix="/distribution-tokens", tags=["Tokens QR"])
app.include_router(stock.router, prefix="/stock", tags=["Stock"])
app.include_router(dons.router, prefix="/dons", tags=["Dons"])
app.include_router(cotisations.router, prefix="/cotisations", tags=["Cotisations"])
app.include_router(rapports.router, prefix="/rapports", tags=["Rapports"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["Campagnes"])

# Interface admin web
app.include_router(admin_router, prefix="/admin", tags=["Admin Web"])


@app.get("/", include_in_schema=False)
def root():
    return {"message": "Hima Chababi API — /docs pour la documentation, /admin pour l'interface admin"}
