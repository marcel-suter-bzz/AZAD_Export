import os
from dotenv import load_dotenv
import shelve
import re

from azure.identity import ClientSecretCredential
from msgraph.core import GraphClient

from person import Person


def main():
    load_dotenv()
    app_client = graph_auth()
    with shelve.open(
            filename=os.getenv('DATAPATH') + 'adusers.db',
            flag='c'
    ) as db:
        load_users(app_client, db)


def load_users(app_client, db):
    """
    loads all users from MS Graph
    :param app_client:
    :param db:
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
                    person.cohorts = list_cohorts(groups)
                db[user['mail']] = person

        if '@odata.nextLink' in users:
            users_response = app_client.get(users['@odata.nextLink'])
            users = users_response.json()
        else:
            users = False


def list_cohorts(groups):
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