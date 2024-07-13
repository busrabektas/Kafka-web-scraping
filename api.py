from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import List
import json
from fastapi.responses import JSONResponse


'''

This python file creates a simple web API using FastAPI, serving product data stored in a JSON file to clients that access the root endpoint ('/')

'''

#Initialize FastAPI application
app = FastAPI()


#Function to load data from JSON file 
def load_data_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

# Define data model using Pydantic
class Product(BaseModel):
    name: str
    price: str
    description: str
    stock: str

#Custom JSONResponse class to pretty-print JSON
class PrettyJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        return json.dumps(content, indent=2, ensure_ascii=False).encode("utf-8")

#Home endpoint definition
@app.get("/", response_model=List[Product], response_class=PrettyJSONResponse)
def home():
    #Load data from JSON file
    data = load_data_from_json('/app/data/data.json')
    return data

#Run the app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
