from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import db 
from passlib.context import CryptContext 
app = FastAPI(title="API - Home Office OS", description="Motor principal do sistema de gestão e segurança.")


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
    
    
    return {
        "mensagem": "Login realizado com sucesso!",
        "usuario": {
            "id": str(usuario_db["_id"]),
            "nome": usuario_db["nome"],
            "email": usuario_db["email"]
        }
    }
class Tarefa(BaseModel):
    titulo: str
    descricao: str
    status: str = "A Fazer"  # Valor padrão
    usuario_id: str

@app.post("/tarefas")
def criar_tarefa(tarefa: Tarefa):
    nova_tarefa = tarefa.model_dump()
    resultado = db["tarefas"].insert_one(nova_tarefa)
    return {"mensagem": "Tarefa criada!", "id": str(resultado.inserted_id)}