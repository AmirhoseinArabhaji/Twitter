import pickle
from django.conf import settings


def pickle_input(function):
    def wrapper(*args, **kwargs):

        celery_kwargs = kwargs.pop('celery_kwargs', {})
        running_async = celery_kwargs.pop('apply_async', settings.RUNNING_TASK_ASYNC)

        args = list(args)
        for index, arg in enumerate(args):
            args[index] = pickle.dumps(arg)

        for key, value in kwargs.items():
            kwargs[key] = pickle.dumps(value)

        if running_async:
            function.apply_async(args=[*args], kwargs={**kwargs}, **celery_kwargs)
        else:
            function(*args, **kwargs)

    return wrapper
