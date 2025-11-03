from fastapi import APIRouter

router = APIRouter()

@router.get("/", summary="List transactions")
def list_transactions():
    return {"message": "Transactions list"}

@router.get("/details/{id}", summary="Transaction details")
def transaction_details(id: int):
    return {"message": f"Transaction details for ID {id}"}

@router.post("/edit", summary="Add or edit a transaction")
def add_edit_transaction():
    return {"message": "Transaction added or edited"}
