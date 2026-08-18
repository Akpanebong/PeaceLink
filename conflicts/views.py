from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from core.models import Activity, Alert, Stakeholder
from .forms import CaseUpdateForm, ConflictReportForm, ReferralForm
from .models import CaseUpdate, ConflictCase, Referral
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Stakeholder
from .services.notifications import notify_referral
from django.db import transaction


def report(request):
    if request.method == "POST":
        form = ConflictReportForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            if request.user.is_authenticated:
                case.reporter = request.user
                if not case.reporter_name:
                    case.reporter_name = request.user.get_full_name() or request.user.username
            case.save()
            Activity.objects.create(actor=request.user if request.user.is_authenticated else None, verb="Conflict reported", detail=case.case_id, accent="purple")
            Alert.objects.create(title="New conflict report", message=f"{case.case_id}: {case.get_conflict_type_display()}", level=Alert.Level.ACTION, action_url=case.get_absolute_url())
            messages.success(request, "Report submitted. A community node will follow up within 24 hours.")
            return redirect("conflict_report")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {"reporter_name": request.user.get_full_name() or request.user.username, "reporter_contact": request.user.phone}
        form = ConflictReportForm(initial=initial)
    return render(request, "conflicts/report.html", {"form": form, "title": "Report a Conflict"})


class CaseListView(LoginRequiredMixin, ListView):
    model = ConflictCase
    template_name = "conflicts/list.html"
    context_object_name = "cases"
    login_url = "login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_community_node:
            messages.error(
                request,
                "Conflict case management is private to community nodes."
            )
            return redirect("conflict_report")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            ConflictCase.objects
            .select_related(
                "community_a",
                "community_b",
                "assigned_node"
            )
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = ConflictCase.objects.all()

        # --------------------------------------------------
        # STAGE COUNTS
        # --------------------------------------------------

        context["reported_count"] = queryset.filter(
            stage=ConflictCase.Stage.REPORTED
        ).count()

        context["assessing_count"] = queryset.filter(
            stage=ConflictCase.Stage.ASSESSING
        ).count()

        context["mediating_count"] = queryset.filter(
            stage=ConflictCase.Stage.MEDIATING
        ).count()

        context["agreed_count"] = queryset.filter(
            stage=ConflictCase.Stage.AGREED
        ).count()

        context["resolved_count"] = queryset.filter(
            stage=ConflictCase.Stage.RESOLVED
        ).count()

        context["referred_count"] = queryset.filter(
            stage=ConflictCase.Stage.REFERRED
        ).count()

        # --------------------------------------------------
        # CONFLICT TYPE COUNTS
        # --------------------------------------------------

        type_counts = (
            queryset
            .values("conflict_type")
            .annotate(total=Count("id"))
        )

        conflict_type_counts = {
            item["conflict_type"]: item["total"]
            for item in type_counts
        }

        context["conflict_type_counts"] = conflict_type_counts

        return context


def detail(request, pk):
    case = get_object_or_404(ConflictCase, pk=pk)
    if not request.user.is_authenticated or not request.user.is_community_node:
        messages.error(request, "Conflict case details are private to community nodes.")
        return redirect("conflict_report")
    update_form = CaseUpdateForm(prefix="update")
    referral_form = ReferralForm(request.POST, prefix="referral")
    if request.method == "POST":
        if "add_update" in request.POST:
            update_form = CaseUpdateForm(request.POST, prefix="update")
            if update_form.is_valid():
                update = update_form.save(commit=False)
                update.case = case
                update.author = request.user
                update.save()
                case.stage = update.stage
                if update.stage == ConflictCase.Stage.RESOLVED:
                    case.resolution_summary = update.note
                if not case.assigned_node:
                    case.assigned_node = request.user
                case.save()
                messages.success(request, "Case update recorded.")
                return redirect(case)
        # elif "add_referral" in request.POST:
        #     referral_form = ReferralForm(request.POST, prefix="referral")
        #     if referral_form.is_valid():
        #         referral = referral_form.save(commit=False)
        #         referral.case = case
        #         referral.save()
        #         print(referral.stakeholder.email)
        #         print(referral.stakeholder.phone)
        #         print(referral.stakeholder.name)
        #         case.stage = ConflictCase.Stage.REFERRED
        #         case.save(update_fields=["stage", "updated_at"])
        #         messages.success(request, "Referral recorded.")
        #         return redirect(case)

        elif "add_referral" in request.POST:

            referral_form = ReferralForm(
                request.POST,
                prefix="referral"
            )

            if referral_form.is_valid():
                with transaction.atomic():
                    referral = referral_form.save(
                        commit=False
                    )

                    referral.case = case
                    referral.save()

                    case.stage = ConflictCase.Stage.REFERRED

                    case.save(
                        update_fields=[
                            "stage",
                            "updated_at"
                        ]
                    )

                    notify_referral(
                        referral=referral,
                        request=request,
                    )

                messages.success(
                    request,
                    "Referral recorded and the stakeholder has been notified."
                )

                return redirect(case)
    return render(request, "conflicts/detail.html", {"case": case, "update_form": update_form, "referral_form": referral_form})


@login_required(login_url='login')
def stakeholders_by_type(request):
    stakeholder_type = request.GET.get("type")

    if not stakeholder_type:
        return JsonResponse({
            "stakeholders": []
        })

    stakeholders = (
        Stakeholder.objects
        .filter(stakeholder_type=stakeholder_type)
        .order_by("name")
    )

    data = [
        {
            "id": stakeholder.pk,
            "name": stakeholder.name,
        }
        for stakeholder in stakeholders
    ]

    return JsonResponse({
        "stakeholders": data
    })


class StakeholderListView(ListView):
    model = Stakeholder
    template_name = "conflicts/stakeholder_list.html"
    context_object_name = "stakeholders"

    def get_queryset(self):
        queryset = (
            Stakeholder.objects
            .prefetch_related("communities")
            .order_by("stakeholder_type", "name")
        )

        stakeholder_type = self.kwargs.get("stakeholder_type")

        if stakeholder_type:
            queryset = queryset.filter(
                stakeholder_type=stakeholder_type
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stakeholder_type = self.kwargs.get("stakeholder_type")

        # All available stakeholder groups
        groups = []

        for value, label in Stakeholder.Type.choices:
            groups.append({
                "value": value,
                "label": label,
                "count": Stakeholder.objects.filter(
                    stakeholder_type=value,
                    active=True
                ).count(),
            })

        context["stakeholder_groups"] = groups
        context["current_type"] = stakeholder_type

        # Current group label
        context["current_type_label"] = None

        if stakeholder_type:
            context["current_type_label"] = dict(
                Stakeholder.Type.choices
            ).get(stakeholder_type)

        return context