from django.contrib import admin
from .models import VacationPlan


@admin.register(VacationPlan)
class VacationPlanAdmin(admin.ModelAdmin):
    list_display = ("destination", "start_date", "end_date", "owner")
