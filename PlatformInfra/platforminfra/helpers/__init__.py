"""Helpers package for platformInfra."""
from flask import jsonify
from flask import Response as Rsp
import jenkins
import gitlab
import random
import string


class Helpers(object):
    """Heleprs Class."""

    def randStr(length):
        """Generate random string."""
        return ''.join(
            random.choice(string.ascii_lowercase) for i in range(length)
        )


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
        lastBuildNumber = self.server.get_job_info(
            build)['lastCompletedBuild']['number']
        buildInfo = self.server.get_build_info(build, lastBuildNumber)
        return buildInfo


class Gitlab(object):
    """Class to manage Gitlab interactions."""

    def __init__(self, uri, token):
        """Create a connection to Gitlab."""
        self.conn = gitlab.Gitlab(uri, token)

    def forkProject(self, user, projectId):
        """Fork a project."""
        result = self.conn.project_forks.create(
            {},
            project_id=projectId,
            sudo=user
        )
        return result

    def getProject(self, team, project):
        """Get a single project."""
        projectName = team + '/' + project
        result = self.conn.projects.get(projectName)
        return result

    def createUser(self, uname, name, password, email):
        """Create a new GitLab User."""
        user = self.conn.users.create({
            'email': email,
            'password': password,
            'username': uname,
            'name': name
        })
        return user

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
