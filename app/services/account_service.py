# app/services/account_service.py

from sqlalchemy.orm import Session

from app.database.models import Account
from app.exception import AlreadyExistsError, NotFoundError
from app.utility import validate_non_empty_string, validate_non_negative_amount


class AccountService:
    """
    Service class for handling all operations related to account
    """

    def __init__(self, db_session: Session, currency_service) -> None:
        """
        Initialize AccountService.

        Args:
            db_session (Session): Database session.
            currency_service (CurrenyService): Service used for currency conversion.
        """
        self.db_session = db_session
        self.currency_service = currency_service

    def get_account(self, account_name: str) -> Account | None:
        """
        Retrieve an account by name.

        Args:
            account_name (str): The account name.

        Returns:
            Account | None: Account object if found, else None.
        """
        account_name = validate_non_empty_string(account_name, "Account name")
        return (
            self.db_session.query(Account).filter_by(account_name=account_name).first()
        )

    def get_all_accounts(self) -> list[Account]:
        """
        Retrieve all existing accounts.

        Returns:
            list[Account]: List of all Account objects.
        """
        return self.db_session.query(Account).all()

    def add_account(
        self, account_name: str, initial_balance: str, currency: str = "MYR"
    ) -> Account:
        """
        Add a new account with an initial balance.

        Args:
            account_name (str): Name of the new account.
            initial_balance (str | float | Decimal): Initial balance.
            currency (str): Currency code.

        Returns:
            Account: The newly created Account object.

        Raises:
            AlreadyExistsError: If an account with the same name exists.
            InvalidInputError: If inputs are invalid.
        """
        account_name = validate_non_empty_string(account_name, "Account name")
        balance_decimal = validate_non_negative_amount(
            initial_balance, "Initial balance"
        )

        # Convert to MYR if needed
        balance_in_myr = balance_decimal
        if self.currency_service and currency.upper() != "MYR":
            balance_in_myr = self.currency_service.convert_to_myr(
                balance_decimal, currency
            )

        # Check for duplicate
        if self.get_account(account_name):
            raise AlreadyExistsError(
                f"An account named '{account_name}' already exists."
            )

        # Create and save
        new_account = Account(account_name=account_name, balance=balance_in_myr)
        self.db_session.add(new_account)

        try:
            self.db_session.commit()
        except Exception:
            self.db_session.rollback()
            raise AlreadyExistsError(
                f"An account named '{account_name}' already exists."
            )

        return new_account

    def edit_account_name(self, old_name: str, new_name: str) -> Account:
        """
        Rename an existing account.

        Args:
            old_name (str): Current account name.
            new_name (str): New account name.

        Returns:
            Account: Updated Account object.

        Raises:
            InvalidInputError: If inputs are invalid.
            NotFoundError: If the old account does not exist.
            AlreadyExistsError: If the new name is already in use.
        """

        # Validate names
        old_name = validate_non_empty_string(old_name, "Old account name")
        new_name = validate_non_empty_string(new_name, "New account name")

        # Check if old name already exist
        account = self.get_account(old_name)
        if not account:
            raise NotFoundError(f"Account '{old_name}' does not exist.")

        # Check if new name already exists
        existing = self.get_account(new_name)
        if existing and existing.id != account.id:
            raise AlreadyExistsError(f"An account named '{new_name}' already exists.")

        # Update the account object's name and the dictionary key
        account.account_name = new_name
        self.db_session.commit()

        return account

    def delete_account(self, account_name: str) -> bool:
        """
        Delete an account and its associated transactions.

        Args:
            account_name (str): Name of the account to delete.

        Returns:
            bool: True if deletion is successful.

        Raises:
            NotFoundError: If the account does not exist.
            InvalidInputError: If inputs are invalid.
        """

        # Validate account name
        account_name = validate_non_empty_string(account_name, "Account name")

        # Retrieve the account object, raise error if not found
        account = self.get_account(account_name)
        if not account:
            raise NotFoundError(f"Account '{account_name}' does not exist.")

        # Remove all transactions associated with this account
        self.db_session.delete(account)
        self.db_session.commit()

        return True
