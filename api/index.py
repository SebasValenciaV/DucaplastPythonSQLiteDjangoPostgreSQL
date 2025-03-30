# api/index.py

import os
import traceback
from ducaplast.wsgi import application  # Asegúrate de que esta ruta es correcta
from werkzeug.wrappers import Response

def handler(request, context):
    try:
        # Copia el entorno que Vercel provee en la request
        environ = request.environ.copy()

        response_body = []
        response_status = None
        response_headers = None

        def start_response(status, headers, exc_info=None):
            nonlocal response_status, response_headers
            response_status = status
            response_headers = headers

        # Llama a la aplicación WSGI (tu aplicación Django)
        result = application(environ, start_response)
        try:
            for data in result:
                response_body.append(data)
        finally:
            if hasattr(result, 'close'):
                result.close()

        status_code = int(response_status.split()[0]) if response_status else 500

        return Response(b''.join(response_body), status=status_code, headers=dict(response_headers))
    except Exception:
        # Para depuración (en producción, no expongas el traceback)
        return Response(traceback.format_exc().encode(), status=500, mimetype="text/plain")
