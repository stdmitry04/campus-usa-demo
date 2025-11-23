# server/universities/admin.py
from django.contrib import admin
from .models import University, SavedUniversity


# registering university model
@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
	list_display = [
		'name',
		'location',
		'rank',
		'admission_chance_display',
		'acceptance_rate_display',
		'tuition_display',
		'has_financial_aid'
	]

	search_fields = ['name', 'location', 'city', 'state']
	list_filter = ['location', 'has_financial_aid', 'rank']
	list_editable = ['rank', 'has_financial_aid']
	ordering = ['rank', 'name']
	list_per_page = 25

	fieldsets = (
		('basic information', {
			'fields': ('name', 'location', 'city', 'state', 'website_url', 'logo')
		}),
		('rankings and stats', {
			'fields': ('rank', 'admission_chance', 'acceptance_rate', 'avg_sat_score', 'avg_gpa')
		}),
		('financial information', {
			'fields': ('annual_tuition', 'has_financial_aid')
		}),
	)


@admin.register(SavedUniversity)
class SavedUniversityAdmin(admin.ModelAdmin):
	list_display = ['user', 'university', 'created_at']
	list_filter = ['created_at']
	search_fields = ['user__username', 'university__name']