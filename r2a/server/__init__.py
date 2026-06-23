"""Local web server: a thin HTTP front-end to the engine, and host for the PWA.

Edge module (imports concretes via the factory/runner). This is the Mac-served
app the iPhone opens in a browser per the runtime model; it does not read iCloud
directly — it talks to the same queue/store the worker drains.
"""

from .app import create_app

__all__ = ["create_app"]
