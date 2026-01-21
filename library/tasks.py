from celery import shared_task
from .models import Loan
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass


@shared_task
def check_overdue_loans():
    """Check loans that are overdue"""
    current_date = timezone.now().date()

    late_loans = Loan.objects.select_related('member__user', 'book').filter(due_date__lt=current_date, is_returned=False)

    if not late_loans.exists():
        logger.info("No late returns found.")
        return

    for late_loan in late_loans:
        user_email = late_loan.member.user.email
        borrowed_book = late_loan.book.title
        user_name = late_loan.member.user.username

        try:
            send_mail(
                subject='Book Return Overdue Notice',
                message=(
                    f'Dear {user_name}, \n\n'
                    f'Your borrowed book "{borrowed_book} was due on {late_loan.due_date}. \n'
                    f'Kindly return it at gyour earliest convenience to avoid any penalties. \n\n'
                    f'Thank you for your cooperation'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user_email],
                fail_silently=False
            )
        except Exception as e:
            logger.error(f'Email delivery failed for user {user_email}: {e}')
