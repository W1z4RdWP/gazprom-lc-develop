class DataMixin:
    def __init__(self):
        pass

    def get_mixin_context(self, context, **kwargs):
        context['key'] = 'value'
        context['key'] = 'value'
        context['key'] = 'value'
        context.update(kwargs)
        return context