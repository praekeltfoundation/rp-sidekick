from django.db import models
from django.db.models import JSONField
from django.utils.text import slugify


class Strata(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)

    @property
    def slug(self):
        return slugify(self.name)

    def __str__(self):
        options = [option.description for option in self.options.all()]
        return f"{self.name} - [{', '.join(options)}]"


class Strategy(models.Model):
    class Meta:
        verbose_name_plural = "Strategies"

    name = models.CharField(max_length=200, null=False, blank=False)
    stratas = models.ManyToManyField(Strata, related_name="stategy_stratas")


class Arm(models.Model):
    strategy = models.ForeignKey(
        Strategy,
        related_name="arms",
        null=False,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=200, null=False, blank=False)
    weight = models.IntegerField(default=1)


class StrataOption(models.Model):
    strata = models.ForeignKey(
        Strata,
        related_name="options",
        null=False,
        on_delete=models.CASCADE,
    )
    description = models.CharField(max_length=200, null=False, blank=False)


class StrataMatrix(models.Model):
    strategy = models.ForeignKey(
        Strategy,
        related_name="matrix_records",
        null=False,
        on_delete=models.CASCADE,
    )
    strata_data = JSONField()
    next_index = models.IntegerField(default=0)
    arm_order = models.CharField(max_length=255, null=False, blank=False)
