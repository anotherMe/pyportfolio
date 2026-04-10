from typing import Optional

from lib.repo.accounts_repository import (
    add_account,
    get_all_accounts,
    get_account_by_name,
    delete_account,
)
from service.dtos import AccountDTO, AccountCreateDTO


class AccountsService:

    def get_all(self, session) -> list[AccountDTO]:
        return [AccountDTO.model_validate(a) for a in get_all_accounts(session)]

    def get_by_name(self, session, name: str) -> Optional[AccountDTO]:
        account = get_account_by_name(session, name)
        return AccountDTO.model_validate(account) if account else None

    def create(self, session, dto: AccountCreateDTO) -> AccountDTO:
        account = add_account(session, dto.name, dto.description)
        session.commit()
        return AccountDTO.model_validate(account)

    def delete(self, session, account_id: int) -> bool:
        result = delete_account(session, account_id)
        if result:
            session.commit()
        return result
