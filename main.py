from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import db 
from passlib.context import CryptContext 
from bson.objectid import ObjectId
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import jwt
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer()


load_dotenv()


SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("Aviso Crítico: JWT_SECRET_KEY não foi encontrada no arquivo .env!")

ALGORITHM = "HS256"

app = FastAPI(title="API - VERIFIQ OS", description="Motor principal do sistema de gestão e segurança.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)
def criar_token(usuario_id: str):
    return jwt.encode({"usuario_id": usuario_id}, SECRET_KEY, algorithm=ALGORITHM)
def validar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("usuario_id")
    except:
        raise HTTPException(status_code=401, detail="Acesso negado. Crachá (Token) inválido.")
@app.get("/")
def home():
    return {"status": "API online e rodando perfeitamente!"}


class UsuarioCadastro(BaseModel):
    nome: str
    email: str
    senha: str

@app.post("/cadastro", status_code=201)
def cadastrar_usuario(usuario: UsuarioCadastro):
    # 1. Verifica no MongoDB se o email já está cadastrado
    usuario_existente = db["usuarios"].find_one({"email": usuario.email})
    if usuario_existente:
        
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado.")

    
    novo_usuario = {
        "nome": usuario.nome,
        "email": usuario.email,
        "senha": gerar_hash_senha(usuario.senha)
    }

    resultado = db["usuarios"].insert_one(novo_usuario)

    return {
        "mensagem": "Usuário cadastrado com sucesso!",
        "id_usuario": str(resultado.inserted_id)
    }

class UsuarioLogin(BaseModel):
    email: str
    senha: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def gerar_hash_senha(senha: str):
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str):
    return pwd_context.verify(senha_plana, senha_hash)

@app.post("/login")
def login(usuario: UsuarioLogin):
    
    usuario_db = db["usuarios"].find_one({"email": usuario.email})
    
    
    if not usuario_db or not verificar_senha(usuario.senha, usuario_db["senha"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    id_do_usuario = str(usuario_db["_id"])
    token_jwt = criar_token(id_do_usuario)
    
    return {
        "mensagem": "Login realizado com sucesso!",
        "token": token_jwt,
        "usuario": usuario_db["nome"]
    }
class Tarefa(BaseModel):
    titulo: str
    descricao: str
    status: str = "A Fazer"  # Valor padrão
    usuario_id: str

class AtualizarStatus(BaseModel):
    status: str

@app.post("/tarefas")
def criar_tarefa(tarefa: Tarefa, usuario_id: str = Depends(validar_token)):
    nova_tarefa = tarefa.model_dump()
    nova_tarefa["usuario_id"] = usuario_id 
    
    resultado = db["tarefas"].insert_one(nova_tarefa)
    return {"mensagem": "Tarefa criada!", "id": str(resultado.inserted_id)}

@app.get("/tarefas")
def listar_tarefas(usuario_id: str = Depends(validar_token)):
    
    tarefas_db = list(db["tarefas"].find({"usuario_id": usuario_id}))
    
    lista_tarefas = []
    for tarefa in tarefas_db:
        tarefa["_id"] = str(tarefa["_id"])
        lista_tarefas.append(tarefa)
        
    return lista_tarefas

@app.put("/tarefas/{tarefa_id}")
def atualizar_status_tarefa(tarefa_id: str, atualizacao: AtualizarStatus, usuario_id: str = Depends(validar_token)):
    
    resultado = db["tarefas"].update_one(
        {"_id": ObjectId(tarefa_id), "usuario_id": usuario_id}, 
        {"$set": {"status": atualizacao.status}}
    )
    
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada ou você não tem permissão para alterá-la.")
        
    return {"mensagem": f"Tarefa movida para: {atualizacao.status}"}
@app.delete("/tarefas/{tarefa_id}")
def deletar_tarefa(tarefa_id: str, usuario_id: str = Depends(validar_token)):

    resultado = db["tarefas"].delete_one(
        {"_id": ObjectId(tarefa_id), "usuario_id": usuario_id}
    )
    
    
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada ou você não tem permissão para excluí-la.")
        
    return {"mensagem": "Tarefa excluída com sucesso!"}