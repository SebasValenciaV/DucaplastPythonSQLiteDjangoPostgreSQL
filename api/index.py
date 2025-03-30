# api/index.py

import os
from ducaplast.wsgi import application  # Asegúrate de que esta ruta sea correcta
from werkzeug.wrappers import Response

def handler(request, context):
    # Copia el entorno de la request que provee Vercel
    environ = request.environ.copy()

    response_body = []
    response_status = None
    response_headers = None

    def start_response(status, headers, exc_info=None):
        nonlocal response_status, response_headers
        response_status = status
        response_headers = headers

    result = application(environ, start_response)
    try:
        for data in result:
            response_body.append(data)
    finally:
        if hasattr(result, 'close'):
            result.close()

    # Extrae el código de estado
    status_code = int(response_status.split()[0]) if response_status else 500
    return Response(b''.join(response_body), status=status_code, headers=dict(response_headers))
