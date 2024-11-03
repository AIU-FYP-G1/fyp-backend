from django.contrib import admin

from patients.models import *

models = [Patient, Diagnosis]

for model in models:
    admin.site.register(model)
