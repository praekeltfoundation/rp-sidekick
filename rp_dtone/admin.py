from django.contrib import admin

from .models import DtoneAccount, Transaction

admin.site.register(DtoneAccount)
admin.site.register(Transaction)
