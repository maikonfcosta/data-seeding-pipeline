"""PII algorithms for synthetic document generation, verification, and masking."""

import random


def generate_valid_cpf(rng: random.Random) -> str:
    """Generate a syntactically valid Brazilian CPF (11 digits) using deterministic RNG."""
    digits = [rng.randint(0, 9) for _ in range(9)]

    # Compute first verifier digit
    sum_1 = sum(v * (10 - i) for i, v in enumerate(digits))
    remainder_1 = sum_1 % 11
    digit_1 = 0 if remainder_1 < 2 else 11 - remainder_1
    digits.append(digit_1)

    # Compute second verifier digit
    sum_2 = sum(v * (11 - i) for i, v in enumerate(digits))
    remainder_2 = sum_2 % 11
    digit_2 = 0 if remainder_2 < 2 else 11 - remainder_2
    digits.append(digit_2)

    return "".join(map(str, digits))


def is_valid_cpf(cpf: str) -> bool:
    """Verify if a CPF string has valid checksum digits."""
    clean = "".join(c for c in cpf if c.isdigit())
    if len(clean) != 11 or len(set(clean)) == 1:
        return False

    digits = [int(c) for c in clean]
    sum_1 = sum(digits[i] * (10 - i) for i in range(9))
    rem_1 = sum_1 % 11
    d1 = 0 if rem_1 < 2 else 11 - rem_1
    if digits[9] != d1:
        return False

    sum_2 = sum(digits[i] * (11 - i) for i in range(10))
    rem_2 = sum_2 % 11
    d2 = 0 if rem_2 < 2 else 11 - rem_2
    return digits[10] == d2


def generate_valid_cnpj(rng: random.Random) -> str:
    """Generate a syntactically valid Brazilian CNPJ (14 digits) using deterministic RNG."""
    # Standard base 8 digits + standard filial branch 0001
    base = [rng.randint(0, 9) for _ in range(8)]
    digits = [*base, 0, 0, 0, 1]

    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_1 = sum(digits[i] * weights_1[i] for i in range(12))
    rem_1 = sum_1 % 11
    d1 = 0 if rem_1 < 2 else 11 - rem_1
    digits.append(d1)

    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_2 = sum(digits[i] * weights_2[i] for i in range(13))
    rem_2 = sum_2 % 11
    d2 = 0 if rem_2 < 2 else 11 - rem_2
    digits.append(d2)

    return "".join(map(str, digits))


def is_valid_cnpj(cnpj: str) -> bool:
    """Verify if a CNPJ string has valid checksum digits."""
    clean = "".join(c for c in cnpj if c.isdigit())
    if len(clean) != 14 or len(set(clean)) == 1:
        return False

    digits = [int(c) for c in clean]
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_1 = sum(digits[i] * weights_1[i] for i in range(12))
    rem_1 = sum_1 % 11
    d1 = 0 if rem_1 < 2 else 11 - rem_1
    if digits[12] != d1:
        return False

    weights_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_2 = sum(digits[i] * weights_2[i] for i in range(13))
    rem_2 = sum_2 % 11
    d2 = 0 if rem_2 < 2 else 11 - rem_2
    return digits[13] == d2


def mask_cpf(cpf: str) -> str:
    """Apply visual masking to a CPF: 123.***.***-45."""
    clean = "".join(c for c in cpf if c.isdigit())
    if len(clean) != 11:
        return cpf
    return f"{clean[:3]}.***.***-{clean[-2:]}"


def mask_cnpj(cnpj: str) -> str:
    """Apply visual masking to a CNPJ: 12.***.***/0001-34."""
    clean = "".join(c for c in cnpj if c.isdigit())
    if len(clean) != 14:
        return cnpj
    return f"{clean[:2]}.***.***/{clean[8:12]}-{clean[-2:]}"


def mask_email(email: str) -> str:
    """Apply visual masking to an email address: j***e@domain.com."""
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = f"{local[0]}*" if local else "*"
    else:
        masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    return f"{masked_local}@{domain}"
