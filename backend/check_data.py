#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/app')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chicken_house_management.settings')
django.setup()

from rotem_scraper.models import RotemDataPoint
from django.db import models

print('Total data points:', RotemDataPoint.objects.count())
print('House-specific data points:', RotemDataPoint.objects.filter(data_type__contains='house_').count())

print('\nHouse-specific data types:')
for data_type, count in RotemDataPoint.objects.filter(data_type__contains='house_').values_list('data_type').annotate(count=models.Count('id')).order_by('-count')[:10]:
    print(f'  {data_type}: {count} records')

print('\nLatest house data:')
for dp in RotemDataPoint.objects.filter(data_type__contains='house_').order_by('-timestamp')[:5]:
    print(f'  {dp.data_type}: {dp.value} {dp.unit} at {dp.timestamp}')
