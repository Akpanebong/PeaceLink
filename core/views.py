from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import render, redirect

from agreements.models import Agreement
from conflicts.models import ConflictCase
from corridors.models import CorridorNotice
from trade.models import TradeOffer
from .models import Activity, Alert, Community, Stakeholder
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CommunityForm, StakeholderForm


def home(request):
    # ---------------------------------------------------------
    # COMMUNITY ALERTS
    # ---------------------------------------------------------
    alerts = (
        Alert.objects
        .select_related("community", "assigned_to")
        .order_by("-created_at")
    )

    if request.user.is_authenticated:
        alerts = alerts.filter(
            Q(assigned_to=request.user) |
            Q(assigned_to__isnull=True)
        )
    else:
        alerts = alerts.filter(assigned_to__isnull=True)

    # ---------------------------------------------------------
    # RECENT ACTIVITIES
    # ---------------------------------------------------------
    activities = (
        Activity.objects
        .select_related("actor")
        .order_by("-happened_at")[:8]
    )

    # ---------------------------------------------------------
    # ACTIVE COMMUNITIES
    # ---------------------------------------------------------
    communities = (
        Community.objects
        .filter(is_active=True)
        .order_by("name")[:8]
    )

    # ---------------------------------------------------------
    # DASHBOARD STATISTICS
    # ---------------------------------------------------------
    context = {
        "communities": communities,
        "alerts": alerts[:6],
        "activities": activities,

        "trade_count": TradeOffer.objects.count(),

        "corridor_count": CorridorNotice.objects.count(),

        "resolved_count": (
            ConflictCase.objects
            .filter(stage=ConflictCase.Stage.RESOLVED)
            .count()
        ),

        "member_count": get_user_model().objects.count(),
    }

    return render(request, "core/home.html", context)



