"""Helpers package for platformInfra."""
from platforminfra import app
from flask import jsonify


class InvalidUsage(Exception):
    """InvalidUsage Class for consistent responses to messages."""

    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        """Constructorfor InvalidUsage class."""
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        """Conver to Dictionary."""
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    """Register InvalidUsage Handler with Flask app."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


class FakeData(object):
    """Temporary Class to generate fake data on the API for testing."""

    def environmentsGet():
        """Provide a list of environments."""
        response = jsonify(
            {'environments': [
                'ghy543',
                '77h89d',
                's8sf8s'
            ]}
        )
        response.status_code = 200
        return response

    def environmentsPost(data):
        """Create a new environment."""
        if 'id' and 'application' in data:
            response = jsonify({
                'response': 'Success'
            })
            response.status_code = 200
            return response
        else:
            raise InvalidUsage(
                'No id or application provided for environment',
                status_code=400,
                payload={'response': 'Fail'}
            )

    def environmentsByIdGet(data):
        """Return data about a specific environment."""
        response = jsonify(
            {
                'response': 'Success',
                'id': data['uuid'],
                'application': 'Retail_suite',
                'vm_count': 3
            }
        )
        response.status_code = 200
        return response

    def environmentsByIdDelete(data):
        """Delete an Environment."""
        if 'uuid' and 'application' in data:
            response = jsonify(
                {
                    'response': 'Success'
                }
            )
            response.status_code = 200
            return response
        else:
            raise InvalidUsage(
                'No id or application provided for environment',
                status_code=400,
                payload={'response': 'Fail'}
                )

    def environmentsByIdActionGet(data, action):
        """Carry out a non-state changing action."""
        if action == 'status':
            response = jsonify(
                {
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
            )
            response.status_code = 200
            return response
        else:
            raise InvalidUsage(
                '%s is not a valid action' % action,
                status_code=400,
                payload={'response': 'Fail'}
                )

    def environmentsByIdActionPut(data, action):
        """Carry out a state changing action on an environemnt in-place."""
        response = jsonify(
            {
                'response': 'Success'
            }
        )
        response.status_code = 200
        if action == 'start':
            return response
        elif action == 'stop':
            return response
        elif action == 'rebuild':
            if 'persist_data' in data:
                if data['persist_data'] == 'True':
                    response = jsonify(
                        {
                            'response': 'Success',
                            'persist_data': 'True'
                        }
                    )
                else:
                    response = jsonify(
                        {
                            'response': 'Success',
                            'persist_data': 'False'
                        }
                    )
            else:
                response = jsonify(
                    {
                        'response': 'Success',
                        'persist_data': 'True'
                    }
                )
            return response
        elif action == 'scale':
            return response
        else:
            raise InvalidUsage(
                '%s is not a valid action' % action,
                status_code=400,
                payload={'response': 'Fail'}
                )
