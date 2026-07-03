# app.py
from fastapi import FastAPI, HTTPException
import requests

app = FastAPI()

@app.get("/generate")
async def generate(prompt: str):
    try:
        response = requests.post(
            "http://localhost:1234/generate",  # API do LM Studio
            json={"prompt": prompt}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erro no servidor")
        return {"response": response.json()["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
