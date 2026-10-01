from django.urls import path

from apps.support.views import IssueDetailView, IssueListCreateView

app_name = "support"

urlpatterns = [
    path("issues/", IssueListCreateView.as_view(), name="issue-list-create"),
    path("issues/<str:public_id>/", IssueDetailView.as_view(), name="issue-detail"),
]
