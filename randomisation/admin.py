from django.contrib import admin

from randomisation.models import Arm, Strata, StrataOption, Strategy


class ArmInline(admin.TabularInline):
    model = Arm


class StrataOptionInline(admin.TabularInline):
    model = StrataOption


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ("name",)

    inlines = [ArmInline]


@admin.register(Strata)
class StrataAdmin(admin.ModelAdmin):
    list_display = ("__str__",)

    inlines = [StrataOptionInline]
