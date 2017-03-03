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
                'id': data['id'],
                'application': data['application']
            })
            response.status_code = 200
            return response
        else:
            raise InvalidUsage(
                'No id or application provided for environment',
                status_code=400
            )

    def environmentsByIdGet(data):
        """Return data about a specific environment."""
        response = jsonify(
            {
                'id': data['uuid'],
                'application': 'Retail_Suite',
                'vm_count': 3
            }
        )
        response.status_code = 200
        return response

    def environmentsByIdPut(data):
        """Update a running environment."""
        """
        Builds a new environment alongside the existing
        with the new configuration.
        """
        if 'application' and 'vm_count' in data:
            response = jsonify(
                {
                    'id': data['uuid'],
                    'application': data['application'],
                    'vm_count': data['vm_count']
                }
            )
            response.status_code = 200
            return response
        else:
            raise InvalidUsage(
                'No application or vm_count provided for environment',
                status_code=400)

    def environmentsByIdDelete(data):
        """Delete an Environment."""
        if 'uuid' and 'application' in data:
            response = jsonify(
                {
                    'id': data['uuid'],
                    'application': data['application']
                }
            )
            response.status_code = 200
            return response
        else:
            raise InvalidUsage(
                'No id or application provided for environment',
                status_code=400)

    def environmentsByIdActionGet(data, action):
        """Carry out a non-state changing action."""
        if action == 'status':
            response = jsonify(
                {
                    'uuid': data['uuid'],
                    'application': 'Retail_Suite',
                    'resources': [
                        {'loadbalancer': "OK"},
                        {'network': "OK"},
                        {'vm': [
                            {data['uuid']+'1': 'OK'},
                            {data['uuid']+'2': 'OK'},
                            {data['uuid']+'4': 'OK'}
                        ]}
                    ]
                }
            )
            response.status_code = 200
            return response
        else:
            raise InvalidUsage(
                '%s is not a valid action' % action,
                status_code=400)

    def environmentsByIdActionPut(data, action):
        """Carry out a state changing action on an environemnt in-place."""
        response = jsonify(
            {
                'id': data['uuid'],
                'application': 'Retail_Suite',
                'vm_count': 3,
                'action': action + 'ed'
            }
        )
        response.status_code = 200
        if action == 'start':
            return response
        elif action == 'stop':
            return response
        elif action == 'rebuild':
            response = jsonify(
                {
                    'id': data['uuid'],
                    'application': 'Retail_Suite',
                    'action': action
                }
            )
            response.status_code = 200
            return response
        elif action == 'scale':
            if 'vm_count' in data:
                response = jsonify(
                    {
                        'id': data['uuid'],
                        'application': 'Retail_Suite',
                        'vm_count': data['vm_count'],
                        'action': action
                    }
                )
                response.status_code = 200
                return response
            else:
                raise InvalidUsage(
                    'scale action requires a vm_count',
                    status_code=400)
        else:
            raise InvalidUsage(
                '%s is not a valid action' % action,
                status_code=400)