def dashboard(request):
    today = timezone.localdate()
    renewal_limit = today + timedelta(days=90)

    # =========================================================
    # BASE QUERYSETS
    # =========================================================

    offers = TradeOffer.objects.all()
    conflicts = ConflictCase.objects.all()
    agreements = Agreement.objects.all()
    corridor_notices = CorridorNotice.objects.all()

    # =========================================================
    # TRADE METRICS
    # =========================================================

    trade_metrics = offers.aggregate(
        total=Count("id"),
        open=Count(
            "id",
            filter=Q(status=TradeOffer.Status.OPEN),
        ),
        matched=Count(
            "id",
            filter=Q(status=TradeOffer.Status.MATCHED),
        ),
        completed=Count(
            "id",
            filter=Q(status=TradeOffer.Status.COMPLETED),
        ),
    )

    # =========================================================
    # CORRIDOR METRICS
    # =========================================================

    corridor_metrics = corridor_notices.aggregate(
        total=Count("id"),
        acknowledged=Count(
            "id",
            filter=Q(
                status=CorridorNotice.Status.ACKNOWLEDGED
            ),
        ),
        pending=Count(
            "id",
            filter=Q(
                status=CorridorNotice.Status.PENDING
            ),
        ),
        negotiating=Count(
            "id",
            filter=Q(
                status=CorridorNotice.Status.NEGOTIATING
            ),
        ),
        closed=Count(
            "id",
            filter=Q(
                status=CorridorNotice.Status.CLOSED
            ),
        ),
    )

    corridor_total = corridor_metrics["total"]

    corridor_ack_rate = (
        round(
            corridor_metrics["acknowledged"]
            * 100
            / corridor_total
        )
        if corridor_total
        else 0
    )

    # =========================================================
    # AGREEMENT METRICS
    # =========================================================

    agreement_metrics = agreements.aggregate(
        total=Count("id"),
        active=Count(
            "id",
            filter=Q(
                status=Agreement.Status.ACTIVE
            ),
        ),
        under_review=Count(
            "id",
            filter=Q(
                status=Agreement.Status.UNDER_REVIEW
            ),
        ),
        breached=Count(
            "id",
            filter=Q(
                status=Agreement.Status.BREACHED
            ),
        ),
        fulfilled=Count(
            "id",
            filter=Q(
                status=Agreement.Status.FULFILLED
            ),
        ),
    )

    # Already expired OR expiring within the next 90 days.
    renewal_due = agreements.filter(
        end_date__isnull=False,
        end_date__lte=renewal_limit,
    ).count()

    # Agreements that have actually expired.
    expired_agreements = agreements.filter(
        end_date__isnull=False,
        end_date__lt=today,
    ).count()

    # Agreements still valid but ending within 90 days.
    expiring_soon = agreements.filter(
        end_date__isnull=False,
        end_date__gte=today,
        end_date__lte=renewal_limit,
    ).count()

    # =========================================================
    # CONFLICT / ADR METRICS
    # =========================================================

    conflict_metrics = conflicts.aggregate(
        total=Count("id"),

        reported=Count(
            "id",
            filter=Q(
                stage=ConflictCase.Stage.REPORTED
            ),
        ),

        assessing=Count(
            "id",
            filter=Q(
                stage=ConflictCase.Stage.ASSESSING
            ),
        ),

        mediating=Count(
            "id",
            filter=Q(
                stage=ConflictCase.Stage.MEDIATING
            ),
        ),

        agreed=Count(
            "id",
            filter=Q(
                stage=ConflictCase.Stage.AGREED
            ),
        ),

        resolved=Count(
            "id",
            filter=Q(
                stage=ConflictCase.Stage.RESOLVED
            ),
        ),

        referred=Count(
            "id",
            filter=Q(
                stage=ConflictCase.Stage.REFERRED
            ),
        ),
    )

    open_cases = (
        conflict_metrics["total"]
        - conflict_metrics["resolved"]
        - conflict_metrics["referred"]
    )

    # =========================================================
    # EARLY WARNING SIGNALS
    # =========================================================

    warnings = (
        conflicts
        .exclude(
            stage__in=[
                ConflictCase.Stage.RESOLVED,
                ConflictCase.Stage.REFERRED,
            ]
        )
        .select_related(
            "community_a",
            "community_b",
            "assigned_node",
        )
        .order_by("-created_at")[:5]
    )

    # =========================================================
    # COMMUNITY TRUST
    # =========================================================

    trust_scores = (
        Community.objects
        .filter(is_active=True)
        .order_by("-trust_score", "name")[:8]
    )

    community_count = Community.objects.filter(
        is_active=True
    ).count()

    # =========================================================
    # ADR PIPELINE
    # =========================================================

    pipeline_counts = {
        ConflictCase.Stage.REPORTED:
            conflict_metrics["reported"],

        ConflictCase.Stage.ASSESSING:
            conflict_metrics["assessing"],

        ConflictCase.Stage.MEDIATING:
            conflict_metrics["mediating"],

        ConflictCase.Stage.AGREED:
            conflict_metrics["agreed"],

        ConflictCase.Stage.RESOLVED:
            conflict_metrics["resolved"],
    }

    pipeline = []

    max_pipeline = max(
        pipeline_counts.values(),
        default=1,
    )

    stage_labels = dict(
        ConflictCase.Stage.choices
    )

    for stage in [
        ConflictCase.Stage.REPORTED,
        ConflictCase.Stage.ASSESSING,
        ConflictCase.Stage.MEDIATING,
        ConflictCase.Stage.AGREED,
        ConflictCase.Stage.RESOLVED,
    ]:
        count = pipeline_counts[stage]

        height = (
            round((count / max_pipeline) * 100)
            if max_pipeline
            else 0
        )

        pipeline.append({
            "key": stage,
            "label": stage_labels[stage],
            "count": count,
            "height": max(height, 8) if count else 8,
        })

    # =========================================================
    # TRADE CATEGORIES
    # =========================================================

    trade_categories = (
        offers
        .values("category")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    # =========================================================
    # CORRIDOR RISK / PENDING NOTICES
    # =========================================================

    route_risks = (
        corridor_notices
        .filter(
            status=CorridorNotice.Status.PENDING
        )
        .select_related(
            "route",
            "route__origin",
            "route__destination",
            "submitted_by",
        )
        .order_by("arrival_date", "-created_at")[:5]
    )

    # =========================================================
    # USER-SPECIFIC CASES
    # =========================================================

    if request.user.is_authenticated:
        private_case_count = conflicts.filter(
            assigned_node=request.user
        ).count()
    else:
        private_case_count = 0

    # =========================================================
    # WEEKLY TRADE VOLUME
    # =========================================================

    week_start = today - timedelta(days=6)

    weekly_trade_rows = (
        offers
        .filter(created_at__date__gte=week_start)
        .values("created_at__date")
        .annotate(total=Count("id"))
        .order_by("created_at__date")
    )

    trade_by_day = {
        row["created_at__date"]: row["total"]
        for row in weekly_trade_rows
    }

    trade_weekly_raw = []

    for offset in range(7):
        day = week_start + timedelta(days=offset)

        trade_weekly_raw.append({
            "date": day,
            "label": day.strftime("%a")[0],
            "value": trade_by_day.get(day, 0),
        })

    max_trade = max(
        [item["value"] for item in trade_weekly_raw],
        default=1,
    )

    trade_weekly = []

    for item in trade_weekly_raw:
        trade_weekly.append({
            **item,
            "percentage": (
                round(
                    item["value"]
                    * 100
                    / max_trade
                )
                if max_trade
                else 0
            ),
        })

    # =========================================================
    # DASHBOARD STATS
    # =========================================================

    stats = [
        {
            "value": trade_metrics["total"],
            "label": "Cross-community trades",
            "delta": (
                f'{trade_metrics["open"]} open · '
                f'{trade_metrics["completed"]} completed'
            ),
        },
        {
            "value": f"{corridor_ack_rate}%",
            "label": "Corridor ack. rate",
            "delta": (
                f'{corridor_metrics["acknowledged"]} '
                f'of {corridor_total} acknowledged'
            ),
        },
        {
            "value": agreement_metrics["active"],
            "label": "Active agreements",
            "delta": f"{renewal_due} renewal due",
        },
        {
            "value": conflict_metrics["resolved"],
            "label": "ADR cases resolved",
            "delta": (
                f"{open_cases} open · "
                f"{conflict_metrics['referred']} referred"
            ),
        },
    ]

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {
        "stats": stats,

        # Header
        "community_count": community_count,

        # Warnings
        "warnings": warnings,

        # Trust
        "trust_scores": trust_scores,

        # Agreements
        "active_agreements": agreement_metrics["active"],
        "renewal_due": renewal_due,
        "expired_agreements": expired_agreements,
        "expiring_soon": expiring_soon,

        # Corridor
        "corridor_ack_rate": corridor_ack_rate,
        "corridor_metrics": corridor_metrics,

        # Conflicts
        "resolved_cases": conflict_metrics["resolved"],
        "open_cases": open_cases,
        "referred_cases": conflict_metrics["referred"],
        "conflict_metrics": conflict_metrics,

        # Pipeline
        "pipeline": pipeline,

        # Trade
        "trade_weekly": trade_weekly,
        "trade_categories": trade_categories,

        # Corridor notices
        "route_risks": route_risks,

        # User
        "private_case_count": private_case_count,
    }

    return render(
        request,
        "core/dashboard.html",
        context,
    )


class CommunityCreateView(LoginRequiredMixin, CreateView):
    model = Community
    form_class = CommunityForm
    template_name = "core/community_form.html"
    success_url = reverse_lazy("home")
    login_url = "login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_community_node:
            messages.error(
                request,
                "Only authorized community nodes can register communities."
            )
            return redirect("conflict_report")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Community "{form.instance.name}" was created successfully.'
        )

        return super().form_valid(form)


class StakeholderCreateView(LoginRequiredMixin, CreateView):
    model = Stakeholder
    form_class = StakeholderForm
    template_name = "core/stakeholder_form.html"
    success_url = reverse_lazy("stakeholder_list")
    login_url = "login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_community_node:
            messages.error(
                request,
                "Only authorized community nodes can register stakeholders."
            )
            return redirect("conflict_report")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Stakeholder "{form.instance.name}" was created successfully.'
        )

        return super().form_valid(form)