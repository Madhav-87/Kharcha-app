"""Public serializers for categories and user category preferences."""

from rest_framework import serializers

from apps.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    is_custom = serializers.SerializerMethodField()
    selected = serializers.SerializerMethodField()
    hidden = serializers.SerializerMethodField()
    effective_icon = serializers.SerializerMethodField()
    effective_color = serializers.SerializerMethodField()
    effective_sort_order = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "public_id", "name", "slug", "icon", "emoji", "color", "is_default",
            "is_custom", "selected", "hidden", "effective_icon", "effective_color",
            "effective_sort_order",
        )
        read_only_fields = ("public_id", "slug", "is_default")

    def get_is_custom(self, obj):
        return obj.user_id is not None

    def get_selected(self, obj):
        return bool(getattr(obj, "user_category_preference", None))

    def get_hidden(self, obj):
        preference = getattr(obj, "user_category_preference", None)
        return bool(preference.hidden) if preference else False

    def get_effective_icon(self, obj):
        preference = getattr(obj, "user_category_preference", None)
        return (preference.icon_override if preference else None) or obj.icon

    def get_effective_color(self, obj):
        preference = getattr(obj, "user_category_preference", None)
        return (preference.color_override if preference else None) or obj.color

    def get_effective_sort_order(self, obj):
        if obj.user_id is not None:
            return obj.sort_order
        preference = getattr(obj, "user_category_preference", None)
        return preference.sort_order if preference else obj.sort_order


class CategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60, trim_whitespace=True)
    icon = serializers.CharField(max_length=40, trim_whitespace=True)
    emoji = serializers.CharField(max_length=8, allow_blank=True, allow_null=True, required=False)
    color = serializers.RegexField(r"^#[0-9A-Fa-f]{6}$", max_length=7)
    sort_order = serializers.IntegerField(required=False, default=0)


class CategoryUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60, trim_whitespace=True, required=False)
    icon = serializers.CharField(max_length=40, trim_whitespace=True, required=False)
    emoji = serializers.CharField(max_length=8, allow_blank=True, allow_null=True, required=False)
    color = serializers.RegexField(r"^#[0-9A-Fa-f]{6}$", max_length=7, required=False)
    sort_order = serializers.IntegerField(required=False)


class CategoryPreferenceSerializer(serializers.Serializer):
    category_public_id = serializers.UUIDField()
    hidden = serializers.BooleanField(required=False)
    color_override = serializers.RegexField(
        r"^#[0-9A-Fa-f]{6}$", max_length=7, required=False, allow_null=True
    )
    icon_override = serializers.CharField(
        max_length=40, required=False, allow_blank=True, allow_null=True
    )
    sort_order = serializers.IntegerField(required=False)


class CategoryPreferencesSerializer(serializers.Serializer):
    preferences = CategoryPreferenceSerializer(many=True, allow_empty=False, max_length=100)
