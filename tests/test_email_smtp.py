"""Pruebas del envío SMTP del OTP."""
from app.services.email import es_error_red_smtp, normalizar_smtp_password


def test_normalizar_smtp_password_quita_espacios_de_gmail():
    assert normalizar_smtp_password("abcd efgh ijkl mnop") == "abcdefghijklmnop"
    assert normalizar_smtp_password("  abcd  ") == "abcd"
    assert normalizar_smtp_password(None) == ""
    assert len(normalizar_smtp_password("xxxx xxxx xxxx xxxx")) == 16


def test_es_error_red_smtp_detecta_errno_101():
    assert es_error_red_smtp(OSError(101, "Network is unreachable"))
    assert not es_error_red_smtp(Exception("authentication failed"))
