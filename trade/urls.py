from django.urls import path

from . import views

urlpatterns = [
    path("", views.TradeListView.as_view(), name="trade_list"),
    path("matched/", views.MatchedTradeListView.as_view(), name="trade_matched"),
    path("post/", views.TradeCreateView.as_view(extra_context={"title": "Post Trade Offer"}), name="trade_create"),
    path("<int:pk>/", views.TradeDetailView.as_view(), name="trade_detail"),
    path("<int:pk>/connect/", views.connect, name="trade_connect"),
    path("<int:pk>/like/", views.toggle_like, name="trade_like"),
    path("connections/<int:pk>/accept/", views.accept_connection, name="trade_accept_connection"),
]
