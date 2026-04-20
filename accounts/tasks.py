from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
 


@shared_task
def send_transaction_notification(email, transaction_type, amount):
    send_mail(
        subject="Уведомление о транзакции",
        message=(
            f"Ваша транзакция выполнена успешно\n"
            f"Тип: {transaction_type}\n"
            f"Сумма: {amount} сом\n"
            f"Дата: {timezone.now().strftime('%d.%m.%Y %H:%M')}"
        ),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
    return f"Уведомление отправлено на {email}"
 

@shared_task
def send_daily_report():
    from accounts.models import Transaction
 
    yesterday = timezone.now() - timezone.timedelta(days=1)
    transactions = Transaction.objects.filter(created_at__gte=yesterday)
    count = transactions.count()
    total = sum(t.amount for t in transactions)
 
    send_mail(
        subject="Ежедневный отчёт по транзакциям",
        message=(
            f"Отчёт за {yesterday.strftime('%d.%m.%Y')}:\n"
            f"Количество транзакций: {count}\n"
            f"Общая сумма: {total} сом"
        ),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )
    return f"Отчёт отправлен, транзакций: {count}, сумма: {total}"
 

@shared_task
def send_otp_email(email, otp_code):
    send_mail(
        subject="Ваш код подтверждения Bank System",
        message=(
            f"Ваш одноразовый код для входа: {otp_code}\n"
            f"Код действителен 5 минут\n"
            f"Если вы не запрашивали код проигнорируйте это письмо"
        ),
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
    return f"Код отправлен на {email}"