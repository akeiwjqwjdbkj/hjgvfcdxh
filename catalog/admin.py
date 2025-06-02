from django.contrib import admin

from .models import Author, Genre, Book, BookInstance, Language

# Register your models here.

# username: asdfasdf, email@email.com
# password: p5bbw0rd

class BooksInstanceInline(admin.TabularInline):
	model = BookInstance
	extra = 0

class BookInline(admin.StackedInline):
	model = Book
	extra = 0


class AuthorAdmin(admin.ModelAdmin):
	list_display = ('last_name', 'first_name', 'date_of_birth', 'date_of_death')

	fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]

	inlines = [BookInline]

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
	pass

class BookAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'display_genre')

	inlines = [BooksInstanceInline]

class BookInstanceAdmin(admin.ModelAdmin):
	list_display = ('book', 'status', 'due_back', 'id')
	list_filter = ('status', 'due_back')

	fieldsets = (
		(None, { 'fields' : ('book', 'imprint', 'id') }),
		('Availability', { 'fields' : ('status', 'due_back') }),
	)

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
	pass

admin.site.register(Author, AuthorAdmin)
# admin.site.register(Genre)
admin.site.register(Book, BookAdmin)
admin.site.register(BookInstance, BookInstanceAdmin)
# admin.site.register(Language)
