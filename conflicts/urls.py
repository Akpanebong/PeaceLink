from django.urls import path

from . import views

urlpatterns = [
    path("report/", views.report, name="conflict_report"),
    path("cases/", views.CaseListView.as_view(), name="conflict_list"),
    path("cases/<int:pk>/", views.detail, name="conflict_detail"),
    path("stakeholders/", views.StakeholderListView.as_view(), name="stakeholder_list"),
    path("stakeholders/by-type/", views.stakeholders_by_type, name="stakeholders_by_type",),
    path("stakeholders/<str:stakeholder_type>/", views.StakeholderListView.as_view(), name="stakeholder_type_list"),
]
