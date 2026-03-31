from pymongo import MongoClient
import os
from dotenv import load_dotenv


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

try:
    
    client = MongoClient(MONGO_URI)
    
    
    db = client["home_office_db"]
    
    
    client.admin.command('ping')
    print("Conexão com o MongoDB Atlas estabelecida com sucesso!")

except Exception as e:
    print(f"Erro ao conectar ao MongoDB: {e}")