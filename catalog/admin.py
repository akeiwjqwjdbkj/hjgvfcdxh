from django.contrib import admin

from .models import Author, Genre, Book, BookInstance, Language

# Register your models here.

# username: asdfasdf, email@email.com
# password: p5bbw0rd

class AuthorAdmin(admin.ModelAdmin):
	pass

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
	pass

class BookAdmin(admin.ModelAdmin):
	pass

class BookInstanceAdmin(admin.ModelAdmin):
	pass

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
	pass

admin.site.register(Author, AuthorAdmin)
# admin.site.register(Genre)
admin.site.register(Book, BookAdmin)
admin.site.register(BookInstance, BookInstanceAdmin)
# admin.site.register(Language)
