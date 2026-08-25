from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BankAccount, Installment, Loan
from .serializers import (
    BankAccountSerializer,
    InstallmentSerializer,
    LoanSerializer,
)


class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.filter(user_id=self.request.user.id)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)


class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    http_method_names = ["get", "post"]  # create + list/retrieve only

    def get_queryset(self):
        return Loan.objects.filter(
            bank_account__user_id=self.request.user.id
        ).prefetch_related("installments")

    @transaction.atomic
    def perform_create(self, serializer):
        account = BankAccount.objects.select_for_update().get(
            user_id=self.request.user.id
        )
        loan = serializer.save(bank_account=account)
        # Loan money is added to the balance
        account.balance += loan.amount
        account.save()
        # Auto-create the two installments
        half = loan.amount / 2
        Installment.objects.create(loan=loan, amount=half)
        Installment.objects.create(loan=loan, amount=loan.amount - half)


class InstallmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InstallmentSerializer

    def get_queryset(self):
        return Installment.objects.filter(
            loan__bank_account__user_id=self.request.user.id
        )

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        with transaction.atomic():
            installment = (
                Installment.objects.select_for_update()
                .filter(pk=pk, loan__bank_account__user_id=request.user.id)
                .first()
            )
            if installment is None:
                return Response(
                    {"detail": "Installment not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if installment.status == Installment.STATUS_PAID:
                return Response(
                    {"detail": "Installment already paid."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            account = BankAccount.objects.select_for_update().get(
                pk=installment.loan.bank_account_id
            )
            if account.balance < installment.amount:
                return Response(
                    {"detail": "Insufficient balance."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            account.balance -= installment.amount
            account.save()

            installment.status = Installment.STATUS_PAID
            installment.paid_at = timezone.now()
            installment.save()

            loan = installment.loan
            if not loan.installments.exclude(
                status=Installment.STATUS_PAID
            ).exists():
                loan.status = Loan.STATUS_PAID
                loan.save()

        return Response(InstallmentSerializer(installment).data)
