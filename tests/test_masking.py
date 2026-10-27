"""Tests for CPF/CNPJ checksum generation, validation and masking algorithms."""

import random

from data_seeding_pipeline.masking.algorithms import (
    generate_valid_cnpj,
    generate_valid_cpf,
    is_valid_cnpj,
    is_valid_cpf,
    mask_cnpj,
    mask_cpf,
    mask_email,
)


def test_cpf_generation_and_validation() -> None:
    rng = random.Random(42)
    for _ in range(50):
        cpf = generate_valid_cpf(rng)
        assert len(cpf) == 11
        assert is_valid_cpf(cpf) is True


def test_invalid_cpfs() -> None:
    assert is_valid_cpf("11111111111") is False
    assert is_valid_cpf("12345678900") is False
    assert is_valid_cpf("short") is False
    assert is_valid_cpf("") is False


def test_cnpj_generation_and_validation() -> None:
    rng = random.Random(123)
    for _ in range(50):
        cnpj = generate_valid_cnpj(rng)
        assert len(cnpj) == 14
        assert is_valid_cnpj(cnpj) is True


def test_invalid_cnpjs() -> None:
    assert is_valid_cnpj("00000000000000") is False
    assert is_valid_cnpj("11111111111111") is False
    assert is_valid_cnpj("12345678000199") is False
    assert is_valid_cnpj("invalid") is False


def test_cpf_masking() -> None:
    cpf = "12345678909"
    masked = mask_cpf(cpf)
    assert masked == "123.***.***-09"
    assert mask_cpf("123") == "123"  # invalid length returns untouched


def test_cnpj_masking() -> None:
    cnpj = "12345678000195"
    masked = mask_cnpj(cnpj)
    assert masked == "12.***.***/0001-95"
    assert mask_cnpj("short") == "short"


def test_email_masking() -> None:
    assert mask_email("johndoe@example.com") == "j*****e@example.com"
    assert mask_email("ab@domain.com") == "a*@domain.com"
    assert mask_email("invalid-email") == "invalid-email"
