from lib.database import write_to_db
from lib.enums import TransactionType
from lib.models import Trade, Position
from lib.repo.trades_repository import (
    add_trade,
    get_all_trades,
    get_all_trades_by_account,
    get_trades_for_position_list,
    delete_trade,
)
from lib.repo.transactions_repository import add_transaction
from service.dtos import TradeDTO, TradeCreateDTO


class TradesService:

    def get_all(self, session) -> list[TradeDTO]:
        return [TradeDTO.from_model(t) for t in get_all_trades(session)]

    def get_by_account(self, session, account) -> list[TradeDTO]:
        return [TradeDTO.from_model(t) for t in get_all_trades_by_account(session, account)]

    def get_by_position(self, session, position_id: int) -> list[TradeDTO]:
        return [TradeDTO.from_model(t) for t in get_trades_for_position_list(session, [position_id])]

    def create(self, session, dto: TradeCreateDTO) -> TradeDTO:
        trade = add_trade(
            session,
            position_id=dto.position_id,
            date=dto.date,
            trade_type=dto.type,
            quantity=dto.quantity,
            price=dto.price,
            description=dto.description,
        )
        if dto.fee > 0:
            position = session.get(Position, dto.position_id)
            add_transaction(
                session,
                account_id=position.account_id,
                position_id=dto.position_id,
                trans_type=TransactionType.FEE,
                amount=dto.fee,
                date=dto.date,
                description=f"Fee for {dto.type.value}ing {dto.quantity} units",
            )
        session.commit()
        return TradeDTO.from_model(trade)

    def update(self, session, trade_id: int, dto: TradeCreateDTO) -> TradeDTO:
        trade = session.get(Trade, trade_id)
        if trade is None:
            raise ValueError(f"Trade {trade_id} not found")
        trade.position_id = dto.position_id
        trade.date = dto.date
        trade.type = dto.type
        trade.quantity = dto.quantity
        trade.price = write_to_db(dto.price)
        trade.description = dto.description
        session.commit()
        return TradeDTO.from_model(trade)

    def delete(self, session, trade_id: int) -> bool:
        result = delete_trade(session, trade_id)
        if result:
            session.commit()
        return result
