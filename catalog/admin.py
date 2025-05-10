from django.contrib import admin

from .models import Author, Genre, Book, BookInstance, Language

# Register your models here.

# username: asdfasdf, email@email.com
# password: p5bbw0rd

admin.site.register(Author)
admin.site.register(Genre)
admin.site.register(Book)
admin.site.register(BookInstance)
admin.site.register(Language)
