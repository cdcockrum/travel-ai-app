from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/signup")
def signup(payload: dict) -> dict:
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password are required")
    return {"message": "signup stub", "email": email}


@router.post("/login")
def login(payload: dict) -> dict:
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password are required")
    return {"message": "login stub", "email": email, "token": "demo-token"}