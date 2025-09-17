
import datetime
import uuid
import random

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission # Required to grant permission to set book returned

from django.contrib.contenttypes.models import ContentType

from catalog.models import Author, BookInstance, Book, Genre, Language
User = get_user_model()

class AuthorListViewTest(TestCase):
	@classmethod
	def setUpTestData(cls):
		# Create 13 authors for pagination tests
		number_of_authors = 13

		for author_id in range(number_of_authors):
			Author.objects.create(
				first_name=f'Dominique { author_id }',
				last_name=f'Surname { author_id }'
			)
	
	# url only
	def test_view_url_exists_at_desired_location(self):
		response = self.client.get('/catalog/authors/')
		self.assertEqual(response.status_code, 200)
	
	# accessible via revrse also
	def test_view_url_accessible_by_name(self):
		response = self.client.get(reverse('authors'))
		self.assertEqual(response.status_code, 200)
	
	def test_view_uses_correct_template(self):
		response = self.client.get(reverse('authors'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'catalog/author_list.html')
	
	def test_pagination_is_ten(self):
		response = self.client.get(reverse('authors'))
		self.assertEqual(response.status_code, 200)
		# verify pagination exists in the context
		self.assertTrue('is_paginated' in response.context)
		self.assertTrue(response.context['is_paginated'] == True)
		self.assertEqual(len(response.context['author_list']), 10)
	
	def test_lists_all_authors(self):
		# get 2nd page and verify it has 3 items remaining
		response = self.client.get(reverse('authors') + '?page=2')
		self.assertEqual(response.status_code, 200)
		self.assertTrue('is_paginated' in response.context)
		self.assertTrue(response.context['is_paginated'] == True)
		self.assertEqual(len(response.context['author_list']), 3)

class LoanedBookInstancesByUserListViewTest(TestCase):
	def setUp(self):
		# Create two users
		test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
		test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')

		test_user1.save()
		test_user2.save()

		# Create book
		test_author = Author.objects.create(first_name='Dominique', last_name='Rousseau')
		test_genre = Genre.objects.create(name='Fantasy')
		test_language = Language.objects.create(name='English')
		test_book = Book.objects.create(
			title = 'BookTitle',
			summary = 'Book summary',
			isbn = 'ABCDEFG',
			author = test_author,
			language = test_language,
		)

		# Create genre as post-step
		genre_objects_for_book = Genre.objects.all()
		test_book.genre.set(genre_objects_for_book) # note: direct assignment of many-to-many types not allowed
		test_book.save()

		# Create 30 BookInstance objects
		number_of_book_copies = 30

		for book_copy in range(number_of_book_copies):
			return_date = timezone.localtime() + datetime.timedelta(days=book_copy % 5)
			current_borrower = test_user1 if book_copy % 2 else test_user2
			status = 'm'

			BookInstance.objects.create(
				book = test_book,
				imprint = 'Unlikely imprint, 2016',
				due_back = return_date,
				borrower = current_borrower,
				status = status
			)

	def test_redirect_if_not_logged_in(self):
		response = self.client.get(reverse('my_borrowed'))
		self.assertRedirects(response, '/accounts/login/?next=/catalog/mybooks/')
	
	def test_logged_in_uses_correct_template(self):
		login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
		response = self.client.get(reverse('my_borrowed'))

		# Verify user is logged in
		self.assertEqual(str(response.context['user']), 'testuser1')
		# Verify "successful" response
		self.assertEqual(response.status_code, 200)

		# Verify correct template
		self.assertTemplateUsed('catalog/bookinstance_list_borrowed_user.html')

	# Verify return of books on loan to current borrower only
	def test_only_borrowed_books_in_list(self):
		login = self.client.login(username='testuser1', password='1X<IsRUkw+tuK')
		response = self.client.get(reverse('my_borrowed'))

		# Verify user is logged in
		self.assertEqual(str(response.context['user']), 'testuser1')
		# Verify "successful" response
		self.assertEqual(response.status_code, 200)

		# I : Verify that there aren't any inital books in list (none on loan)
		self.assertTrue('bookinstance_list' in response.context)
		self.assertEqual(len(response.context['bookinstance_list']), 0)

		# Change all books to be on loan
		books = BookInstance.objects.all()[:10]

		for book in books:
			book.status = 'o'
			book.save()

		# II : Verify there are borrowed books in list
		response = self.client.get(reverse('my_borrowed'))
		# Verify login
		self.assertEqual(str(response.context['str']), 'testuser1')
		# Verify "successful response"
		self.assertEqual(response.status_code, 200)

		self.assertTrue('bookinstance_list' in response.context)

		# III : Verify all books belong to testuser1 and are on loan
		for book_item in response.context['bookinstance_list']:
			self.assertEqual(response.context['user'], book_item.borrower)
			self.assertEqual(book_item.status, 'o')
	
	def test_pages_ordered_by_due_date(self):
		# Change all books to be on loan
		for book in BookInstance.objects.all():
			book.status = 'o'
			book.save()
		
		login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
		response = self.client.get(reverse('my_borrowed'))

		# Verify login
		self.assertEqual(str(response.content['user']), 'testuser1')
		# Verify "successful" response
		self.assertEqual(response.status_code, 200)

class RenewBookInstancesViewTest(TestCase):
	def setUp(self):
		# Create users
		test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
		test_user2 = User.objects.create_user(username='testuser2', password='2HJ1vRV0Z&3iD')

		test_user1.save()
		test_user2.save()

		# Give test_user 2 permission to renew books
		permission = Permission.objects.get(name='Set book as returned')
		test_user2.user_permissions.add(permission)
		test_user2.save()

		# Create book
		test_author = Author.objects.create(first_name='Dominique', last_name='Rousseau')
		test_genre = Genre.objects.create(name='Fantasy')
		test_language = Language.objects.create(name='English')
		test_book = Book.objects.create(
			title = 'Book title',
			summary = 'My book summary',
			isbn = 'ABCDEFG',
			author = test_author,
			language = test_language
		)

		# Post-step : Create genre
		genre_objects_for_book = Genre.objects.all()
		test_book.genre.set(genre_objects_for_book) # Direct assignment of many-to-many types not allowed
		test_book.save()

		# Create BookInstance object for test_user1
		return_date = datetime.date.today() + datetime.timedelta(days=5)
		self.test_bookinstance1 = BookInstance.objects.create(
			book = test_book,
			imprint = 'Unlikely Imprint, 2016',
			due_back = return_date,
			borrower = test_user1,
			status = 'o'
		)

		# Create BookInstance object for test_user2
		return_date = datetime.date.today() + datetime.timedelta(days=5)
		self.test_bookinstance2 = BookInstance.objects.create(
			book=test_book,
			imprint='Unlikely Imprint, 2016',
			due_back=return_date,
			borrower=test_user2,
			status='o'
		)
	
	# Test cases for verifying correct permissions
	def test_redirect_if_not_logged_in(self):
		response = self.client.get(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance1.pk
		}))
		# Manually check redirect (redriect URL is unpredictable when using assertRedirect)
		self.assertEqual(response.status_code, 302) # URL redirect, "Moved Temporarily"
		self.assertTrue(response.url.startsWith('/accounts/login/'))
	
	def test_forbidden_if_logged_in_but_incorrect_permission(self):
		# test_user1 does not have correct permissions (test_user2 does)
		login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
		response = self.client.get(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance1.pk
		}))
		self.assertEqual(response.status_code, 403)
	
	def test_logged_in_with_permission_borrowed_book(self):
		# test_user2 has correct permissions to borrow books
		login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
		response = self.client.get(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance2.pk
		}))

		# Verify login is possible (book is assigned to this user with correct permissions)
		self.assertEqual(response.status_code, 200)
	
	def test_logged_in_with_permission_borrowed_book_of_another_user(self):
		# test_user2 has correct permissions to view books
		login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
		response = self.client.get(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance1.pk # look into book assigned to test_user1
		}))

		# Verify login is possible (any book can be viewed as librarian)
		self.assertEqual(response.status_code, 200)
	
	def test_HTTP404_for_invalid_book_if_logged_in(self):
		# unlikely UID to match BookInstance!!
		test_uid = uuid.uuid4()

		login = self.client.login(username='testuser2', password='2Hj1vRV0Z&3iD')
		response = self.client.get(reverse('renew_book_librarian', kwargs={ 'pk' : test_uid }))
		self.assertEqual(response.status_code, 404) # Invalid book
	
	def test_uses_correct_template(self):
		login = self.client.login(username='testuser2', password='2hJ1vRV0Z&3iD')
		response = self.client.get(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance1.pk # look into book assigned to test_user1
		}))

		self.assertEqual(response.status_code, 200)
		# Verify correct template used
		self.assertTemplateUsed(response, 'catalog/book_renew_librarian.html')

	# Test case for redirecting to all borrowed books if renewal succeeds
	def test_redirects_to_all_borrowed_book_list_on_success(self):
		login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
		valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
		response = self.client.post(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance1.pk
		}), { 'renewal_date' : valid_date_in_future })

		self.assertRedirects(response, reverse('all_borrowed'))
	
	# Test case for verifying initial date is 3 weeks in the future
	def test_form_renewal_date_initally_has_date_3_weeks_in_future(self):
		login = self.client.login(username='testuser2', password='2HJ1vRV0Z&3iD')
		response = self.client.get(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance1.pk
		}))

		self.assertEqual(response.status_code, 200)
		
		date_3_weeks_in_future = datetime.date.today() + datetime.timedelta(weeks=3)
		self.assertEqual(response.context['form'].initial['renewal_date'], date_3_weeks_in_future)
	
	# Test cases for invalid dates
	def test_invalid_renewal_date_past(self):
		login = self.client.login(username='testuser2', password='2HJ1vRV0Z&iD')
		date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)
		response = self.client.post(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance1.pk
		}), { 'renewal_date' : date_in_past })

		self.assertEqual(response.status_code, 200)
		self.assertFormError(response.context['form'], 'renewal_date', 'Invalid date - renewal in past')
	
	def test_invalid_renewal_date_future(self):
		login = self.client.login(username='testuser2', password='2HJ1vRV0Z&iD')
		date_in_future = datetime.date.today() + datetime.timedelta(weeks=5)
		response = self.client.post(reverse('renew_book_librarian', kwargs={
			'pk' : self.test_bookinstance1.pk
		}), { 'renewal_date' : date_in_future })

		self.assertEqual(response.status_code, 200)
		self.assertFormError(
			response.context['form'],
			'renewal_date',
			'Invalid date - renewal more than 4 weeks ahead'
		)

