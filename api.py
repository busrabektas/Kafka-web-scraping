from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import List

import json

app = FastAPI()

def load_data_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# Veri modeli oluştur
class Product(BaseModel):
    name: str
    price: str
    description: str
    stock: str

@app.get("/", response_model=List[Product])
def home():
    data = load_data_from_json('/app/data/data.json')
    return data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
