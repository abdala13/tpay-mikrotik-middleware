import logging
import os
import sys
import traceback

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

try:
    from trustlens import create_app
    app = create_app()
    logging.info("TrustLens AI WSGI app loaded successfully.")
except Exception as exc:
    logging.error("TrustLens AI failed during startup: %s", exc)
    traceback.print_exc(file=sys.stderr)
    raise
