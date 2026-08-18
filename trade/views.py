from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView

from core.models import Activity
from .forms import TradeConnectionAcceptForm, TradeConnectionForm, TradeOfferForm
from .models import TradeConnection, TradeLike, TradeOffer
from .services import notify_trade_connection


class TradeListView(ListView):
    model = TradeOffer
    template_name = "trade/list.html"
    context_object_name = "offers"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            TradeOffer.objects.select_related("owner", "community")
            .prefetch_related("connections", "likes")
            .exclude(status=TradeOffer.Status.CLOSED)
        )
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = TradeOffer.Category.choices
        if self.request.user.is_authenticated:
            context["liked_offer_ids"] = set(
                TradeLike.objects.filter(user=self.request.user, offer__in=context["offers"]).values_list("offer_id", flat=True)
            )
        else:
            context["liked_offer_ids"] = set()
        return context


class TradeDetailView(DetailView):
    model = TradeOffer
    template_name = "trade/detail.html"
    context_object_name = "offer"

    def get_queryset(self):
        return TradeOffer.objects.select_related("owner", "community").prefetch_related(
            "connections__requester",
            "likes",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offer = self.object
        user = self.request.user
        context["connection_form"] = TradeConnectionForm()
        context["can_connect"] = user.is_authenticated and offer.owner_id != user.pk and not offer.is_sold_out
        context["can_view_connections"] = user.is_authenticated and (offer.owner_id == user.pk or user.is_staff or user.is_superuser)
        connections = list(offer.connections.select_related("requester"))
        for connection in connections:
            connection.accept_form = TradeConnectionAcceptForm(instance=connection, offer=offer)
        context["connections"] = connections
        context["like_count"] = offer.likes.count()
        context["remaining_quantity"] = offer.remaining_quantity
        context["user_liked"] = user.is_authenticated and offer.likes.filter(user=user).exists()
        context["has_connected"] = user.is_authenticated and offer.connections.filter(requester=user).exists()
        return context


class TradeCreateView(LoginRequiredMixin, CreateView):
    model = TradeOffer
    form_class = TradeOfferForm
    template_name = "trade/create.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        if not form.instance.community_id:
            form.instance.community = self.request.user.community
        response = super().form_valid(form)
        Activity.objects.create(actor=self.request.user, verb="Trade offer posted", detail=str(self.object), accent="green")
        messages.success(self.request, "Trade offer posted.")
        return response


def connect(request, pk):
    if not request.user.is_authenticated:
        return redirect("login")
    offer = get_object_or_404(TradeOffer, pk=pk)
    if offer.owner_id == request.user.pk:
        messages.info(request, "You cannot connect to your own trade offer.")
        return redirect(offer)
    if offer.is_sold_out:
        messages.info(request, "This trade has been completed because all available quantity has been sold.")
        return redirect(offer)
    if request.method == "POST":
        form = TradeConnectionForm(request.POST)
        if form.is_valid():
            connection, created = TradeConnection.objects.get_or_create(
                offer=offer,
                requester=request.user,
                defaults={"message": form.cleaned_data["message"]},
            )
            if not created:
                connection.message = form.cleaned_data["message"]
                connection.save(update_fields=["message", "updated_at"])
            else:
                notify_trade_connection(connection, request)
            offer.sync_sales_status()
            Activity.objects.create(actor=request.user, verb="Trade connection requested", detail=str(offer), accent="teal")
            messages.success(request, "Connection request sent.")
            return redirect(offer)
    return redirect(offer)


class MatchedTradeListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = TradeOffer
    template_name = "trade/matched.html"
    context_object_name = "offers"
    paginate_by = 12

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        return (TradeOffer.objects.select_related("owner", "community")
                .prefetch_related("connections__requester", "likes")
                .filter(connections__isnull=False).distinct())


@login_required
def accept_connection(request, pk):
    connection = get_object_or_404(TradeConnection.objects.select_related("offer", "requester", "offer__owner"), pk=pk)
    offer = connection.offer
    if not (request.user == offer.owner or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to accept this trade connection.")
        return redirect(offer)
    if request.method != "POST":
        return redirect(offer)

    form = TradeConnectionAcceptForm(request.POST, instance=connection, offer=offer)
    if form.is_valid():
        connection = form.save(commit=False)
        connection.accepted = True
        connection.save(update_fields=["accepted", "quantity_sold", "updated_at"])
        offer.sync_sales_status()
        Activity.objects.create(
            actor=request.user,
            verb="Trade sale accepted",
            detail=f"{connection.quantity_sold} sold for {offer.commodity}",
            accent="green",
        )
        messages.success(request, "Trade connection accepted and quantity sold recorded.")
    else:
        for error in form.errors.get("quantity_sold", []):
            messages.error(request, error)
    return redirect(f"{reverse('trade_detail', kwargs={'pk': offer.pk})}#trade-matches")


def toggle_like(request, pk):
    if not request.user.is_authenticated:
        return redirect("login")
    offer = get_object_or_404(TradeOffer, pk=pk)
    like, created = TradeLike.objects.get_or_create(offer=offer, user=request.user)
    if created:
        messages.success(request, "Trade offer liked.")
    else:
        like.delete()
        messages.success(request, "Trade offer unliked.")
    return redirect(request.POST.get("next") or offer)
