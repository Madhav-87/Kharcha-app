"""System categories and per-user category preferences."""

from django.db import models

from apps.accounts.models import User
from common.db_fields import (
    DatabaseNowDateTime3Field,
    DateTime3Field,
    FixedCharField,
    PublicIdField,
    UnsignedBigAutoField,
    UpdatedDateTime3Field,
)


class Category(models.Model):
    id = UnsignedBigAutoField(primary_key=True)
    public_id = PublicIdField()
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_categories",
    )
    name = models.CharField(max_length=60)
    slug = models.CharField(max_length=80)
    icon = models.CharField(max_length=40)
    emoji = models.CharField(max_length=8, null=True, blank=True)
    color = FixedCharField(max_length=7)
    is_default = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    archived_at = DateTime3Field(null=True, blank=True)
    created_at = DatabaseNowDateTime3Field()
    updated_at = UpdatedDateTime3Field()

    class Meta:
        managed = False
        db_table = "categories"
        constraints = [
            models.UniqueConstraint(fields=("user", "slug"), name="uq_cat_user_slug"),
            models.UniqueConstraint(fields=("user", "name"), name="uq_cat_user_name"),
        ]

    def __str__(self):
        return self.name


class UserCategory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category_preferences")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="user_preferences"
    )
    color_override = FixedCharField(max_length=7, null=True, blank=True)
    icon_override = models.CharField(max_length=40, null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    hidden = models.BooleanField(default=False)
    pk = models.CompositePrimaryKey("user_id", "category_id")

    class Meta:
        managed = False
        db_table = "user_categories"
