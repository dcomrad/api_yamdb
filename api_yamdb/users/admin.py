from django.contrib import admin
from reviews.models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('pk', 'username', 'role', 'email',
                    'first_name', 'last_name')
    search_fields = ('username',)


admin.site.register(User, UserAdmin)
