__version__ = "0.0.1"

import cos.cos_accounts.__init__
from cos.worker_portal_csrf_patch import patch as _patch_worker_portal_csrf

_patch_worker_portal_csrf()
