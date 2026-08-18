from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class CommunityNodeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_community_node


class CoordinatorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.can_manage_intelligence
