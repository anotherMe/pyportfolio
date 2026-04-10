from lib.database import write_to_db
from lib.models import Transaction
from lib.repo.transactions_repository import (
    add_transaction,
    get_all_transactions,
    get_transactions_for_position_list,
    delete_transaction,
)
from service.dtos import TransactionDTO, TransactionCreateDTO


class TransactionsService:

    def get_all(self, session, account=None) -> list[TransactionDTO]:
        return [TransactionDTO.from_model(t) for t in get_all_transactions(session, account)]

    def get_by_position(self, session, position_id: int) -> list[TransactionDTO]:
        return [TransactionDTO.from_model(t) for t in get_transactions_for_position_list(session, [position_id])]

    def get_by_type(self, session, trans_type, account=None) -> list[TransactionDTO]:
        transactions = get_all_transactions(session, account)
        return [TransactionDTO.from_model(t) for t in transactions if t.type == trans_type]

    def create(self, session, dto: TransactionCreateDTO) -> TransactionDTO:
        transaction = add_transaction(
            session,
            account_id=dto.account_id,
            position_id=dto.position_id,
            trans_type=dto.type,
            amount=dto.amount,
            date=dto.date,
            description=dto.description,
        )
        session.commit()
        return TransactionDTO.from_model(transaction)

    def update(self, session, transaction_id: int, dto: TransactionCreateDTO) -> TransactionDTO:
        transaction = session.get(Transaction, transaction_id)
        if transaction is None:
            raise ValueError(f"Transaction {transaction_id} not found")
        transaction.account_id = dto.account_id
        transaction.position_id = dto.position_id
        transaction.date = dto.date
        transaction.type = dto.type
        transaction.amount = write_to_db(dto.amount)
        transaction.description = dto.description
        session.commit()
        return TransactionDTO.from_model(transaction)

    def delete(self, session, transaction_id: int) -> bool:
        return delete_transaction(session, transaction_id)
