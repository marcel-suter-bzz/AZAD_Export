""" This script reads all users and their groups from Azure AD and saves them to a JSON file. """
import msal
import os
import re

import requests
from dotenv import load_dotenv

from group import Group
from person import Person


def main():
    """
    main function
    """
    load_dotenv()
    people_list = []
    groups_dict = {}

    token = create_token()
    load_users(token, people_list, groups_dict)
    save_users(people_list)
    save_groups(groups_dict)
    pass


def create_token():
    """
    Creates the Entra token for the app
    """
    app_client = msal.ConfidentialClientApplication(
        os.getenv('AZURECLIENT'),
        authority=os.getenv('AZUREAUTHORITY'),
        client_credential=os.getenv('AZURESECRET')
    )

    token = app_client.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])
    if not token:
        print('No suitable token exists in cache. Let\'s get a new one from AAD.')
        token = app_client.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])

    return token


def load_users(token, people_list, groups_dict):
    """
    loads all users from MS Graph
    :param token:
    :param people_list:
    :param groups_dict:
    :return:
    """

    users = read_users(token)
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
            users = read_users(token, users['@odata.nextLink'])
        else:
            users = False


def read_users(token, url=None):
    """
    reads all users from Entra
    :param token: the token for the app
    :return: userdata as json
    """
    if not url:
        url = f'{os.getenv("GRAPHURL")}' \
              f'/users?' \
              '$select=displayName,id,givenname,surname,mail,department' \
              '&$expand=memberOf'
    response = requests.get(
        url=url,
        headers={'Authorization': f'Bearer {token["access_token"]}'}
    )
    return response.json()


def list_groups(groups):
    """
    creates a list of all relevant cohorts
    :param groups: Azure AD groups
    :return: list of cohorts
    """
    cohort_list = list()
    for group in groups:
        try:
            if re.match(r'[A-Z]{2,3}\d{2}[a-z]$', group['displayName']):
                if os.getenv('DEBUG') == 'True':
                    print(f'Processing {group["displayName"]}')
                cohort_list.append(group['displayName'])
            else:
                print(f'Skipping AD Group {group["displayName"]}')
        except TypeError:
            pass
    return cohort_list


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


def get_role(groups):
    """
    gets the role of a user
    :param groups: the groups the user is a member of
    :return: "student" / "teacher" / "other"
    """
    for group in groups:
        if group['displayName'] == os.getenv('GRAPHSTUDENTGROUP'):
            return 'student'
        if group['displayName'] == os.getenv('GRAPHTEACHERGROUP'):
            return 'teacher'

    return 'student'


def save_users(people_list):
    """
    saves the people_list to a JSON file
    """
    data = '['
    for person in people_list:
        data += person.json + ','
    data = data[:-1] + ']'

    with open(os.getenv('PEOPLEFILE'), 'w', encoding='UTF-8') as file:
        file.write(data)


def save_groups(groups_dict):
    """
    saves the groups_dict to a JSON file
    """
    data = '['
    for key in groups_dict:
        data += groups_dict[key].json + ','
    data = data[:-1] + ']'

    with open(os.getenv('GROUPFILE'), 'w', encoding='UTF-8') as file:
        file.write(data)


if __name__ == '__main__':
    main()
