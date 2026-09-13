import requests
import json
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

def generate_sslcommerz_payment(request,order):

    post_body = {}
    post_body['store_id'] = settings.SSLCOMMERZ_STORE_ID
    post_body['store_passw'] = settings.SSLCOMMERZ_STORE_PASSWORD
    post_body['total_amount'] = float(order.get_total_cost())
    post_body['currency'] = 'BDT'
    post_body['tran_id'] = str(order.id)
    post_body['cus_name'] = f'{order.first_name} {order.last_name}'
    post_body['success_url'] = requests.build_absolute_url(f'/payment/success/{order.id}')
    post_body['fail_url'] = requests.build_absolute_url(f'/payment/fail/{order.id}')
    post_body['cancel_url'] = requests.build_absolute_url(f'/payment/cancel/{order.id}')

    response = requests.post(settings.SSLCOMMERZ_PAYMENT_URL, data = post_body )
    return json.loads(response.text)

def send_order_confirmation_email(order):
    subject = f'Order Confirmation - Order #{order.id}'
    message = render_to_string('') # html code ke --> string convert kore
    to = order.email
    send_email = EmailMultiAlternatives(subject, '', to=[to])
    send_email.attach_alternative(message, 'text/html')
    send_email.send()
