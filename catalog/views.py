from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

import datetime

from .models import Book, BookInstance, Author, Genre
from catalog.forms import RenewBookForm

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

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
	# get object with primary key, return Http404 if it doesn't exist
	book_instance = get_object_or_404(BookInstance, pk=pk)

	# If POST request process form data
	if request.method == 'POST':
		# Create form instance and populate with data from request (binding)
		form = RenewBookForm(request.POST)

		if form.is_valid():
			# process the data in form.cleared_data as required (write to model due_back field)
			# ensure sanitization, validation, conversion to more 'friendly' data types
			book_instance.due_back = form.cleaned_data['renewal_date']
			book_instance.save()

			# redirect to success
			return HttpResponseRedirect(reverse('all_borrowed'))
		else:
			# doesn't work when producing renewal dates?
			context = {
				'form' : form,
				'book_instance' : book_instance,
			}

			return render(request, 'catalog/book_renew_librarian.html', context)
	
	# Produce default form for other methods like GET
	else:
		# default - 3 weeks
		proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
		form = RenewBookForm(initial={ 'renewal_date' : proposed_renewal_date })

		context = {
			'form' : form,
			'book_instance' : book_instance,
		}

		return render(request, 'catalog/book_renew_librarian.html', context)

# implementation II

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

# Author modification views

# create, update views utilize templates with '_form" suffix
class AuthorCreate(PermissionRequiredMixin, CreateView):
	model = Author
	fields = { 'first_name', 'last_name', 'date_of_birth', 'date_of_death' } # to be displayed
	initial = { 'date_of_death' : '11/11/2025' }
	permission_required = 'catalog.add_author'

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
	model = Author
	fields = { 'first_name', 'last_name', 'date_of_birth', 'date_of_death' } # to be displayed
	permission_required = 'catalog.update_author'

# delete view utilizes templates with '_confirm_delete' suffix
class AuthorDelete(PermissionRequiredMixin, DeleteView):
	model = Author
	success_url = reverse_lazy('authors') # unknown if link exists
	permission_required = 'catalog.delete_author'

	def form_valid(self, form):
		try:
			self.object.delete()
			return HttpResponseRedirect(self.success_url)
		except Exception as e:
			return HttpResponseRedirect(reverse('author_delete'), kwargs={ 'pk' : self.object.pk })
