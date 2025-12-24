import re

COMMON_PASSWORDS = {
    "password1", "password123", "password2023", "password2024",
    "qwerty123", "qwertyui123", "qazwsxedc123",
    "admin123", "adminadmin123", "administrator1",
    "letmein123", "welcome1", "hello123", "hello1234",
    "monkey123", "dragon123", "sunshine1",
    "12345678a", "123456789a", "1234abcd",
    "abc12345", "abcd1234", "test1234",
    "iloveyou1", "superman1", "trustno11",
    "baseball1", "football1", "qwerty1234",
    "passw0rd", "pass1234", "zaq12wsx",
    "password!", "password1!", "admin123!",
    "welcome123", "login1234", "secret123",
    "admin12345", "user12345", "root12345",
    "changeme1", "changeme123",
    "password01", "password02",
    "q1w2e3r4", "q1w2e3r4t5",
    "asdf1234", "asdfghjk1",
    "1q2w3e4r", "1q2w3e4r5t",
    "11111111a", "aaaaaaaa1",
    "aaaaaaa1", "abcdefg1",
    "password9", "pass12345"
}

def validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Пароль должен быть не короче 8 символов")

    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("Пароль слишком простой")

    if not re.search(r"[a-zA-Z]", password):
        raise ValueError("Пароль должен содержать буквы")

    if not re.search(r"\d", password):
        raise ValueError("Пароль должен содержать цифры")
