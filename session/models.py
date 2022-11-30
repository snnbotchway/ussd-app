"""Models for the ussd project"""
from django.db import models


class Session(models.Model):
    """Session models"""

    PAGES = (
        (1, "Feeling"),
        (2, "Reason"),
        (3, "Result"),
    )

    FEELINGS = (
        (1, "Not well"),
        (2, "Feeling frisky"),
        (3, "Sad"),
    )

    REASONS = (
        (1, "Health"),
        (2, "Money"),
        (3, "Relationship"),
    )

    id = models.PositiveBigIntegerField(primary_key=True)
    page = models.PositiveSmallIntegerField(default=1, choices=PAGES)
    feeling = models.PositiveSmallIntegerField(null=True, choices=FEELINGS)
    reason = models.PositiveSmallIntegerField(null=True, choices=REASONS)
