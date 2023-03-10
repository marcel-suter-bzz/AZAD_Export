from dataclasses import dataclass
from json import dumps


@dataclass
class Person:
    """
    a student or teacher

    author: Marcel Suter
    """

    email: str
    firstname: str
    lastname: str
    department: str
    role: str

    @property
    def __dict__(self):
        return {
            'email': self.email,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'department': self.department,
            'role': self.role
        }

    @property
    def json(self):
        return dumps(self.__dict__)

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value

    @property
    def firstname(self):
        return self._firstname

    @firstname.setter
    def firstname(self, value):
        self._firstname = value

    @property
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, value):
        self._lastname = value

    @property
    def department(self):
        return self._department

    @department.setter
    def department(self, value):
        self._department = value

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, value):
        self._groups = value

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, value):
        self._role = value
