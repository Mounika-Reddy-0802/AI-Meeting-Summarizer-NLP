"""Create a login from the command line.

python scripts/create_user.py --email you@example.com --name "Your Name"
"""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.auth import hash_password  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.models import User  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--password", help="prompted for if omitted")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password (min 8 characters): ")
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return 1

    init_db()
    email = args.email.strip().lower()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)) is not None:
            print(f"{email} already exists.")
            return 1
        db.add(User(email=email, name=args.name.strip(), password_hash=hash_password(password)))
        db.commit()
    print(f"Created {email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
