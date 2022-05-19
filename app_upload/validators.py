import imghdr
from urllib.parse import urlparse

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

VALID_IMAGE_EXTENSIONS = [
    'jpeg',
    'png',
    'jpg'
]


def twitter_image_url_validator(urls):
    if not urls:
        return
    for url in urls:
        obj = urlparse(url)
        if obj.netloc != settings.HOST:
            raise ValidationError(_('Enter a valid image URL A valid image URL must be hosted in our website'))


def image_format_validation(value):
    what = imghdr.what(value)
    if what not in VALID_IMAGE_EXTENSIONS:
        raise ValidationError(_('Uploaded file is not a valid image.A valid image format must be jpg, jpeg or png'))
