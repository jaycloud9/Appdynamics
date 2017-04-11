"""Views defines the routes for the platformInfra application."""

from platforminfra import app
from platforminfra.helpers import Response
from platforminfra.controller import Controller
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
    rsp = Response()
    if request.method == 'GET':
        listGetController = Controller()
        return listGetController.listEnvironments()
    elif request.method == 'POST':
        createPostController = Controller()
        return createPostController.createEnvironment(request.get_json())
    else:
        return rsp.httpResponse(404, 'Not Found')


@app.route(
    base_path + 'environments/<string:uuid>',
    methods=['DELETE']
)
def environmentsById(uuid):
    """DELETE a Specific env."""
    rsp = Response()
    req = dict()
    req['uuid'] = uuid
    if request.method == 'DELETE':
        deleteDeleteController = Controller()
        return deleteDeleteController.deleteEnvironment(req)
    else:
        return rsp.httpResponse(404, 'Not Found')


@app.route(
    base_path + 'environments/<string:uuid>/<string:action>',
    methods=['PUT', 'POST']
)
def environmentsByIdAction(uuid, action):
    """Action on an environemnt."""
    rsp = Response()
    req = dict()
    if request.method == 'POST' and action == 'status':
        req = request.get_json()
        req['uuid'] = uuid
        statusPostController = Controller()
        return statusPostController.environmentStatus(req)
    elif request.method == 'PUT' and action == 'rebuild':
        req = request.get_json()
        req['uuid'] = uuid
        rebuildPutController = Controller()
        return rebuildPutController.rebuildEnvironmentServer(req)
    elif request.method == 'PUT' and action == 'scale':
        req = request.get_json()
        req['uuid'] = uuid
        scalePutController = Controller()
        return scalePutController.scaleEnvironmentServer(req)
    elif request.method == 'PUT' and (
        action == 'start' or
        action == 'stop'
    ):
        req = request.get_json()
        req['uuid'] = uuid
        stopStartPutController = Controller()
        return stopStartPutController.environmentServerStopStart(req, action)
    else:
        return rsp.httpResponse(404, 'Not Found')
