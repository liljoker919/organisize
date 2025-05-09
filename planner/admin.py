from django.contrib import admin
from .models import VacationPlan, Group


@admin.register(VacationPlan)
class VacationPlanAdmin(admin.ModelAdmin):
    list_display = ("destination", "start_date", "end_date", "owner")

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'invite_link', 'created_at')
    filter_horizontal = ('members',)
    search_fields = ('name',)
    readonly_fields = ('invite_link',)