from dataclasses import dataclass


@dataclass
class Group:
    """
    a group of students

    author: Marcel Suter
    """

    name: str
    students: list

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
