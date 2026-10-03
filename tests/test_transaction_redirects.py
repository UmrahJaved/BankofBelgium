import unittest
from unittest.mock import patch

from banking_app.app import create_app
from banking_app.models import User


class TransactionRedirectTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.app.login_manager.session_protection = None

        @self.app.login_manager.user_loader
        def load_user(user_id):
            return User(
                {
                    "id": user_id,
                    "username": "testuser",
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                    "phone": None,
                    "address": None,
                    "date_of_birth": None,
                    "is_active": 1,
                }
            )

        self.client = self.app.test_client()

    @patch("banking_app.routes.account.create_transaction")
    @patch("banking_app.routes.account.update_account_balance")
    @patch("banking_app.routes.account.debit_account_for_transfer")
    @patch("banking_app.routes.account.get_account_by_iban")
    @patch("banking_app.routes.account.get_recent_user_transactions")
    @patch("banking_app.routes.account.get_user_accounts")
    def test_transfer_post_redirects_to_dashboard(
        self,
        mock_accounts,
        mock_recent_tx,
        mock_get_iban,
        mock_debit,
        mock_update_bal,
        mock_create_tx,
    ):
        mock_accounts.return_value = [
            {"id": "acc-1", "user_id": "test-user", "iban": "BE11111111111111", "account_type": "Checking", "balance": 1000.0}
        ]
        mock_recent_tx.return_value = []
        mock_get_iban.return_value = {
            "id": "acc-2",
            "user_id": "other-user",
            "iban": "BE12345678901234",
            "owner_first_name": "Jane",
            "owner_last_name": "Doe",
        }
        mock_debit.return_value = True

        with self.client.session_transaction() as session:
            session["_user_id"] = "test-user"
            session["_fresh"] = True

        response = self.client.post(
            "/transfer",
            data={
                "from_account": "acc-1",
                "account_number": "BE12345678901234",
                "recipient": "Jane Doe",
                "amount": "50",
                "description": "Test transfer",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/dashboard")

    @patch("banking_app.routes.account.create_transaction")
    @patch("banking_app.routes.account.update_account_balance")
    @patch("banking_app.routes.account.get_user_accounts")
    def test_deposit_post_redirects_to_dashboard(
        self,
        mock_accounts,
        mock_update_bal,
        mock_create_tx,
    ):
        mock_accounts.return_value = [
            {"id": "acc-1", "user_id": "test-user", "iban": "BE11111111111111", "account_type": "Checking"}
        ]

        with self.client.session_transaction() as session:
            session["_user_id"] = "test-user"
            session["_fresh"] = True

        response = self.client.post(
            "/deposit",
            data={
                "account_id": "acc-1",
                "amount": "75",
                "description": "Test deposit",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/dashboard")


if __name__ == "__main__":
    unittest.main()
