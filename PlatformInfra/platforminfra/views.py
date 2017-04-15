"""Views defines the response to the end user.

Views defines the routes, message format and how errors are handeled.
"""

from platforminfra import app
from platforminfra.helpers import Response
from platforminfra.controller import Controller
from flask import request
from werkzeug.exceptions import HTTPException

root_path = 'api'
api_version = '1.0'
base_path = '/' + root_path + '/' + api_version + '/'


@app.errorhandler(Exception)
def handle_error(e):
    """Handle all Errors."""
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
        rsp = Response({'error':  str(e)})
    elif (e.args and type(e.args[0]) is dict):
        if 'code' in e.args[0]:
            code = e.args[0]['code']
        rsp = Response({'error': e.args[0]['error']})
    else:
        rsp = Response({'error': str(e)})
    return rsp.httpResponse(code)


@app.route(
    base_path + 'environments',
    strict_slashes=False,
    methods=['GET', 'POST']
)
def environments():
    """Get a list of environments."""
    rsp = Response()
    if request.method == 'GET':
        listGetController = Controller()
        response = listGetController.listEnvironments()
    elif request.method == 'POST':
        createPostController = Controller()
        response = createPostController.createEnvironment(request.get_json())
    else:
        raise Exception({'error': 'Not Found', 'code': 404})
    return rsp.httpResponse(response['code'], response['msg'])


@app.route(
    base_path + 'environments/<string:uuid>',
    strict_slashes=False,
    methods=['DELETE']
)
def environmentsById(uuid):
    """DELETE a Specific env."""
    rsp = Response()
    req = dict()
    req['uuid'] = uuid
    if request.method == 'DELETE':
        deleteDeleteController = Controller()
        response = deleteDeleteController.deleteEnvironment(req)
    else:
        raise Exception({'error': 'Not Found', 'code': 404})
    return rsp.httpResponse(response['code'], response['msg'])


@app.route(
    base_path + 'environments/<string:uuid>/<string:action>',
    strict_slashes=False,
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
        response = statusPostController.environmentStatus(req)
    elif request.method == 'PUT' and action == 'rebuild':
        req = request.get_json()
        req['uuid'] = uuid
        rebuildPutController = Controller()
        response = rebuildPutController.rebuildEnvironmentServer(req)
    elif request.method == 'PUT' and action == 'scale':
        req = request.get_json()
        req['uuid'] = uuid
        scalePutController = Controller()
        response = scalePutController.scaleEnvironmentServer(req)
    elif request.method == 'PUT' and (
        action == 'start' or
        action == 'stop'
    ):
        req = request.get_json()
        req['uuid'] = uuid
        stopStartPutController = Controller()
        response = stopStartPutController.environmentServerStopStart(
            req,
            action
        )
    else:
        raise Exception({'error': 'Not Found', 'code': 404})
    return rsp.httpResponse(response['code'], response['msg'])
