def is_community_node(user):
    return bool(user and user.is_authenticated and user.is_community_node)


def is_coordinator(user):
    return bool(user and user.is_authenticated and user.can_manage_intelligence)
