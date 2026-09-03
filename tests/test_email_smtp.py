"""Pruebas del envío SMTP del OTP."""
from app.services.email import EmailService, es_error_red_smtp, normalizar_smtp_password


def test_normalizar_smtp_password_quita_espacios_de_gmail():
    assert normalizar_smtp_password("abcd efgh ijkl mnop") == "abcdefghijklmnop"
    assert normalizar_smtp_password("  abcd  ") == "abcd"
    assert normalizar_smtp_password(None) == ""
    assert len(normalizar_smtp_password("xxxx xxxx xxxx xxxx")) == 16


def test_es_error_red_smtp_detecta_errno_101():
    assert es_error_red_smtp(OSError(101, "Network is unreachable"))
    assert es_error_red_smtp(TimeoutError("[Errno 101] Network is unreachable"))
    assert not es_error_red_smtp(Exception("authentication failed"))


def test_es_error_red_smtp_detecta_causa_anidada():
    red = OSError(101, "Network is unreachable")
    envuelto = Exception("fallo SMTP")
    envuelto.__cause__ = red
    assert es_error_red_smtp(envuelto)


def test_intentos_smtp_prueba_587_y_465():
    intentos = EmailService()._intentos_smtp()
    assert intentos[0][0] in {587, 465}
    puertos = {puerto for puerto, _ssl in intentos}
    assert 587 in puertos
    assert 465 in puertos


def test_smtp_red_inaccesible_pide_resend(monkeypatch):
    from unittest.mock import patch

    from app.config import settings
    from app.services.email import MENSAJE_SMTP_BLOQUEADO

    monkeypatch.setattr(settings, "RESEND_API_KEY", None)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(settings, "SMTP_USER", "calidad.iudc@gmail.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "abcdefghijklmnop")
    servicio = EmailService()
    with patch.object(
        servicio,
        "_enviar_por_smtp",
        side_effect=OSError(101, "Network is unreachable"),
    ):
        enviado = servicio.enviar_correo_sync(
            "dest@example.com",
            "asunto",
            "cuerpo",
            log_cuerpo=False,
        )
    assert enviado is False
    assert servicio.ultimo_error == MENSAJE_SMTP_BLOQUEADO
