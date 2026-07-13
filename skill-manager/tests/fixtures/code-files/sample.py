import os

def validate_email(email: str) -> bool:
    return "@" in email

def format_name(first: str, last: str) -> str:
    return f"{first} {last}"

class UserService:
    def get_user(self, user_id: int):
        return {"id": user_id}

    def delete_user(self, user_id: int):
        pass