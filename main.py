import os
from dotenv import load_dotenv
import shelve
import re

from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient

from group import Group
from person import Person


def main():
    load_dotenv()
    app_client = graph_auth()
    with \
            shelve.open(
                filename=os.getenv('DATAPATH') + 'adusers_new.db',
                flag='c'
            ) as people_db, \
            shelve.open(
                filename=os.getenv('DATAPATH') + 'adgroups_new.db',
                flag='c'
            ) as groups_db:
        load_users(app_client, people_db, groups_db)


def load_users(app_client, people_db, groups_db):
    """
    loads all users from MS Graph
    :param app_client:
    :param people_db:
    :return:
    """
    users = read_users(app_client)
    while users:
        for user in users['value']:
            if user['department'] is not None and \
                    user['givenName'] is not None and \
                    user['surname'] is not None and \
                    user['mail'] is not None and \
                    user['mail'].endswith('@bzz.ch'):
                groups = user['memberOf']
                role = get_role(groups)
                person = Person(
                    email=user['mail'],
                    firstname=user['givenName'],
                    lastname=user['surname'],
                    department=user['department'],
                    cohorts=list(),
                    role=role
                )
                if role == 'student':
                    person.groups = list_groups(groups)
                    group_add(groups_db, person.email, person.groups)
                people_db[user['mail']] = person

        if '@odata.nextLink' in users:
            users_response = app_client.get(users['@odata.nextLink'])
            users = users_response.json()
        else:
            users = False


def group_add(groups_db, email, groups):
    """
    adds the email-address to a group
    :param groups_db:
    :param email:
    :param groups:
    :return:
    """
    for item in groups:
        if item in groups_db:
            group = groups_db[item]
        else:
            group = Group(name=item, students=list())
        group.students.append(email)
        groups_db[item] = group


def list_groups(groups):
    """
    creates a list of all relevant cohorts
    :param groups: Azure AD groups
    :return: list of cohorts
    """
    cohort_list = list()
    for group in groups:
        if re.match(r'[A-Z]{2,3}\d{2}[a-z]', group['displayName']):
            cohort_list.append(group['displayName'])
    return cohort_list


def graph_auth():
    """
    authenticates the app with MS Graph
    :return:
    """
    client_id = os.getenv('AZURECLIENT')
    tenant_id = os.getenv('AZURETENANT')
    client_secret = os.getenv('AZURESECRET')
    client_credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    app_client = GraphClient(credential=client_credential,
                             scopes=['https://graph.microsoft.com/.default'])
    return app_client


def read_users(app_client):
    """
    reads all users from Azure AD
    :param app_client: the authorized app client
    :return: userdata as json
    """
    request_url = '/users?' \
                  '$select=displayName,id,givenname,surname,mail,department' \
                  '&$expand=memberOf'
    # '&$filter=endsWith(mail,\'@bzz.ch\')' \
    # '&$count=true'
    headers = {'ConsistencyLevel': 'eventual'}
    users_response = app_client.get(request_url, headers=headers)
    return users_response.json()


def get_role(groups):
    """
    gets the role of a user
    :param groups: the groups the user is a member of
    :return: "student" / "teacher" / "other"
    """
    for group in groups:
        if group['displayName'] == os.getenv('GRAPHSTUDENTGROUP'):
            return "student"
        if group['displayName'] == os.getenv('GRAPHTEACHERGROUP'):
            return "teacher"
    return "other"


if __name__ == '__main__':
    main()
