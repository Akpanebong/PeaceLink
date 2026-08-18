from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DetailView, ListView
from core.models import Activity, Alert
from .forms import CorridorNegotiationOutcomeForm, CorridorNoticeForm, CorridorResponseForm
from .models import CorridorNotice, CorridorResponse, CorridorRoute
from django.views.generic import ListView
from django.db.models import Count, Q


class CorridorListView(ListView):
    model = CorridorNotice
    template_name = "corridors/list.html"
    context_object_name = "notices"

    def get_queryset(self):
        return (
            CorridorNotice.objects
            .select_related(
                "route",
                "submitted_by",
                "route__origin",
                "route__destination",
            )
            .order_by("arrival_date", "-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        active_routes = (
            CorridorRoute.objects
            .filter(active=True)
            .select_related("origin", "destination")
            .annotate(notice_count=Count("notices"))
            .order_by("name")
        )

        context["active_routes"] = active_routes

        context["corridor_stats"] = {
            "total": self.get_queryset().count(),
            "pending": self.get_queryset().filter(
                status=CorridorNotice.Status.PENDING
            ).count(),
            "acknowledged": self.get_queryset().filter(
                status=CorridorNotice.Status.ACKNOWLEDGED
            ).count(),
            "negotiating": self.get_queryset().filter(
                status=CorridorNotice.Status.NEGOTIATING
            ).count(),
        }

        return context


class CorridorDetailView(DetailView):
    model = CorridorNotice
    template_name = "corridors/detail.html"
    context_object_name = "notice"

    def get_queryset(self):
        return CorridorNotice.objects.select_related("route", "submitted_by").prefetch_related("responses__responder")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        responses = list(self.object.responses.select_related("responder"))
        for response in responses:
            response.negotiation_outcome_form = CorridorNegotiationOutcomeForm(instance=response)
        context["responses"] = responses
        return context


class CorridorCreateView(LoginRequiredMixin, CreateView):
    model = CorridorNotice
    form_class = CorridorNoticeForm
    template_name = "corridors/form.html"

    def form_valid(self, form):
        form.instance.submitted_by = self.request.user
        response = super().form_valid(form)
        Alert.objects.create(title="Corridor notice", message=str(self.object), level=Alert.Level.WATCH, action_url=self.object.get_absolute_url())
        Activity.objects.create(actor=self.request.user, verb="Corridor notice sent", detail=str(self.object), accent="amber")
        messages.success(self.request, "Corridor notice sent to community nodes.")
        return response


def respond(request, pk):
    notice = get_object_or_404(CorridorNotice, pk=pk)
    if not request.user.is_authenticated or not request.user.is_community_node:
        messages.error(request, "Only community nodes can acknowledge or negotiate routes after local consultation.")
        return redirect(notice)
    form = CorridorResponseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        response = form.save(commit=False)
        response.notice = notice
        response.responder = request.user
        response.save()
        notice.status = CorridorNotice.Status.ACKNOWLEDGED if response.response_type == "acknowledge" else CorridorNotice.Status.NEGOTIATING
        notice.save(update_fields=["status", "updated_at"])
        messages.success(request, "Route response recorded.")
        return redirect(notice)
    return render(request, "corridors/response_form.html", {"form": form, "title": "Route Response", "notice": notice})


@login_required
def update_negotiation_outcome(request, pk):
    response = get_object_or_404(CorridorResponse.objects.select_related("notice", "responder"), pk=pk)
    notice = response.notice
    can_update = request.user == response.responder or request.user.is_staff or request.user.is_superuser
    if response.response_type != "negotiate" or not request.user.is_community_node or not can_update:
        messages.error(request, "Only the negotiating community node can update the final corridor decision.")
        return redirect(notice)
    if request.method == "POST":
        form = CorridorNegotiationOutcomeForm(request.POST, instance=response)
        if form.is_valid():
            form.save()
            messages.success(request, "Final negotiation response updated.")
        else:
            for error in form.errors.get("negotiation_outcome", []):
                messages.error(request, error)
    return redirect(f"{notice.get_absolute_url()}#response-{response.pk}")
