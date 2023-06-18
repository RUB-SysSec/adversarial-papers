import typing
import copy

class FeatureDelta:
    """
    Class for keeping track of what features were changed by a transformer from the specified word dict, so from
    the list of features we wanted to change! No side effects.
    It also saves the words that a transformer marked as not realizable.
    """

    def __init__(self):
        self.changes: typing.Dict[str, int] = {}
        self.unrealizable_words: typing.Set = set()

    # the following is implemented to give access via [] to this object
    def __delitem__(self, key):
        # self.__delattr__(key)
        del self.changes[key]

    def __getitem__(self, key):
        return self.changes[key]

    def __setitem__(self, key, value):
        self.changes[key] = value

    def get_json_dump_output(self) -> typing.Dict[str, typing.Union[typing.Dict, typing.List]]:
        """
        Get the objects of this class as dict, so that it can directly be passed to json.dump.
        """
        out = {
            'changes': copy.deepcopy(self.changes),
            'unrealizable_words': list(copy.deepcopy(self.unrealizable_words))
        }
        return out
