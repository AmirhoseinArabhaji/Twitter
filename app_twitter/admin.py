from django.contrib import admin
from . import models

admin.site.register(models.Hashtag)
admin.site.register(models.Tweet)
admin.site.register(models.Fellowship)
admin.site.register(models.Conversation)
admin.site.register(models.BlockList)
admin.site.register(models.Mention)
admin.site.register(models.WaitingForResponse)
