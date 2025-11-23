# server/universities/management/commands/seed_universities.py
"""
[BUSINESS DATA REPLACED WITH GENERIC DEMO DATA]

Original implementation: Seeded database with real university partnerships and admission data.
This included proprietary partner university information, negotiated admission rates, and
business relationships that were specific to the education platform.

Demo version: Uses generic, fictional university data for demonstration purposes only.
"""
from django.core.management.base import BaseCommand
from ...models import University


class Command(BaseCommand):
	help = 'populate database with sample universities (demo data only)'

	def handle(self, *args, **options):
		University.objects.all().delete()

		# Generic demo universities - NOT real institutions
		universities_data = [
			{
				'id': 1,
				'name': 'Demo Tech Institute',
				'location': 'US',
				'rank': 1,
				'admission_chance': 50,
				'acceptance_rate': 4,
				'avg_sat_score': 1550,
				'avg_gpa': 4.0,
				'annual_tuition': 56000,
				'has_financial_aid': True,
				'logo': None
			},
			{
				'id': 2,
				'name': 'Sample State University',
				'location': 'US',
				'rank': 2,
				'admission_chance': 48,
				'acceptance_rate': 5,
				'avg_sat_score': 1500,
				'avg_gpa': 3.96,
				'annual_tuition': 52000,
				'has_financial_aid': True,
				'logo': None
			},
			{
				'id': 3,
				'name': 'Example College',
				'location': 'US',
				'rank': 3,
				'admission_chance': 47,
				'acceptance_rate': 4,
				'avg_sat_score': 1520,
				'avg_gpa': 3.97,
				'annual_tuition': 54000,
				'has_financial_aid': True,
				'logo': None
			},
			{
				'id': 4,
				'name': 'Test Institute of Technology',
				'location': 'US',
				'rank': 4,
				'admission_chance': 45,
				'acceptance_rate': 6,
				'avg_sat_score': 1530,
				'avg_gpa': 4.0,
				'annual_tuition': 58000,
				'has_financial_aid': True,
				'logo': None
			},
			{
				'id': 5,
				'name': 'Mock University',
				'location': 'US',
				'rank': 5,
				'admission_chance': 43,
				'acceptance_rate': 7,
				'avg_sat_score': 1510,
				'avg_gpa': 3.95,
				'annual_tuition': 56000,
				'has_financial_aid': True,
				'logo': None
			}
		]

		for uni_data in universities_data:
			university = University.objects.create(**uni_data)
			self.stdout.write(self.style.SUCCESS(f'created university: {university.name}'))

		self.stdout.write(self.style.SUCCESS(f'successfully created {len(universities_data)} universities'))