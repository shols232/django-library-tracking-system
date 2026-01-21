from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, LoanExtensionSerializer, MemberSerializer, LoanSerializer
from rest_framework.decorators import action
from django.utils import timezone
from .tasks import send_loan_notification
from django.db.models import Count
from rest_framework.pagination import PageNumberPagination

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.select_related('author').prefetch_related('loans')
    serializer_class = BookSerializer
    pagination_class = PageNumberPagination

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan = Loan.objects.create(book=book, member=member)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def top_active_members(self, request):
        top_members = (
            Member.objects.annotate(total_loans=Count('loans')).order_by('-total_loans').select_related('user')
        )

        data = [
            {'username': member.user.username, 'total_loans': member.total_loans, 'email': member.user.email, 'id': member.user.id} for member in top_members
        ]

        return Response(data, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=True, methods=['post'])
    def extend_due_date(self, request, pk=None):
        loan = self.get_object()
        serializer = LoanExtensionSerializer(data=request.data, context={'loan': loan})

        if serializer.is_valid():
            loan.due_date += timezone.timedelta(days=serializer.validated_data['additional_days'])
            loan.save(update_fields=['due_date'])
            return Response({'message': "Loan due date extended"})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