class AuthorCreateViewTest(TestCase):
	# check access, initial date, used template, redirect successful
	def setUp(self):
		# Create user
		test_user1 = User.objects.create_user(username='test_user1', password='1X<ISRUkw+tuK')
		test_user2 = User.objects.create_user(username='test_user2', password='2HJ1vRV0Z&3iD')

		content_typeAuthor = ContentType.objects.get_for_model(Author)
		permAddAuthor = Permission.objects.get(codename='add_author', content_type=content_typeAuthor)

		test_user1.user_permissions.add(permAddAuthor)

		test_user1.save()
		test_user2.save()
		# return super().setUp() # to change
	
	def test_redirect_if_not_logged_in(self): #
		response = self.client.get(reverse('author_create'))
		# Check URL
		self.assertEqual(response.status_code, 302)
		# will cause redirect to login page
		self.assertTrue(response.url.startsWith('/accounts/login/'))
	
	def test_forbidden_if_logged_in_but_incorrect_permission(self):
		# test_user2 does not have correct permissions
		login = self.client.login(username='test_user2', password='2HJ1vRV0Z&3iD')
		response = self.client.get(reverse('author_create'))
		self.assertEqual(response.status_code, 403)
	
	def test_logged_in_with_permission(self):
		# test_user1 should have correct permission to create authors
		login = self.client.login(username='test_user1', password='1X<ISRUkw+tuK')
		response = self.client.get(reverse('author_create'))
		self.assertEqual(response.status_code, 200) # Verify success

	def test_uses_correct_template(self):
		login = self.client.login(username='test_user', password='')
		response = self.client.get(reverse('author_create'))
		
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'catalog/author_create.html') # !!

	def test_redirects_to_created_author(self):
		login = self.client.login(username='test_user1', password='1X<ISRUkw+tuK')
		
		valid_birth_date = datetime.date.today() - datetime.timedelta(weeks=(random.random()*100))
		valid_death_date = datetime.date.today() - datetime.timedelta(weeks=(random.random()*30))

		response = self.client.post(reverse('author_create'), {
			'first_name' : 'Test',
			'last_name' : 'Test',
			'date_of_birth' : valid_birth_date,
			'date_of_death' : valid_death_date
		})
		current_num_authors = Author.objects.all().count()
		# Ensure redirect to created author
		self.assertRedirects(response, reverse('author_detail', kwargs={
			'pk' : current_num_authors
		}))
	
	def test_initial_date_of_death(self): #
		login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
		response = self.client.get(reverse('author_create'))

		self.assertEqual(response.status_code, 200)

		inital_date = datetime.date(2025, 11, 11)
		self.assertEqual(response.context['form'].initial['date_of_death'], inital_date)
