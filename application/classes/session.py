from os import urandom 
from bson import ObjectId

from application import db


class Session:
    def __init__(self, id:str, start_time=None, end_time=None, total_time=None, proximity=[], slump=[], forward_tilt=[], head_tilt=[], shoulder_tilt=[], shoulder_width=[], flags=[], posture_score=[], base_key_points=[]):
        self.id = str(id)
        self.start_time = start_time
        self.end_time = end_time
        self.total_time = total_time
        self.proximity = proximity
        self.slump = slump
        self.forward_tilt = forward_tilt
        self.head_tilt = head_tilt 
        self.shoulder_tilt = shoulder_tilt 
        self.shoulder_width = shoulder_width  
        self.flags = flags
        self.posture_score = posture_score
        self.base_key_points = base_key_points

    def to_dict(self):
        return self.__dict__

    @staticmethod
    def from_dict(dictionary:dict):
        return Session(str(dictionary.get("id")),
                        dictionary.get("start_time"),
                        dictionary.get("end_time"),
                        dictionary.get("total_time"),
                        dictionary.get("proximity"),
                        dictionary.get("slump"),
                        dictionary.get("forward_tilt"),
                        dictionary.get("head_tilt"),
                        dictionary.get("shoulder_tilt"),
                        dictionary.get("shoulder_width"),
                        dictionary.get("flags"),
                        dictionary.get("posture_score"),
                        dictionary.get("base_key_points")
            )

    def __repr__(self):
        return f"Session('{str(self.id)}')"