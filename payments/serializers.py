from rest_framework import serializers
from .models import Tariff, Payment


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ('id', 'name', 'description', 'price', 'duration_days', 'order')


class PaymentSerializer(serializers.ModelSerializer):
    tariff_name = serializers.CharField(source='tariff.name', read_only=True)
    provider_display = serializers.CharField(source='get_provider_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'tariff', 'tariff_name', 'provider', 'provider_display',
            'amount', 'status', 'status_display', 'created_at', 'paid_at',
        )
        read_only_fields = ('id', 'amount', 'status', 'created_at', 'paid_at')


class CreatePaymentSerializer(serializers.Serializer):
    tariff_id = serializers.IntegerField()
    provider = serializers.ChoiceField(choices=['payme', 'click', 'uzum'])
