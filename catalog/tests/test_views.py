
import datetime
import uuid

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission # Required to grant permission to set book returned

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