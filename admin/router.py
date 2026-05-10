import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.security import hash_password, verify_password
from database import get_db
from models.agent import Agent
from models.beneficiaire import Beneficiaire
from models.campaign import Campaign
from models.campaign_stock import CampaignStock
from models.cotisation import Cotisation
from models.distribution import Distribution
from models.don import Don
from models.foyer import Foyer

router = APIRouter()
templates = Jinja2Templates(directory="admin/templates")

# Sessions en mémoire : {session_id: agent_id}
_sessions: dict[str, int] = {}


def _get_session_agent(request: Request, db: Session) -> Optional[Agent]:
    sid = request.cookies.get("admin_session")
    if not sid or sid not in _sessions:
        return None
    agent_id = _sessions[sid]
    agent = db.query(Agent).filter(Agent.id == agent_id, Agent.is_active == True).first()
    if not agent or agent.role != "admin":
        _sessions.pop(sid, None)
        return None
    return agent


def _require_admin(request: Request, db: Session):
    agent = _get_session_agent(request, db)
    if not agent:
        raise RedirectResponse(url="/admin/login", status_code=302)
    return agent


# ── Login ──────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"session_agent": None, "error": None})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.username == username, Agent.is_active == True).first()
    if not agent or agent.role != "admin" or not verify_password(password, agent.hashed_password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"session_agent": None, "error": "Identifiants invalides ou accès non autorisé"},
            status_code=401,
        )
    sid = str(uuid.uuid4())
    _sessions[sid] = agent.id
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    response.set_cookie("admin_session", sid, httponly=True, samesite="lax", max_age=60 * 60 * 8)
    return response


@router.post("/logout")
def logout(request: Request):
    sid = request.cookies.get("admin_session")
    _sessions.pop(sid, None)
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


# ── Dashboard ──────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stats = {
        "nb_foyers": db.query(func.count(Foyer.id)).scalar() or 0,
        "nb_beneficiaires": db.query(func.count(Beneficiaire.id)).scalar() or 0,
        "distributions_ce_mois": db.query(func.count(Distribution.id)).filter(Distribution.date >= first_of_month).scalar() or 0,
        "dons_total": float(db.query(func.sum(Don.montant)).scalar() or 0),
        "cotisations_total": float(db.query(func.sum(Cotisation.montant)).scalar() or 0),
        "nb_agents_actifs": db.query(func.count(Agent.id)).filter(Agent.is_active == True, Agent.role == "agent").scalar() or 0,
    }

    islands = ["grande_comore", "anjouan", "moheli"]
    island_stats = []
    for island in islands:
        nb_foyers = db.query(func.count(Foyer.id)).filter(Foyer.island == island).scalar() or 0
        nb_distributions = (
            db.query(func.count(Distribution.id))
            .join(Foyer, Distribution.foyer_id == Foyer.id)
            .filter(Foyer.island == island)
            .scalar() or 0
        )
        island_stats.append({"island": island, "nb_foyers": nb_foyers, "nb_distributions": nb_distributions})

    # Campagne active (résumé)
    active_campaign = db.query(Campaign).filter(Campaign.status == "active").first()
    active_summary = None
    if active_campaign:
        nb_dist = db.query(func.count(Distribution.id)).filter(Distribution.campaign_id == active_campaign.id).scalar() or 0
        stocks = db.query(CampaignStock).filter(CampaignStock.campaign_id == active_campaign.id).all()
        active_summary = {
            "campaign": active_campaign,
            "nb_distributions": nb_dist,
            "stocks": stocks,
        }

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "session_agent": session_agent,
            "stats": stats,
            "island_stats": island_stats,
            "active_summary": active_summary,
        },
    )


# ── Campagnes ──────────────────────────────────────────────────────────────

CAMPAIGN_TYPES = [
    ("fournitures_scolaires", "Fournitures scolaires"),
    ("vetements", "Vêtements"),
    ("medicaments", "Médicaments"),
    ("autre", "Autre"),
]


def _campaign_type_label(type_: str) -> str:
    return dict(CAMPAIGN_TYPES).get(type_, type_)


