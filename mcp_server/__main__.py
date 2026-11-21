import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from mcp_server.server import server  # noqa: E402  (après django.setup())

if __name__ == "__main__":
    server.run(transport="stdio")
