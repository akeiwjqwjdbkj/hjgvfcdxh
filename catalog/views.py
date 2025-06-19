from django.shortcuts import render
from django.views import generic

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Book, BookInstance, Author, Genre

# Create your views here.

def index(request):
	'''View function for the home page of the site.'''

	# Object counts
	num_books = Book.objects.all().count()
	num_authors = Author.objects.count() # all implied
	num_instances = BookInstance.objects.all().count()

	# Available books, a=available
	num_instances_available = BookInstance.objects.filter(status__exact='a').count()

	num_genre_fantasy = Genre.objects.filter(name__iexact='fantasy').count()
	num_genre_drama = Genre.objects.filter(name__iexact='drana').count()

	num_book_topaz = Book.objects.filter(title__iexact='topaz').count()
	num_book_c = Book.objects.filter(title__iexact='sobre').count()

	# Number of visits in the view, counted via session variable
	num_visits = request.session.get('num_visits', 0)
	num_visits += 1
	request.session['num_visits'] = num_visits
	
	context = {
		'num_books' : num_books,
		'num_authors' : num_authors,
		'num_instances' : num_instances,
		'num_instances_available' : num_instances_available,

		'num_genre_fantasy' : num_genre_fantasy,
		'num_genre_drama' : num_genre_drama,

		'num_book_topaz' : num_book_topaz,
		'num_book_c' : num_book_c,

		'num_visits' : num_visits,
	}

	# render in template with data provided in context
	return render(request, 'index.html', context=context)

# Book views

class BookListView(generic.ListView):
	model = Book

	context_object_name = 'book_list' # list name
	paginate_by = 10

	# def get_queryset(self):
	#	return Book.objects.filter(title__icontains='campana')[:5]

class BookDetailView(generic.DetailView):
	model = Book

# Author views

class AuthorListView(generic.ListView):
	model = Author

	context_object_name = 'author_list'
	paginate_by = 10

class AuthorDetailView(generic.DetailView):
	model = Author

class LoanedBooksByUserListView (LoginRequiredMixin, generic.ListView):
	"""Generic class-based view listing books on loan to the current user."""

	model = BookInstance
	template_name = 'catalog/bookinstance_list_borrowed_user.html'
	paginate_by = 10

	def get_queryset(self):
		return (
			BookInstance.objects
				.filter(borrower=self.request.user)
				.filter(status__exact='o')
				.order_by('due_back')
		)

class AllLoanedBooksListView(PermissionRequiredMixin, generic.ListView):
	'''Generic class-based view for lising all books on loan.'''

	permission_required = 'catalog.can_mark_returned'

	model = BookInstance
	template_name = 'catalog/bookinstance_list_all_borrowed.html'
	paginate_by = 10

	# get all books
	def get_queryset(self):
		return (
			BookInstance.objects
				.filter(status__exact='o')
				.order_by('due_back')
		)
