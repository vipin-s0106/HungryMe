from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


# make Framework to use Custom user Model For to store Admin Detail to Databases
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['id','username', 'password', 'email', 'is_staff']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )


admin.site.register(User, CustomUserAdmin)


