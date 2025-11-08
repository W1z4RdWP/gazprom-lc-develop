from django import template

register = template.Library()

def accept_moving_to_quiz():
    """Сейчас не используется"""
    is_accepted = True
    return is_accepted
    