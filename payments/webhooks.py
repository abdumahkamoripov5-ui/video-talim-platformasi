"""Provider callbacks: authenticate before looking up an order, lock before state changes."""
import base64
import hashlib
import hmac
import time
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Payment


def basic_auth(request, login, secret):
    expected = 'Basic ' + base64.b64encode(f'{login}:{secret}'.encode()).decode()
    return bool(login and secret and hmac.compare_digest(request.headers.get('Authorization', ''), expected))


def order(pk, provider):
    try:
        return Payment.objects.select_for_update().get(pk=pk, provider=provider)
    except (Payment.DoesNotExist, ValueError, TypeError, ValidationError):
        return None


def millis():
    return int(time.time() * 1000)


def payme_result(payment):
    data = payment.provider_data
    return {'transaction': str(payment.pk), 'state': data.get('state', 1),
            'create_time': data.get('create_time', 0), 'perform_time': data.get('perform_time', 0),
            'cancel_time': data.get('cancel_time', 0), 'reason': data.get('reason')}


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
@transaction.atomic
def payme_webhook(request):
    data = request.data
    if not isinstance(data, dict):
        return Response({'error': 'Invalid request'}, status=400)
    def error(code, message):
        return Response({'jsonrpc': '2.0', 'id': data.get('id'), 'error': {'code': code, 'message': {'uz': message, 'ru': message, 'en': message}}})
    def result(value):
        return Response({'jsonrpc': '2.0', 'id': data.get('id'), 'result': value})
    if not basic_auth(request, 'Paycom', settings.PAYME_SECRET):
        return error(-32504, 'Unauthorized')
    params = data.get('params', {})
    if not isinstance(params, dict):
        return error(-32600, 'Invalid request')
    method = data.get('method')
    if method in {'CheckPerformTransaction', 'CreateTransaction'}:
        account = params.get('account', {})
        if not isinstance(account, dict):
            return error(-31050, 'Invalid account')
        payment = order(account.get('payment_id'), 'payme')
        if not payment:
            return error(-31050, 'Order not found')
        if params.get('amount') != int(payment.amount * 100):
            return error(-31001, 'Incorrect amount')
        if method == 'CheckPerformTransaction':
            return result({'allow': True}) if payment.status == 'pending' else error(-31008, 'Order closed')
        if not isinstance(params.get('id'), str) or not isinstance(params.get('time'), int):
            return error(-32600, 'Invalid transaction')
        if payment.external_id and payment.external_id != params['id']:
            return error(-31008, 'Transaction exists')
        if payment.status != 'pending' and not (payment.status == 'paid' and payment.external_id == params['id']):
            return error(-31008, 'Order closed')
        if Payment.objects.filter(provider='payme', external_id=params['id']).exclude(pk=payment.pk).exists():
            return error(-31008, 'Transaction already exists')
        if not payment.external_id:
            payment.external_id = params['id']
            payment.provider_data = {'create_time': millis(), 'provider_time': params['time'], 'state': 1}
            payment.save(update_fields=['external_id', 'provider_data'])
        return result(payme_result(payment))
    if method == 'GetStatement':
        start, end = params.get('from'), params.get('to')
        if not isinstance(start, int) or not isinstance(end, int):
            return error(-32600, 'Invalid period')
        records = Payment.objects.filter(provider='payme').exclude(external_id='')
        return result({'transactions': [{**payme_result(p), 'id': p.external_id,
            'time': p.provider_data['provider_time'], 'amount': int(p.amount * 100),
            'account': {'payment_id': str(p.pk)}} for p in records
            if start <= p.provider_data.get('provider_time', 0) <= end]})
    if method not in {'PerformTransaction', 'CheckTransaction', 'CancelTransaction'}:
        return error(-32601, 'Method not found')
    payment = Payment.objects.select_for_update().filter(provider='payme', external_id=params.get('id') or '__missing__').first()
    if not payment:
        return error(-31003, 'Transaction not found')
    if method == 'PerformTransaction':
        if payment.status == 'pending' and millis() - payment.provider_data['create_time'] > 43200000:
            payment.status = 'cancelled'
            payment.provider_data.update(state=-1, cancel_time=millis(), reason=4)
            payment.save(update_fields=['status', 'provider_data'])
        if payment.status not in {'pending', 'paid'}:
            return error(-31008, 'Order closed')
        if payment.activate_subscription():
            payment.provider_data.update(state=2, perform_time=int(payment.paid_at.timestamp() * 1000))
            payment.save(update_fields=['provider_data'])
    if method == 'CancelTransaction':
        if payment.status == 'paid':
            return error(-31007, 'Subscription already provided; contact support for refund')
        payment.status = 'cancelled'
        payment.provider_data.update(state=-1, cancel_time=payment.provider_data.get('cancel_time') or millis(), reason=params.get('reason'))
        payment.save(update_fields=['status', 'provider_data'])
    return result(payme_result(payment))


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
@transaction.atomic
def click_webhook(request):
    data = request.data
    if not isinstance(data, dict):
        return Response({'error': -8, 'error_note': 'Invalid request'}, status=400)
    def response(code, note, payment=None):
        body = {'error': code, 'error_note': note, 'click_trans_id': data.get('click_trans_id'), 'merchant_trans_id': data.get('merchant_trans_id')}
        if payment:
            body['merchant_prepare_id' if str(data.get('action')) == '0' else 'merchant_confirm_id'] = str(payment.pk)
        return Response(body)
    action = str(data.get('action', ''))
    if action not in {'0', '1'}:
        return response(-3, 'Invalid action')
    if not settings.CLICK_SECRET or str(data.get('service_id')) != settings.CLICK_SERVICE_ID:
        return response(-1, 'Unauthorized')
    required = ['click_trans_id', 'service_id', 'merchant_trans_id', 'amount', 'sign_time', 'sign_string', 'error']
    if any(k not in data for k in required):
        return response(-8, 'Missing parameter')
    raw = str(data['click_trans_id']) + str(data['service_id']) + settings.CLICK_SECRET + str(data['merchant_trans_id'])
    if action == '1':
        raw += str(data.get('merchant_prepare_id', ''))
    raw += str(data['amount']) + action + str(data['sign_time'])
    if not hmac.compare_digest(hashlib.md5(raw.encode()).hexdigest(), str(data['sign_string'])):
        return response(-1, 'Invalid signature')
    payment = order(data['merchant_trans_id'], 'click')
    if not payment:
        return response(-5, 'Order not found')
    try:
        if Decimal(str(data['amount'])) != payment.amount:
            return response(-2, 'Incorrect amount')
        provider_error = int(data['error'])
    except (InvalidOperation, ValueError, TypeError):
        return response(-8, 'Invalid parameter')
    if payment.external_id and payment.external_id != str(data['click_trans_id']):
        return response(-4, 'Transaction already exists')
    if action == '1' and (str(data.get('merchant_prepare_id')) != str(payment.pk) or not payment.external_id):
        return response(-6, 'Prepare transaction not found')
    if payment.status == 'paid':
        return response(-4, 'Already paid', payment)
    if payment.status != 'pending':
        return response(-9, 'Transaction cancelled')
    if provider_error != 0:
        payment.status = 'cancelled'
        payment.save(update_fields=['status'])
        return response(-9, 'Transaction cancelled')
    payment.external_id = str(data['click_trans_id'])
    payment.save(update_fields=['external_id'])
    if action == '1':
        payment.activate_subscription()
    return response(0, 'Success', payment)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
