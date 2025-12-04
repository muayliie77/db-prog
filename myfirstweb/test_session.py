from django.conf import settings
import os
import django
import sys

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myfirstweb.settings")
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore

# Create a session
s = SessionStore()
s["test_key"] = "test_value"
s.create()
session_key = s.session_key
print(f"Created session: {session_key}")

# Retrieve it
s2 = SessionStore(session_key=session_key)
print(f"Retrieved value: {s2.get('test_key')}")

if s2.get("test_key") == "test_value":
    print("Session persistence works.")
else:
    print("Session persistence FAILED.")

