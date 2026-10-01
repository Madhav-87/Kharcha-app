"""MySQL column types used by the supplied Student Finance schema."""

import uuid

from django.db import models
from django.db.models.functions import Now
from django.core.validators import MaxValueValidator, MinValueValidator


class UnsignedBigAutoField(models.BigAutoField):
    """BIGINT UNSIGNED AUTO_INCREMENT primary key."""

    def db_type(self, connection):
        return "bigint unsigned AUTO_INCREMENT"

    def rel_db_type(self, connection):
        return "bigint unsigned"


class UnsignedIntegerAutoField(models.AutoField):
    """INT UNSIGNED AUTO_INCREMENT primary key."""

    def db_type(self, connection):
        return "int unsigned AUTO_INCREMENT"

    def rel_db_type(self, connection):
        return "int unsigned"


class UnsignedSmallAutoField(models.SmallAutoField):
    """SMALLINT UNSIGNED AUTO_INCREMENT primary key."""

    def db_type(self, connection):
        return "smallint unsigned AUTO_INCREMENT"

    def rel_db_type(self, connection):
        return "smallint unsigned"


class UnsignedBigIntegerField(models.BigIntegerField):
    def __init__(self, *args, **kwargs):
        validators = list(kwargs.pop("validators", []))
        validators.extend((MinValueValidator(0), MaxValueValidator(18_446_744_073_709_551_615)))
        super().__init__(*args, validators=validators, **kwargs)

    def db_type(self, connection):
        return "bigint unsigned"


class UnsignedIntegerField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        validators = list(kwargs.pop("validators", []))
        validators.extend((MinValueValidator(0), MaxValueValidator(4_294_967_295)))
        super().__init__(*args, validators=validators, **kwargs)

    def db_type(self, connection):
        return "int unsigned"


class UnsignedSmallIntegerField(models.SmallIntegerField):
    def __init__(self, *args, **kwargs):
        validators = list(kwargs.pop("validators", []))
        validators.extend((MinValueValidator(0), MaxValueValidator(65_535)))
        super().__init__(*args, validators=validators, **kwargs)

    def db_type(self, connection):
        return "smallint unsigned"


class UnsignedTinyIntegerField(models.PositiveSmallIntegerField):
    def __init__(self, *args, **kwargs):
        validators = list(kwargs.pop("validators", []))
        validators.append(MaxValueValidator(255))
        super().__init__(*args, validators=validators, **kwargs)

    def db_type(self, connection):
        return "tinyint unsigned"


class UnsignedTinyAutoField(models.AutoField):
    """TINYINT UNSIGNED AUTO_INCREMENT primary key."""

    def db_type(self, connection):
        return "tinyint unsigned AUTO_INCREMENT"

    def rel_db_type(self, connection):
        return "tinyint unsigned"


class DateTime3Field(models.DateTimeField):
    """DATETIME(3), matching the millisecond precision in the SQL schema."""

    def db_type(self, connection):
        return "datetime(3)"


class DatabaseNowDateTime3Field(DateTime3Field):
    """DATETIME(3) with a database CURRENT_TIMESTAMP default."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("db_default", Now())
        super().__init__(*args, **kwargs)


class UpdatedDateTime3Field(DateTime3Field):
    """DATETIME(3) updated to the current UTC time on ORM saves."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("auto_now", True)
        super().__init__(*args, **kwargs)


class FixedCharField(models.CharField):
    """CHAR(n), where the SQL schema intentionally uses fixed-width storage."""

    def db_type(self, connection):
        return f"char({self.max_length})"


class PublicIdField(FixedCharField):
    """36-character UUID text compatible with the schema's CHAR(36)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 36)
        kwargs.setdefault("default", uuid.uuid4)
        kwargs.setdefault("unique", True)
        kwargs.setdefault("editable", False)
        super().__init__(*args, **kwargs)


class VarBinaryField(models.BinaryField):
    """VARBINARY(n), rather than Django's default MySQL LONGBLOB."""

    def db_type(self, connection):
        return f"varbinary({self.max_length})"


class AsciiBinaryCollationField(models.CharField):
    """ASCII VARCHAR using a bytewise collation for opaque FCM tokens."""

    def db_type(self, connection):
        return f"varchar({self.max_length}) CHARACTER SET ascii COLLATE ascii_bin"