@router.get("/campaigns", response_class=HTMLResponse)
def campaigns_page(
    request: Request,
    db: Session = Depends(get_db),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    campaigns = db.query(Campaign).order_by(Campaign.status.asc(), Campaign.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "campaigns.html",
        {
            "session_agent": session_agent,
            "campaigns": campaigns,
            "campaign_types": CAMPAIGN_TYPES,
            "type_label": _campaign_type_label,
            "success": success,
            "error": error,
        },
    )


@router.post("/campaigns/create")
def create_campaign_admin(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    if db.query(Campaign).filter(Campaign.status == "active").first():
        return RedirectResponse(
            url="/admin/campaigns?error=Une+campagne+est+d%C3%A9j%C3%A0+active",
            status_code=302,
        )
    if type not in {t[0] for t in CAMPAIGN_TYPES}:
        return RedirectResponse(url="/admin/campaigns?error=Type+invalide", status_code=302)

    c = Campaign(name=name, type=type, status="active", created_by_admin_id=session_agent.id)
    db.add(c)
    db.commit()
    return RedirectResponse(url=f"/admin/campaigns/{c.id}?success=Campagne+lanc%C3%A9e", status_code=302)


@router.get("/campaigns/{campaign_id}", response_class=HTMLResponse)
def campaign_detail(
    campaign_id: int,
    request: Request,
    db: Session = Depends(get_db),
    success: Optional[str] = None,
    error: Optional[str] = None,
):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        return RedirectResponse(url="/admin/campaigns?error=Campagne+introuvable", status_code=302)

    stocks = db.query(CampaignStock).filter(CampaignStock.campaign_id == campaign_id).all()
    distributions = (
        db.query(Distribution)
        .filter(Distribution.campaign_id == campaign_id)
        .order_by(Distribution.date.desc())
        .all()
    )
    new_foyers = (
        db.query(Foyer)
        .filter(Foyer.created_during_campaign_id == campaign_id)
        .order_by(Foyer.created_at.desc())
        .all()
    )
    # Map agents pour affichage
    agent_ids = {d.agent_id for d in distributions}
    agents_map = {a.id: a for a in db.query(Agent).filter(Agent.id.in_(agent_ids)).all()} if agent_ids else {}
    foyers_map = {f.id: f for f in db.query(Foyer).filter(Foyer.id.in_({d.foyer_id for d in distributions if d.foyer_id})).all()}
    benef_map = {
        b.id: b for b in db.query(Beneficiaire).filter(Beneficiaire.id.in_({d.beneficiaire_id for d in distributions if d.beneficiaire_id})).all()
    }

    return templates.TemplateResponse(
        request,
        "campaign_detail.html",
        {
            "session_agent": session_agent,
            "campaign": c,
            "type_label": _campaign_type_label(c.type),
            "stocks": stocks,
            "distributions": distributions,
            "new_foyers": new_foyers,
            "agents_map": agents_map,
            "foyers_map": foyers_map,
            "benef_map": benef_map,
            "success": success,
            "error": error,
        },
    )


@router.post("/campaigns/{campaign_id}/stock")
def upsert_stock_admin(
    campaign_id: int,
    request: Request,
    item_name: str = Form(...),
    quantite_initiale: int = Form(...),
    db: Session = Depends(get_db),
):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c or c.status != "active":
        return RedirectResponse(
            url=f"/admin/campaigns/{campaign_id}?error=Campagne+non+modifiable",
            status_code=302,
        )

    item = (
        db.query(CampaignStock)
        .filter(CampaignStock.campaign_id == campaign_id, CampaignStock.item_name == item_name)
        .first()
    )
    if item:
        item.quantite_initiale = quantite_initiale
    else:
        db.add(
            CampaignStock(
                campaign_id=campaign_id,
                item_name=item_name,
                quantite_initiale=quantite_initiale,
                quantite_distribuee=0,
            )
        )
    db.commit()
    return RedirectResponse(
        url=f"/admin/campaigns/{campaign_id}?success=Stock+mis+%C3%A0+jour",
        status_code=302,
    )


@router.post("/campaigns/{campaign_id}/close")
def close_campaign_admin(campaign_id: int, request: Request, db: Session = Depends(get_db)):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        return RedirectResponse(url="/admin/campaigns?error=Campagne+introuvable", status_code=302)
    if c.status != "active":
        return RedirectResponse(
            url=f"/admin/campaigns/{campaign_id}?error=D%C3%A9j%C3%A0+cl%C3%B4tur%C3%A9e",
            status_code=302,
        )
    c.status = "closed"
    c.closed_at = datetime.now(timezone.utc)
    c.closed_by_admin_id = session_agent.id
    db.commit()
    return RedirectResponse(
        url="/admin/campaigns?success=Campagne+termin%C3%A9e",
        status_code=302,
    )


# ── Agents ─────────────────────────────────────────────────────────────────

@router.get("/agents", response_class=HTMLResponse)
def agents_page(request: Request, db: Session = Depends(get_db), success: str = None, error: str = None):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    agents = db.query(Agent).order_by(Agent.role.desc(), Agent.full_name).all()
    return templates.TemplateResponse(
        request,
        "agents.html",
        {"session_agent": session_agent, "agents": agents, "success": success, "error": error},
    )


@router.post("/agents/create")
def create_agent(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    island: str = Form(""),
    village: str = Form(""),
    db: Session = Depends(get_db),
):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    if db.query(Agent).filter(Agent.username == username).first():
        agents = db.query(Agent).order_by(Agent.role.desc(), Agent.full_name).all()
        return templates.TemplateResponse(
            request,
            "agents.html",
            {
                "session_agent": session_agent,
                "agents": agents,
                "error": f"Le nom d'utilisateur '{username}' existe déjà.",
                "success": None,
            },
        )

    new_agent = Agent(
        username=username,
        hashed_password=hash_password(password),
        full_name=full_name,
        role="agent",
        island=island or None,
        village=village or None,
    )
    db.add(new_agent)
    db.commit()
    return RedirectResponse(url="/admin/agents?success=Compte+créé+avec+succès", status_code=302)


@router.post("/agents/{agent_id}/deactivate")
def deactivate_agent(agent_id: int, request: Request, db: Session = Depends(get_db)):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent and agent.id != session_agent.id:
        agent.is_active = False
        db.commit()
    return RedirectResponse(url="/admin/agents", status_code=302)


@router.post("/agents/{agent_id}/activate")
def activate_agent(agent_id: int, request: Request, db: Session = Depends(get_db)):
    session_agent = _get_session_agent(request, db)
    if not session_agent:
        return RedirectResponse(url="/admin/login", status_code=302)

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent:
        agent.is_active = True
        db.commit()
    return RedirectResponse(url="/admin/agents", status_code=302)


# ── Redirect root ──────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def admin_root(request: Request, db: Session = Depends(get_db)):
    if _get_session_agent(request, db):
        return RedirectResponse(url="/admin/dashboard", status_code=302)
    return RedirectResponse(url="/admin/login", status_code=302)
