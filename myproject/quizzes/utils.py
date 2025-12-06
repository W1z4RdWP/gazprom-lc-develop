class DataMixin:
    def __init__(self):
        pass

    def get_mixin_context(self, context, **kwargs):
        context.update(kwargs)
        return context