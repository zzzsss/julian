from flask import render_template, request, jsonify
from . import main

@main.app_errorhandler(401)
def unauthorized(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'unauthorized'})
        response.status_code = 401
        return response
    return render_template('error.html', error="401: unauthorized"), 401

@main.app_errorhandler(500)
def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    return render_template('error.html', error="500: internal-error"), 500

#
# @main.app_errorhandler(403)
# def forbidden(e):
#     if request.accept_mimetypes.accept_json and \
#             not request.accept_mimetypes.accept_html:
#         response = jsonify({'error': 'forbidden'})
#         response.status_code = 403
#         return response
#     return render_template('403.html'), 403
#
#
# @main.app_errorhandler(404)
# def page_not_found(e):
#     if request.accept_mimetypes.accept_json and \
#             not request.accept_mimetypes.accept_html:
#         response = jsonify({'error': 'not found'})
#         response.status_code = 404
#         return response
#     return render_template('404.html'), 404
#
#