@transaction.atomic
def uzum_webhook(request, action):
    data = request.data
    if not isinstance(data, dict):
        return Response({'errorCode': 'INVALID_REQUEST'}, status=400)
    if not basic_auth(request, settings.UZUM_LOGIN, settings.UZUM_PASSWORD):
        return Response({'errorCode': 'UNAUTHORIZED'}, status=401)
    if str(data.get('serviceId')) != settings.UZUM_SERVICE_ID:
        return Response({'errorCode': 'SERVICE_NOT_FOUND'}, status=400)
    if action not in {'check', 'create', 'confirm', 'reverse', 'status'}:
        return Response({'errorCode': 'METHOD_NOT_FOUND'}, status=400)
    if action in {'check', 'create'}:
        payment = order(data.get('params', {}).get('account'), 'uzum')
    else:
        payment = Payment.objects.select_for_update().filter(provider='uzum', external_id=data.get('transId') or '__missing__').first()
    if not payment:
        return Response({'errorCode': 'ACCOUNT_NOT_FOUND'}, status=400)
    if action == 'create':
        if data.get('amount') != int(payment.amount * 100) or not data.get('transId'):
            return Response({'errorCode': 'INVALID_AMOUNT'}, status=400)
        if payment.status != 'pending' or (payment.external_id and payment.external_id != data['transId']):
            return Response({'errorCode': 'TRANSACTION_ALREADY_EXISTS'}, status=400)
        payment.external_id = data['transId']
        payment.save(update_fields=['external_id'])
    if action == 'confirm':
        if payment.status not in {'pending', 'paid'}:
            return Response({'errorCode': 'TRANSACTION_CANCELLED'}, status=400)
        payment.activate_subscription()
    if action == 'reverse':
        if payment.status == 'paid':
            return Response({'errorCode': 'TRANSACTION_ALREADY_CONFIRMED'}, status=400)
        payment.status = 'cancelled'
        payment.save(update_fields=['status'])
    state = {'pending': 'CREATED', 'paid': 'CONFIRMED', 'cancelled': 'REVERSED', 'failed': 'FAILED'}[payment.status]
    return Response({'serviceId': data['serviceId'], 'timestamp': millis(), 'transId': payment.external_id,
        'status': 'OK' if action == 'check' else state, 'transTime': int(payment.created_at.timestamp()*1000),
        'amount': int(payment.amount*100), 'data': {'account': {'value': str(payment.pk)}, 'fio': {'value': payment.user.full_name}}})
