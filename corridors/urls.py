from django.urls import path

from . import views

urlpatterns = [
    path("", views.CorridorListView.as_view(), name="corridor_list"),
    path("send/", views.CorridorCreateView.as_view(extra_context={"title": "Send Corridor Notice"}), name="corridor_create"),
    path("<int:pk>/", views.CorridorDetailView.as_view(), name="corridor_detail"),
    path("<int:pk>/respond/", views.respond, name="corridor_respond"),
    path("responses/<int:pk>/final/", views.update_negotiation_outcome, name="corridor_negotiation_outcome"),
]
