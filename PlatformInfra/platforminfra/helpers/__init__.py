"""Helpers package for platformInfra.

This Module contains helper classes for small operations, such as:

- Response Objects
- Gitlab
- Jenkins

And the Helper class containes small routines (single method) such as:
- randStr
"""
from flask import jsonify
from flask import Response as Rsp
import jenkins
import gitlab
from gitlab.exceptions import GitlabCreateError
import random
import string
import re


class Helpers(object):
    """Heleprs Class."""

    def randStr(length):
        """Generate random string.

        :param length: length below 300
        :returns: string.ascii_lowercase string
        :rtype: str
        """
        if length <= 300:
            return ''.join(
                random.choice(string.ascii_lowercase) for i in range(length)
            )
        else:
            raise Exception({
                'error': "randStr must be less than or equal to 300 "
                "Length was {}".format(length),
                'code': 500
            })

    def validString(validate):
        """Given a string Validate it is 'acceptable'.

        :param validate: A string to be validated
        :returns: Boolean
        :rtype: Boolean
        """
        if len(validate) > 15:
            return False
        pattern = re.compile("[a-z0-9-]*")
        match = pattern.search(validate)
        if match.group(0) == validate:
            return True
        else:
            return False


class Response(object):
    """Class to handle responses simply and consistantly."""

    def __init__(self, payload=None):
        """Constructing the ResponseHandler."""
        if payload is not None:
            self.payload = payload
        else:
            self.payload = {}

    def httpResponse(self, status_code, msg=None):
        """Create the response."""
        self.status_code = status_code
        if self.status_code is 200:
            self.response = {'response': 'Success'}
        elif self.status_code is 201:
            self.response = {'response': 'Success'}
        elif self.status_code is 204:
            self.response = None
        else:
            self.response = {'response': 'Failure'}

        response_message = None
        if msg is not None:
            response_message = {
                **self.payload,
                **self.response,
                **{'message': msg}
            }
        elif self.response:
            response_message = {
                **self.payload,
                **self.response
            }

        if response_message:
            rsp = jsonify(response_message)
        else:
            rsp = Rsp()

        rsp.status_code = self.status_code
        rsp.headers['Connection'] = 'close'
        return rsp


class Jenkins(object):
    """Class to manage Jenkins interactions."""

    def __init__(self, connection, user, password):
        """Create a connection to the Server."""
        self.server = jenkins.Jenkins(
            connection,
            username=user,
            password=password
        )

    def runBuildWithParams(self, build, params):
        """Run a build with params and return it's info."""
        self.server.build_job(build, params)

    def getBuildStatus(self, buildName, uuid):
        """Get all of the running jobs back.

        If one of those jobs has a param of uuid return running.
        Else return the last status of the last run job with that param uuid.
        """
        jobs = self.server.get_job_info(buildName, fetch_all_builds=True)
        response = list()
        for job in jobs['builds']:
            jobInfo = self.server.get_build_info(buildName, job['number'])
            jobState = 'RUNNING'
            for action in jobInfo['actions']:
                if 'parameters' in action:
                    for param in action['parameters']:
                        if (
                            param['name'] == "UUID" and
                            param['value'] == uuid
                        ):
                            if jobInfo['result']:
                                jobState = jobInfo['result']
                            response.append({
                                'buildName': buildName,
                                'build': job['number'],
                                'status': jobState
                            })
        return response


class Gitlab(object):
    """Class to manage Gitlab interactions."""

    def __init__(self, uri, token):
        """Create a connection to Gitlab."""
        self.conn = gitlab.Gitlab(uri, token)

    def forkProject(self, user, projectId):
        """Fork a project."""
        try:
            result = self.conn.project_forks.create(
                {},
                project_id=projectId,
                sudo=user
            )
        except GitlabCreateError as e:
            result = {
                'error': "Can't access project with id {}".format(projectId),
                'code': e.response_code
            }
        return result

    def addUserToProjectMembers(self, user, project):
        """Add a user to a project members group."""
        print("Granting Permissions for user to project")
        try:
            print("User id {}".format(user.id))
            print("With Access {}".format(gitlab.DEVELOPER_ACCESS))
            result = self.conn.project_members.create(
                {
                    'user_id': user.id,
                    'access_level': gitlab.DEVELOPER_ACCESS,
                },
                project_id=project.id
            )
        except Exception as e:
            result = {
                'error': e,
                'code': 500
            }
            pass
        return result

    def addHook(self, url, project):
        """Add Hook to Project."""
        print("Adding Hook to {}".format(url))
        try:
            result = self.conn.project_hooks.create(
                {
                    'url': url,
                    'token': '148c508109eba106a4a5827122a348cd',
                    'push_events': 1
                },
                project_id=project.id
            )
        except Exception as e:
            result = {
                'error': e,
                'code': 500
            }
            pass
        print("hook Added")
        return result

    def getProject(self, team, project):
        """Get a single project."""
        projectName = team + '/' + project
        try:
            result = self.conn.projects.get(projectName)
        except GitlabCreateError as e:
            result = {
                'error': "Can't find project {}".format(projectName),
                'code': e.response_code
            }
        return result

    def createUser(self, uname, name, password, email):
        """Create a new GitLab User."""
        try:
            user = self.conn.users.create({
                'email': email,
                'password': password,
                'username': uname,
                'name': name
            })
        except GitlabCreateError as e:
            user = self.getUser(uname)

        return user

    def addSshKey(self, user, key):
        """Add a SSH Key to a User."""
        try:
            k = user.keys.create({'title': 'my_key', 'key': key})
            user.save
        except GitlabCreateError as e:
            k = {'error': 'Invalid SSH Key', 'code': e.response_code}
        return k

    def getUser(self, uname):
        """Get a User."""
        try:
            user = self.conn.users.list(username=uname)[0]
        except:
            print("No User: {}".format(uname))
            return None
        return user.username

    def deleteUser(self, uname):
        """Delete a user."""
        try:
            user = self.conn.users.list(username=uname)[0]
            user.delete()
        except:
            print("No User: {}".format(uname))
            return None
        return user.username
