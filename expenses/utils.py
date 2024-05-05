from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, queue=settings.NOTIFICATION_QUEUE)
def send_email_notification(self, **kwargs):
    """
    Helper for sending email notifications of all sorts
    """
    email = kwargs.get("email")
    subject = kwargs.get("subject")
    message = kwargs.get("message")
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

