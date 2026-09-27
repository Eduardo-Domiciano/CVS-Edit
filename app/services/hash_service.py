import re
from pathlib import Path

import bcrypt

_BCRYPT_SALT_CHARS = "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BCRYPT_HASH_RE = re.compile(r"^\$2[aby]\$(\d{2})\$")


def is_bcrypt_hash(value: str) -> bool:
    return bool(_BCRYPT_HASH_RE.match(value.strip()))


def extract_bcrypt_cost(value: str) -> int | None:
    match = _BCRYPT_HASH_RE.match(value.strip())
    if not match:
        return None
    return int(match.group(1))


def _to_bcrypt_salt_component(text: str) -> str:
    chars = []
    for char in text:
        if char in _BCRYPT_SALT_CHARS:
            chars.append(char)
        else:
            chars.append(_BCRYPT_SALT_CHARS[ord(char) % len(_BCRYPT_SALT_CHARS)])
        if len(chars) == 22:
            break
    while len(chars) < 22:
        chars.append(".")
    return "".join(chars)


def _empty_bcrypt_salt(cost: int) -> bytes:
    return f"$2b${cost:02d}${'.' * 22}".encode()


def apply_pepper(password: str, pepper: str, position: str = "after") -> str:
    if not pepper:
        return password
    if position == "before":
        return pepper + password
    if position == "both":
        return pepper + password + pepper
    return password + pepper


def create_password_hash(
    password: str,
    cost: int,
    custom_salt: str | None = None,
    *,
    auto_generate_salt: bool = True,
) -> str:
    if custom_salt:
        salt_component = _to_bcrypt_salt_component(custom_salt)
        salt = f"$2b${cost:02d}${salt_component}".encode()
    elif auto_generate_salt:
        salt = bcrypt.gensalt(rounds=cost)
    else:
        salt = _empty_bcrypt_salt(cost)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(
    password: str,
    target_hash: str,
    *,
    pepper: str = "",
    pepper_position: str = "after",
    cost: int = 12,
    custom_salt: str | None = None,
    auto_generate_salt: bool = True,
    use_embedded_salt: bool = True,
) -> bool:
    candidate = apply_pepper(password, pepper, pepper_position)
    encoded = candidate.encode("utf-8")

    if use_embedded_salt and is_bcrypt_hash(target_hash):
        return bcrypt.checkpw(encoded, target_hash.strip().encode("utf-8"))

    generated = create_password_hash(
        candidate,
        cost,
        custom_salt,
        auto_generate_salt=auto_generate_salt,
    )
    return generated == target_hash.strip()


def load_wordlist(path: Path) -> list[str]:
    passwords: list[str] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            entry = line.strip()
            if not entry or entry.startswith("#"):
                continue
            if entry not in seen:
                seen.add(entry)
                passwords.append(entry)
    return passwords
