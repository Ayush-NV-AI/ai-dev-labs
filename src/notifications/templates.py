from src.notifications.models import NotificationTemplate


class TemplateNotFound(Exception):
    pass


class TemplateRenderError(Exception):
    pass


_TEMPLATES: dict[str, NotificationTemplate] = {
    "reservation_confirmed": NotificationTemplate(
        key="reservation_confirmed",
        channel="email",
        subject="Your reservation is confirmed",
        body=(
            "Hi {customer_name}, your reservation for {resource_name} "
            "starting {starts_at} is confirmed."
        ),
    ),
    "reservation_changed": NotificationTemplate(
        key="reservation_changed",
        channel="email",
        subject="Your reservation has changed",
        body=(
            "Hi {customer_name}, your reservation for {resource_name} "
            "has been updated. New start time: {starts_at}."
        ),
    ),
    "reservation_cancelled": NotificationTemplate(
        key="reservation_cancelled",
        channel="email",
        subject="Your reservation was cancelled",
        body="Hi {customer_name}, your reservation for {resource_name} has been cancelled.",
    ),
    "reservation_reminder": NotificationTemplate(
        key="reservation_reminder",
        channel="email",
        subject="Upcoming reservation reminder",
        body=(
            "Hi {customer_name}, your reservation for {resource_name} "
            "starts soon at {starts_at}."
        ),
    ),
}


def get_template(template_key: str) -> NotificationTemplate:
    template = _TEMPLATES.get(template_key)
    if template is None:
        raise TemplateNotFound(template_key)
    return template


def render(template_key: str, context: dict) -> tuple[str, str]:
    template = get_template(template_key)
    try:
        subject = template.subject.format(**context)
        body = template.body.format(**context)
    except KeyError as exc:
        raise TemplateRenderError(f"missing context key: {exc}") from exc
    return subject, body
