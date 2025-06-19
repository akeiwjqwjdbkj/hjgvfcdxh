
from django.urls import path, include
from . import views

urlpatterns = [
	path('', views.index, name='index'),

	path('books/', views.BookListView.as_view(), name='books'),
	path('book/<int:pk>', views.BookDetailView.as_view(), name='book_detail'), # store primary key = pk

	path('authors/', views.AuthorListView.as_view(), name='authors'),
	path('authors/<int:pk>', views.AuthorDetailView.as_view(), name='author_detail'),

	path('mybooks/', views.LoanedBooksByUserListView.as_view(), name='my_borrowed'),
	path('allbooks/', views.AllLoanedBooksListView.as_view(), name='all_borrowed'),
]
