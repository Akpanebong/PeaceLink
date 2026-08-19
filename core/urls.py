from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("communities/create/", views.CommunityCreateView.as_view(), name="community_create",),
    # Stakeholder
    path("stakeholders/create/", views.StakeholderCreateView.as_view(), name="stakeholder_create",),
]

