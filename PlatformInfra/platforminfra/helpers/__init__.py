"""Helpers package for platformInfra."""
from flask import jsonify
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
        else:
            self.response = {'response': 'Failure'}

        if msg is not None:
            response_message = {
                **self.payload,
                **self.response,
                **{'message': msg}
            }
        else:
            response_message = {
                **self.payload,
                **self.response
            }
        rsp = jsonify(response_message)
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


class FakeData(object):
    """Temporary Class to generate fake data on the API for testing."""

    def environmentsGet():
        """Provide a list of environments."""
        env_list = {
            'environments': [
                'ghy543',
                '77h89d',
                's8sf8s'
            ]
        }
        rsp = Response(env_list)
        return rsp.httpResponse(200)

    def environmentsPost(data):
        """Create a new environment."""
        rsp = Response()
        if 'id' and 'application' in data:
            return rsp.httpResponse(200)
        else:
            return rsp.httpResponse(
                400,
                'No id or application provided for environment'
            )

    def environmentsByIdGet(data):
        """Return data about a specific environment."""
        rsp = Response(
            {
                'response': 'Success',
                'id': data['uuid'],
                'application': 'Retail_suite',
                'vm_count': 3
            }
        )
        return rsp.httpResponse(200)

    def environmentsByIdDelete(data):
        """Delete an Environment."""
        rsp = Response()
        if 'uuid' and 'application' in data:
            return rsp.httpResponse(200)
        else:
            return rsp.httpResponse(
                400,
                'No id or application provided for environment'
            )

    def environmentsByIdActionGet(data, action):
        """Carry out a non-state changing action."""
        rsp = Response()
        if action == 'status':
            rsp.payload = {
                    'response': 'Success',
                    'status': 'OK',
                    'application': [
                        {'name': 'Retail_Suite'}
                    ],
                    'resources': [
                        {'loadbalancer': "Creating"},
                        {'network': "Created"},
                        {'vm': [
                            {data['uuid']+'1': 'Creating'},
                            {data['uuid']+'2': 'Starting'},
                            {data['uuid']+'3': 'Stopping'},
                            {data['uuid']+'4': 'Started'},
                            {data['uuid']+'5': 'Stopped'},
                            {data['uuid']+'6': 'Destroying'},
                            {data['uuid']+'7': 'Destroyed'},
                        ]}
                    ]
                }
            return rsp.httpResponse(200)
        else:
            return rsp.httpResponse(
                400,
                'No id or application provided for environment'
            )

    def environmentsByIdActionPut(data, action):
        """Carry out a state changing action on an environemnt in-place."""
        rsp = Response()
        if action == 'start':
            return rsp.httpResponse(200)
        elif action == 'stop':
            return rsp.httpResponse(200)
        elif action == 'rebuild':
            if 'persist_data' in data:
                if data['persist_data'] == 'True':
                    rsp.payload = {
                            'persist_data': 'True'
                        }
                else:
                    rsp.payload = {
                            'persist_data': 'False'
                        }
            else:
                rsp.payload = {
                        'persist_data': 'True'
                    }
            return rsp.httpResponse(200)
        elif action == 'scale':
            return rsp.httpResponse(200)
        else:
            return rsp.httpResponse(
                400,
                "%s is not a valid action" % action
            )
