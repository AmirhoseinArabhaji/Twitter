from django.core.validators import RegexValidator
from django.utils.translation import gettext as _


class PhoneValidator(RegexValidator):
    message = _(
        'Enter a valid phone number.'
        'A valid phone number must be exactly 11 digits and starts with `09`.'
    )
    regex = r'^09\d{9}$'


phone_number_validator = PhoneValidator()
