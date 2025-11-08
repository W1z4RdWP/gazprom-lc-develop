from django import template

register = template.Library()

@register.filter
def pagination_range(page, padding=2):
    start = max(1, page.number - padding)
    end = min(page.paginator.num_pages, page.number + padding)
    return range(start, end + 1)