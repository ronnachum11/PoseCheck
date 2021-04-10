from os import urandom 
from bson import ObjectId

from application import db


class Session:
    def __init__(self, id:str, start_time=None, end_time=None, total_time=None, screen_distance=[], slump_distance=[], tilt_distance=[], flags=[], posture_score=[]):
        self.id = str(id)
        self.start_time = start_time
        self.end_time = end_time
        self.total_time = total_time
        self.screen_distance = screen_distance # distance from screen
        self.slump_distance = slump_distance # distance from eyes to shoulders
        self.tilt_distance = tilt_distance # distance from ears to eyes
        self.flags = flags
        self.posture_score = posture_score

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(dictionary:dict):
        return Session(str(dictionary.get("id")),
                        dictionary.get("start_time"),
                        dictionary.get("end_time"),
                        dictionary.get("total_time"),
                        dictionary.get("screen_distance"),
                        dictionary.get("slump_distance"),
                        dictionary.get("tilt_distance"),
                        dictionary.get("flags"),
                        dictionary.get("posture_score"),
            )

    def __repr__(self):
        return f"Session('{str(self.id)}')"