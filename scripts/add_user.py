#!/usr/bin/env python3
"""Generate one "email:bcrypt_hash" entry for the Prior Art Tool's login.

Run this yourself — your password is only used locally to compute a hash
and is never sent anywhere or stored anywhere in plaintext.

Usage:
    python scripts/add_user.py

Then send/paste ONLY the printed "email:hash" line to whoever manages the
deployment (e.g. the Render dashboard's APP_USERS environment variable), or
append it yourself, comma-separated, to APP_USERS if you manage it directly.
Nobody else's password is ever contained in what you generate or share.
"""
import getpass
import re
import sys

import bcrypt

DOMAIN = "bmwtechworks.in"


def main() -> None:
    email = input(f"Your work email (must end with @{DOMAIN}): ").strip().lower()
    if not re.match(rf"^[^@\s]+@{re.escape(DOMAIN)}$", email):
        sys.exit(f"Error: email must be a valid @{DOMAIN} address.")

    password = getpass.getpass("Choose a password (input hidden): ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        sys.exit("Error: passwords did not match.")
    if len(password) < 8:
        sys.exit("Error: use at least 8 characters.")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    print("\nAdd this single entry to the APP_USERS environment variable")
    print("(comma-separate it after any existing entries — do NOT share")
    print("your password itself, only this line):\n")
    print(f"{email}:{hashed}")


if __name__ == "__main__":
    main()
