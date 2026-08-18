from django.contrib import messages
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView
from django.shortcuts import render
from account.mixins import CommunityNodeRequiredMixin
from core.models import Activity, Stakeholder
from .forms import AgreementForm, AgreementNoticeForm
from .models import Agreement, AgreementNotice
from .utils import queue_agreement_notice
from django.utils import timezone
from datetime import timedelta


class AgreementListView(ListView):
    model = Agreement
    template_name = "agreements/list.html"
    context_object_name = "agreements"

    def get_queryset(self):
        return (Agreement.objects.select_related("community_a","community_b","entered_by",
                                                 ).prefetch_related("notices", "stakeholders"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        agreements = context["agreements"]

        today = timezone.localdate()
        renewal_limit = today + timedelta(days=90)

        context["agreement_stats"] = {
            "active": agreements.filter(
                status=Agreement.Status.ACTIVE
            ).count(),

            "renewal_due": agreements.filter(
                end_date__isnull=False,
                end_date__lte=renewal_limit,
            ).count(),

            "all_time": agreements.count(),
        }

        return context


class AgreementDetailView(DetailView):
    model = Agreement
    template_name = "agreements/detail.html"
    context_object_name = "agreement"

    def get_queryset(self):
        return Agreement.objects.select_related("community_a", "community_b", "entered_by").prefetch_related("notices__stakeholder")


def create(request):

    # Allow access to superusers or community nodes
    if not (request.user.is_superuser or request.user.is_community_node):
        messages.error(
            request,
            "Only community nodes can register mediated agreements."
        )
        return redirect("agreement_list")

    NoticeFormSet = modelformset_factory(
        AgreementNotice,
        form=AgreementNoticeForm,
        extra=3,
        can_delete=False,
    )

    # -------------------------------------------------------------
    # Stakeholders
    # -------------------------------------------------------------
    stakeholders = (
        Stakeholder.objects
        .filter(active=True)
        .order_by("name")
    )

    # -------------------------------------------------------------
    # Data consumed by JavaScript
    # -------------------------------------------------------------
    stakeholder_data = [
        {
            "id": stakeholder.id,
            "holder_id": stakeholder.holder_id or "",
            "name": stakeholder.name or "",
            "designation": stakeholder.designation or "",
            "organization": stakeholder.organization or "",
            "email": stakeholder.email or "",
            "phone": stakeholder.phone or "",
        }
        for stakeholder in stakeholders
    ]

    # -------------------------------------------------------------
    # POST
    # -------------------------------------------------------------
    if request.method == "POST":

        form = AgreementForm(request.POST)

        formset = NoticeFormSet(
            request.POST,
            queryset=AgreementNotice.objects.none(),
            prefix="notices",
        )

        if form.is_valid() and formset.is_valid():

            agreement = form.save(commit=False)

            agreement.entered_by = request.user

            agreement.save()

            notices = formset.save(commit=False)

            for notice in notices:

                if (
                    notice.stakeholder_id
                    and notice.destination
                ):

                    notice.agreement = agreement

                    notice.save()

                    queue_agreement_notice(notice)

            Activity.objects.create(
                actor=request.user,
                verb="Agreement registered",
                detail=agreement.agreement_id,
                accent="sky",
            )

            messages.success(
                request,
                (
                    f"Agreement {agreement.agreement_id} "
                    "registered and stakeholder notices queued."
                )
            )

            return redirect(agreement)

    # -------------------------------------------------------------
    # GET
    # -------------------------------------------------------------
    else:

        form = AgreementForm()

        formset = NoticeFormSet(
            queryset=AgreementNotice.objects.none(),
            prefix="notices",
        )

    # -------------------------------------------------------------
    # Render
    # -------------------------------------------------------------
    return render_agreement_form(
        request,
        form,
        formset,
        stakeholder_data=stakeholder_data,
    )


def render_agreement_form(
    request,
    form,
    formset,
    stakeholder_data=None,
):
    return render(
        request,
        "agreements/form.html",
        {
            "form": form,
            "formset": formset,
            "stakeholder_data": stakeholder_data or [],
            "title": "Register mediated agreement",
        },
    )
