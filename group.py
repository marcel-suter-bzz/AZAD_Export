from dataclasses import dataclass
from json import dumps


@dataclass
class Group:
    """
    a group of students

    author: Marcel Suter
    """

    name: str
    students: list

    @property
    def __dict__(self):
        return {
            'name': self.name,
            'students': self.students
        }

    @property
    def json(self):
        return dumps(self.__dict__)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def students(self):
        return self._students

    @students.setter
    def students(self, value):
        self._students = value
