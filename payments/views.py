from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Tariff, Payment
from .serializers import TariffSerializer, PaymentSerializer, CreatePaymentSerializer


class TariffListView(generics.ListAPIView):
    queryset = Tariff.objects.filter(is_active=True)
    serializer_class = TariffSerializer
    permission_classes = [permissions.AllowAny]


class PaymentHistoryView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.payments.select_related('tariff')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_payment(request):
    serializer = CreatePaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        tariff = Tariff.objects.get(id=serializer.validated_data['tariff_id'], is_active=True)
    except Tariff.DoesNotExist:
        return Response({'detail': 'Tarif topilmadi'}, status=status.HTTP_404_NOT_FOUND)

    provider = serializer.validated_data['provider']

    from django.conf import settings
    required = {'payme': settings.PAYME_MERCHANT_ID and settings.PAYME_SECRET,
                'click': settings.CLICK_SERVICE_ID and settings.CLICK_MERCHANT_ID and settings.CLICK_SECRET,
                'uzum': settings.UZUM_CHECKOUT_URL and settings.UZUM_LOGIN and settings.UZUM_PASSWORD}
    if not required.get(provider):
        return Response({'detail': 'Bu to‘lov tizimi hozircha ulanmagan. Boshqa usulni tanlang.'}, status=503)
    payment = Payment.objects.create(
        user=request.user,
        tariff=tariff,
        provider=provider,
        amount=tariff.price,
        duration_days=tariff.duration_days,
        status='pending',
    )

    payment_url = _build_payment_url(payment, provider)

    return Response({
        'payment_id': str(payment.id),
        'amount': str(payment.amount),
        'provider': provider,
        'payment_url': payment_url,
    }, status=status.HTTP_201_CREATED)


def _build_payment_url(payment, provider):
    import base64
    from urllib.parse import urlencode
    from django.conf import settings
    if provider == 'payme':
        params = f'm={settings.PAYME_MERCHANT_ID};ac.payment_id={payment.pk};a={int(payment.amount * 100)};c={settings.FRONTEND_URL}/payment/success'
        return 'https://checkout.paycom.uz/' + base64.b64encode(params.encode()).decode()
    if provider == 'click':
        return 'https://my.click.uz/services/pay?' + urlencode({
            'service_id': settings.CLICK_SERVICE_ID, 'merchant_id': settings.CLICK_MERCHANT_ID,
            'amount': str(payment.amount), 'transaction_param': str(payment.pk),
            'return_url': settings.FRONTEND_URL + '/payment/success',
        })
    return settings.UZUM_CHECKOUT_URL + '?' + urlencode({'account': str(payment.pk), 'amount': int(payment.amount * 100)})


from .webhooks import payme_webhook, click_webhook, uzum_webhook
