from django.urls import path

from . import views

urlpatterns = [
    path("", views.AgreementListView.as_view(), name="agreement_list"),
    path("register/", views.create, name="agreement_create"),
    path("<int:pk>/", views.AgreementDetailView.as_view(), name="agreement_detail"),
]
