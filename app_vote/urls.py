from django.urls import path

from app_vote.views import VoteUpdateAPIView

app_name = 'app_vote'

urlpatterns = [
    path('', VoteUpdateAPIView.as_view(), name='vote')
]
