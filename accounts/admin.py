from django.contrib import admin

from accounts.models import *

models = [Profile]

for model in models:
    admin.site.register(model)