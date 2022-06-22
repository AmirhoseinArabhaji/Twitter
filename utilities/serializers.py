from django.forms import ImageField as BaseImageField
from drf_extra_fields.fields import Base64ImageField, Base64FieldMixin
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ImageField as DjangoRestImageField


class HybridImageField(Base64ImageField):

    def __init__(self, *args, **kwargs):
        kwargs.update({'_DjangoImageField': BaseImageField})
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            return DjangoRestImageField.to_internal_value(self, data)
        except ValidationError:
            return Base64FieldMixin.to_internal_value(self, data)
