from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import db 
from passlib.context import CryptContext 
from bson.objectid import ObjectId
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API - Home Office OS", description="Motor principal do sistema de gestão e segurança.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite que qualquer front-end acesse. (No futuro, colocamos o link real do site aqui)
    allow_credentials=True,
    allow_methods=["*"],  # Permite POST, GET, PUT, DELETE
    allow_headers=["*"],
)

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

class AtualizarStatus(BaseModel):
    status: str

@app.post("/tarefas")
def criar_tarefa(tarefa: Tarefa):
    nova_tarefa = tarefa.model_dump()
    resultado = db["tarefas"].insert_one(nova_tarefa)
    return {"mensagem": "Tarefa criada!", "id": str(resultado.inserted_id)}

@app.get("/tarefas/{usuario_id}")
def listar_tarefas(usuario_id: str):
    # 1. Busca no banco todas as tarefas que tenham este usuario_id
    tarefas_db = list(db["tarefas"].find({"usuario_id": usuario_id}))
    
    # 2. Formata a lista para o front-end entender 
    lista_tarefas = []
    for tarefa in tarefas_db:
        tarefa["_id"] = str(tarefa["_id"])
        lista_tarefas.append(tarefa)
        
    return lista_tarefas

@app.put("/tarefas/{tarefa_id}")
def atualizar_status_tarefa(tarefa_id: str, atualizacao: AtualizarStatus):
    # 1. Manda o MongoDB procurar a tarefa pelo ID e atualizar o campo "status"
    resultado = db["tarefas"].update_one(
        {"_id": ObjectId(tarefa_id)}, 
        {"$set": {"status": atualizacao.status}}
    )
    
    # 2. Verifica se a tarefa realmente existia
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
        
    return {"mensagem": f"Tarefa movida para: {atualizacao.status}"}

@app.delete("/tarefas/{tarefa_id}")
def deletar_tarefa(tarefa_id: str):
    # Pede para o MongoDB deletar o documento com este ID
    resultado = db["tarefas"].delete_one({"_id": ObjectId(tarefa_id)})
    
    # Se ele não deletou nada (deleted_count == 0), a tarefa não existia
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
        
    return {"mensagem": "Tarefa excluída com sucesso!"}