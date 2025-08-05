"""
WSGI config para PythonAnywhere

INSTRUCCIONES:
1. Copia este contenido completo
2. Ve a tu Web App en PythonAnywhere
3. Click en "WSGI configuration file"
4. BORRA todo el contenido existente
5. PEGA este código
6. CAMBIA "tu-username" por tu usuario real de PythonAnywhere
7. Guarda el archivo (Ctrl+S)
8. Recarga tu web app

EJEMPLO: Si tu usuario es "juan123", cambia:
- /home/tu-username/  →  /home/juan123/
"""

import os
import sys

# CAMBIAR "tu-username" por tu usuario real de PythonAnywhere aquí ↓
path = '/home/tu-username/Ayuda-RRHH-Usuarios'  # ← CAMBIAR AQUÍ
if path not in sys.path:
    sys.path.insert(0, path)

# Configurar Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'proyecto_rrhh.settings'

# CAMBIAR "tu-username" por tu usuario real de PythonAnywhere aquí ↓
activate_this = '/home/tu-username/.virtualenvs/rrhh-env/bin/activate_this.py'  # ← CAMBIAR AQUÍ
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
