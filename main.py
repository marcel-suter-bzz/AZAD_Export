import os
from dotenv import load_dotenv
import re

from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient

from group import Group
from person import Person


def main():
    load_dotenv()
    app_client = graph_auth()
    people_list = list()
    groups_dict = dict()
    load_users(app_client, people_list, groups_dict)
    save_users(people_list)
    save_groups(groups_dict)


def load_users(app_client, people_list, groups_dict):
    """
    loads all users from MS Graph
    :param app_client:
    :param people_list:
    :param groups_dict:
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
                    role=role
                )
                if role == 'student':
                    group_add(groups_dict, person.email, list_groups(groups))
                people_list.append(person)
            else:
                pass

        if '@odata.nextLink' in users:
            users_response = app_client.get(users['@odata.nextLink'])
            users = users_response.json()
        else:
            users = False


def group_add(groups_dict, email, groups):
    """
    adds the email-address to a group
    :param groups_dict:
    :param email:
    :param groups:
    :return:
    """
    for item in groups:
        if item in groups_dict:
            group = groups_dict[item]
        else:
            group = Group(name=item, students=list())
            groups_dict[item] = group
        if email not in group.students:
            group.students.append(email)


def list_groups(groups):
    """
    creates a list of all relevant cohorts
    :param groups: Azure AD groups
    :return: list of cohorts
    """
    cohort_list = list()
    for group in groups:
        try:
            if re.match(r'[A-Z]{2,3}\d{2}[a-z]', group['displayName']):
                cohort_list.append(group['displayName'])
        except TypeError:
            pass
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


def save_users(people_list):
    data = '['
    for person in people_list:
        data += person.json + ','
    data = data[:-1] + ']'

    with open(os.getenv('PEOPLEFILE'), 'w', encoding='UTF-8') as file:
        file.write(data)


def save_groups(groups_dict):
    data = '['
    for key in groups_dict:
        data += groups_dict[key].json + ','
    data = data[:-1] + ']'

    with open(os.getenv('GROUPFILE'), 'w', encoding='UTF-8') as file:
        file.write(data)


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
    return "student"


if __name__ == '__main__':
    main()
