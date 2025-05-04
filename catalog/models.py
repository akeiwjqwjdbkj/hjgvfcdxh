from django.db import models

from django.urls import reverse # Use for get_absolute_url()
from django.db.models import UniqueConstraint # Constrain fields to unique values
from django.db.models.functions import Lower # Return lower case value

# Create your models here.

class Genre(models.Model):
	"""Model representing a book genre."""

	name = models.CharField(
		max_length=200,
		unique=True,
		help_text="Enter a book genre (e.g., Science Fiction, French Poetry, etc.)"
	)

	def __str__(self):
		"""Strng for representing Model object."""
		return self.name
	
	def get_absolute_url(self):
		"""Returns the URL to access a particular genre instance."""
		return reverse('genre-detail', args=[str(self.id)])
	
	class Meta:
		constraints = [UniqueConstraint(
			Lower('name'),
			name='genre_name_case_insensitive_unique',
			violation_error_message="Genre already exists (case insensitive match)"
		)]
