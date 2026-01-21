from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch

from library.models import Author, Book, Loan, Member
from library.tasks import check_overdue_loans

class LoanTests(TestCase):

    def setUp(self):
        """Initial setup"""
        self.user = User.objects.create_user(username='test', password='testpass')
        self.member = Member.objects.create(user=self.user)
        self.author = Author.objects.create(first_name="Testname", last_name="test_last")
        self.book = Book.objects.create(title='Test Book', author=self.author, isbn='2983984', genre='fiction', available_copies=5)

    # def test_top_active_members(self):
    #     user2 = User.objects.create_user(username='user2', password='pass2', email='user2@test.com')
    #     member2 = Member.objects.create(user=user2)


    #     Loan.objects.create(book=self.book, member=self.member, due_date=timezone.now().date() + timezone.timedelta(days=7))
    #     Loan.objects.create(book=self.book, member=self.member, due_date=timezone.now().date() + timezone.timedelta(days=14))
    #     Loan.objects.create(book=self.book, member=member2, due_date=timezone.now().date() + timezone.timedelta(days=7))

    #     response = self.client.get('/api/members/top_active_members/')

    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(len(response.data), 2)
        
    #     self.assertEqual(response.data[0]['total_loans'], 2)
    #     self.assertEqual(response.data[0]['username'], 'tests')


    #     self.assertEqual(response.data[1]['total_loans'], 1)
    #     self.assertEqual(response.data[1]['username'], 'user2')

    @patch('library.tasks.send_mail')
    def test_check_overdue_loans(self, mock_send_mail):
        overdue_loan = Loan.objects.create(book=self.book, member=self.member, due_date=timezone.now().date() - timezone.timedelta(days=1))
        check_overdue_loans()

        self.assertEqual(mock_send_mail.call_count, 1)

    def test_extend_due_date(self):
        loan = Loan.objects.create(book=self.book, member=self.member, due_date=timezone.now().date() + timezone.timedelta(days=7))
        response = self.client.post(f"/api/loans/{loan.id}/extend_due_date/",
                                    {'additional_days': 5}, content_type='application/json')
        self.assertEqual(response.status_code, 200)


# Create your tests here.
