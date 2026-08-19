from rest_framework import serializers

from .models import BankAccount, Installment, Loan


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = ["id", "user_id", "balance", "created_at"]
        read_only_fields = ["user_id", "created_at"]


class InstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Installment
        fields = ["id", "loan", "amount", "status", "paid_at"]
        read_only_fields = ["loan", "amount", "status", "paid_at"]


class LoanSerializer(serializers.ModelSerializer):
    installments = InstallmentSerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = ["id", "amount", "status", "installments", "created_at"]
        read_only_fields = ["status", "created_at"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Loan amount must be positive.")
        return value