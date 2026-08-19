import threading

from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from .models import BankAccount, Installment, Loan


def make_token(user_id):
    token = AccessToken()
    token["user_id"] = user_id
    return str(token)


def auth_client(user_id):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {make_token(user_id)}")
    return client


class AuthTests(TransactionTestCase):
    def test_endpoint_blocked_without_token(self):
        client = APIClient()  # no token — like Postman without auth
        response = client.get("/api/accounts/")
        self.assertEqual(response.status_code, 401)

    def test_endpoint_blocked_with_invalid_token(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
        response = client.get("/api/accounts/")
        self.assertEqual(response.status_code, 401)

    def test_endpoint_allowed_with_valid_token(self):
        response = auth_client(1).get("/api/accounts/")
        self.assertEqual(response.status_code, 200)


class LoanTests(TransactionTestCase):
    def setUp(self):
        self.client_a = auth_client(1)
        self.account = BankAccount.objects.create(user_id=1, balance=0)

    def test_create_loan_creates_two_installments(self):
        response = self.client_a.post(
            "/api/loans/", {"amount": "1000"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        loan = Loan.objects.get(pk=response.data["id"])
        self.assertEqual(loan.installments.count(), 2)
        self.assertEqual(sum(i.amount for i in loan.installments.all()), 1000)

    def test_loan_adds_to_balance(self):
        self.client_a.post("/api/loans/", {"amount": "1000"}, format="json")
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 1000)

    def test_negative_loan_rejected(self):
        response = self.client_a.post(
            "/api/loans/", {"amount": "-50"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_see_other_users_loans(self):
        self.client_a.post("/api/loans/", {"amount": "1000"}, format="json")
        response = auth_client(2).get("/api/loans/")
        self.assertEqual(response.data["count"] if "count" in response.data else len(response.data), 0)


class PaymentTests(TransactionTestCase):
    def setUp(self):
        self.client_a = auth_client(1)
        self.account = BankAccount.objects.create(user_id=1, balance=500)
        self.loan = Loan.objects.create(bank_account=self.account, amount=1000)
        self.inst1 = Installment.objects.create(loan=self.loan, amount=500)
        self.inst2 = Installment.objects.create(loan=self.loan, amount=500)

    def test_pay_installment_deducts_balance(self):
        response = self.client_a.post(f"/api/installments/{self.inst1.id}/pay/")
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 0)

    def test_pay_already_paid_rejected(self):
        self.client_a.post(f"/api/installments/{self.inst1.id}/pay/")
        response = self.client_a.post(f"/api/installments/{self.inst1.id}/pay/")
        self.assertEqual(response.status_code, 400)

    def test_insufficient_balance_rejected(self):
        self.account.balance = 100
        self.account.save()
        response = self.client_a.post(f"/api/installments/{self.inst1.id}/pay/")
        self.assertEqual(response.status_code, 400)
        self.inst1.refresh_from_db()
        self.assertEqual(self.inst1.status, Installment.STATUS_PENDING)

    def test_paying_all_installments_marks_loan_paid(self):
        self.account.balance = 1000
        self.account.save()
        self.client_a.post(f"/api/installments/{self.inst1.id}/pay/")
        self.client_a.post(f"/api/installments/{self.inst2.id}/pay/")
        self.loan.refresh_from_db()
        self.assertEqual(self.loan.status, Loan.STATUS_PAID)

    def test_concurrent_payment_no_double_spend(self):
        """Two threads pay installments at once; row locking must prevent
        the balance from going negative (double-spend)."""
        self.account.balance = 500
        self.account.save()
        results = []

        def pay(installment_id):
            client = auth_client(1)
            resp = client.post(f"/api/installments/{installment_id}/pay/")
            results.append(resp.status_code)

        t1 = threading.Thread(target=pay, args=(self.inst1.id,))
        t2 = threading.Thread(target=pay, args=(self.inst2.id,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Balance is 500; each installment costs 500 — only ONE can succeed
        self.assertEqual(sorted(results), [200, 400])
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, 0)
