import os
import bcrypt
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.model.user import User


def seed_users():
    db: Session = SessionLocal()

    # ensure tables exist
    Base.metadata.create_all(bind=engine)

    rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))

    for key, value in os.environ.items():
        if not key.endswith("_USERS"):
            continue

        try:
            role_order = int(key.split("_")[0])
        except ValueError:
            continue

        role = key.split("_", 1)[1].replace("_USERS", "").lower()

        entries = [x.strip() for x in value.split(",") if x.strip()]
        for entry in entries:
            if ":" not in entry:
                continue
            username, password = entry.split(":", 1)
            username = username.strip().lower()
            password = password.strip()

            # hash password fresh each time
            salt = bcrypt.gensalt(rounds=rounds)
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), salt
            ).decode("utf-8")

            existing = db.query(User).filter(User.username == username).first()
            if existing:
                # overwrite user info
                existing.role = role
                existing.role_order = role_order
                existing.password_hash = password_hash
                print(f"🔄 Updated user {username} ({role}, {role_order})")
            else:
                user = User(
                    username=username,
                    role=role,
                    role_order=role_order,
                    password_hash=password_hash,
                )
                db.add(user)
                print(f"✅ Created user {username} ({role}, {role_order})")

    db.commit()
    db.close()


if __name__ == "__main__":
    seed_users()
