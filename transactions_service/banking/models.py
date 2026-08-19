from django.db import models


class BankAccount(models.Model):
    user_id = models.IntegerField(unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Account of user {self.user_id} (balance: {self.balance})"


class Loan(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_PAID = "paid"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), (STATUS_PAID, "Paid")]

    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="loans"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)


class Installment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CHOICES = [(STATUS_PENDING, "Pending"), (STATUS_PAID, "Paid")]

    loan = models.ForeignKey(
        Loan, on_delete=models.CASCADE, related_name="installments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    paid_at = models.DateTimeField(null=True, blank=True)
