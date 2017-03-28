"""Views defines the routes for the platformInfra application."""

from platforminfra import app
from platforminfra.helpers import Response, FakeData
from platforminfra.controller import Controller
from flask import request

root_path = 'api'
api_version = '1.0'
base_path = '/' + root_path + '/' + api_version + '/'
controller = Controller()


@app.route(
    base_path + 'environments',
    methods=['GET', 'POST']
)
def environments():
    """Get a list of environments."""
    rsp = Response()
    if request.method == 'GET':
        return controller.listEnvironments()
    elif request.method == 'POST':
        return controller.createEnvironment(request.get_json())
    else:
        return rsp.httpResponse(404, 'Not Found')


@app.route(
    base_path + 'environments/<string:uuid>',
    methods=['GET', 'PUT', 'DELETE']
)
def environmentsById(uuid):
    """GET, PUT or DELETE a Specific env."""
    rsp = Response()
    req = dict()
    req['uuid'] = uuid
    if request.method == 'GET':
        return FakeData.environmentsByIdGet(req)
    elif request.method == 'DELETE':
        req = request.get_json()
        req['uuid'] = uuid
        return controller.deleteEnvironment(req)
    else:
        return rsp.httpResponse(404, 'Not Found')


@app.route(
    base_path + 'environments/<string:uuid>/<string:action>',
    methods=['GET', 'PUT']
)
def environmentsByIdAction(uuid, action):
    """Action on an environemnt."""
    rsp = Response()
    req = dict()
    req['uuid'] = uuid
    if request.method == 'GET' and action == 'status':
        return FakeData.environmentsByIdActionGet(req, action)
    elif request.method == 'PUT' and (
        action == 'start' or
        action == 'stop' or
        action == 'rebuild' or
        action == 'scale'
    ):
        req = request.get_json()
        req['uuid'] = uuid
        return FakeData.environmentsByIdActionPut(req, action)
    else:
        return rsp.httpResponse(404, 'Not Found')
