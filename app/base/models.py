# -*- coding: utf-8 -*-

class BaseModel:
    """
    A base model class to be inherited by other models.
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        """
        Convert the model instance to a dictionary.
        """
        return {key: getattr(self, key) for key in self.__dict__}