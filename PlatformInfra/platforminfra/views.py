"""Views defines the routes for the platformInfra application."""

from platforminfra import app
from platforminfra.helpers import InvalidUsage, FakeData
from flask import request

root_path = 'api'
api_version = '1.0'
base_path = '/' + root_path + '/' + api_version + '/'


@app.route(
    base_path + 'environments',
    methods=['GET', 'POST']
)
def environments():
    """Get a list of environments."""
    if request.method == 'GET':
        return FakeData.environmentsGet()
    elif request.method == 'POST':
        return FakeData.environmentsPost(request.get_json())
    else:
        raise InvalidUsage('Not supported', status_code=405)


@app.route(
    base_path + 'environments/<string:uuid>',
    methods=['GET', 'PUT', 'DELETE']
)
def environmentsById(uuid):
    """GET, PUT or DELETE a Specific env."""
    req = dict()
    req['uuid'] = uuid
    req['id'] = uuid[0:6]
    req['env_id'] = uuid[6:12]
    if request.method == 'GET':
        return FakeData.environmentsByIdGet(req)
    elif request.method == 'PUT':
        req = request.get_json()
        req['uuid'] = uuid
        req['id'] = uuid[0:6]
        req['env_id'] = uuid[6:12]
        return FakeData.environmentsByIdPut(req)
    elif request.method == 'DELETE':
        req = request.get_json()
        req['uuid'] = uuid
        req['id'] = uuid[0:6]
        req['env_id'] = uuid[6:12]
        return FakeData.environmentsByIdDelete(req)
    else:
        raise InvalidUsage('Not supported', status_code=405)


@app.route(
    base_path + 'environments/<string:uuid>/<string:action>',
    methods=['GET', 'PUT']
)
def environmentsByIdAction(uuid, action):
    """Action on an environemnt."""
    req = dict()
    req['uuid'] = uuid
    req['id'] = uuid[0:6]
    req['env_id'] = uuid[6:12]
    if request.method == 'GET' and action == 'status':
        return FakeData.environmentsByIdActionGet(req, action)
    elif request.method == 'PUT' and (
        action == 'start' or
        action == 'stop' or
        action == 'restart' or
        action == 'scale'
    ):
        req = request.get_json()
        req['uuid'] = uuid
        req['id'] = uuid[0:6]
        req['env_id'] = uuid[6:12]
        return FakeData.environmentsByIdActionPut(req, action)
    else:
        raise InvalidUsage('Not supported', status_code=405)
