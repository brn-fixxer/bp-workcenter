from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import date
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Session
import os

# ── DB setup ──────────────────────────────────────────────
DATABASE_URL = "sqlite:///./notas.db"
engine = sa.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

class Base(DeclarativeBase):
    pass

class NotaDB(Base):
    __tablename__ = "notas"
    id          = sa.Column(sa.Integer, primary_key=True, index=True)
    titulo      = sa.Column(sa.String, nullable=False)
    descripcion = sa.Column(sa.String, default="")
    fecha       = sa.Column(sa.String, default=str(date.today()))
    estado      = sa.Column(sa.String, default="Hoy")        # Hoy | Esta semana | En espera | Cerrado
    categoria   = sa.Column(sa.String, default="General")    # Reuniones, Procesos, Alertas, etc.
    fijado      = sa.Column(sa.Boolean, default=False)

Base.metadata.create_all(bind=engine)

# ── Schemas ───────────────────────────────────────────────
class NotaCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = ""
    fecha: Optional[str] = str(date.today())
    estado: Optional[str] = "Hoy"
    categoria: Optional[str] = "General"
    fijado: Optional[bool] = False

class NotaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha: Optional[str] = None
    estado: Optional[str] = None
    categoria: Optional[str] = None
    fijado: Optional[bool] = None

class NotaOut(NotaCreate):
    id: int
    class Config:
        from_attributes = True

# ── App ───────────────────────────────────────────────────
app = FastAPI(title="Sistema de Notas Post-it")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

def get_db():
    with Session(engine) as session:
        yield session

# ── Endpoints ─────────────────────────────────────────────
@app.get("/notas", response_model=list[NotaOut])
def leer_notas(estado: Optional[str] = None, categoria: Optional[str] = None):
    with Session(engine) as db:
        q = db.query(NotaDB)
        if estado:
            q = q.filter(NotaDB.estado == estado)
        if categoria:
            q = q.filter(NotaDB.categoria == categoria)
        notas = q.order_by(NotaDB.fijado.desc(), NotaDB.id.desc()).all()
        return notas

@app.post("/notas", response_model=NotaOut, status_code=201)
def crear_nota(nota: NotaCreate):
    with Session(engine) as db:
        nueva = NotaDB(**nota.model_dump())
        db.add(nueva)
        db.commit()
        db.refresh(nueva)
        return nueva

@app.patch("/notas/{nota_id}", response_model=NotaOut)
def actualizar_nota(nota_id: int, cambios: NotaUpdate):
    with Session(engine) as db:
        nota = db.get(NotaDB, nota_id)
        if not nota:
            raise HTTPException(404, "Nota no encontrada")
        for field, value in cambios.model_dump(exclude_unset=True).items():
            setattr(nota, field, value)
        db.commit()
        db.refresh(nota)
        return nota

@app.delete("/notas/{nota_id}", status_code=204)
def eliminar_nota(nota_id: int):
    with Session(engine) as db:
        nota = db.get(NotaDB, nota_id)
        if not nota:
            raise HTTPException(404, "Nota no encontrada")
        db.delete(nota)
        db.commit()

# Sirve el frontend
if os.path.exists("index.html"):
    @app.get("/")
    def root():
        return FileResponse("index.html")