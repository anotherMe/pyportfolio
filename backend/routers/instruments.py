
from fastapi.params import Depends
from sqlalchemy.orm import Session
from lib.database import get_session
from fastapi import APIRouter
from lib.repo.instruments_repository import get_all_instruments
from schemas.instrument import InstrumentRead
from typing import List


router = APIRouter()

@router.get("/", response_model=List[InstrumentRead], summary="List instruments")
def list_instruments(session: Session = Depends(get_session)):
    return get_all_instruments(session)

@router.get("/details/{id}", summary="Instrument details")
def instrument_details(id: int, session: Session = Depends(get_session)):
    return {"message": f"Instrument details for ID {id}"}

@router.post("/edit", summary="Add or edit a instrument")
def add_edit_instrument(session: Session = Depends(get_session)):
    return {"message": "Instrument added or edited"}