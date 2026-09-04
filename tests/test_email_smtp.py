"""Pruebas del envío SMTP del OTP."""
from app.services.email import (
    EmailService,
    es_error_red_smtp,
    extraer_remitente,
    normalizar_smtp_password,
)


def test_normalizar_smtp_password_quita_espacios_de_gmail():
    assert normalizar_smtp_password("abcd efgh ijkl mnop") == "abcdefghijklmnop"
    assert normalizar_smtp_password("  abcd  ") == "abcd"
    assert normalizar_smtp_password(None) == ""
    assert len(normalizar_smtp_password("xxxx xxxx xxxx xxxx")) == 16


def test_extraer_remitente_nombre_y_correo():
    nombre, correo = extraer_remitente("SGC Calidad <calidad.iudc@gmail.com>")
    assert nombre == "SGC Calidad"
    assert correo == "calidad.iudc@gmail.com"
    assert extraer_remitente("calidad.iudc@gmail.com")[1] == "calidad.iudc@gmail.com"


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
    monkeypatch.setattr(settings, "BREVO_API_KEY", None)
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


def test_resend_modo_prueba_explica_dominio(monkeypatch):
    from unittest.mock import Mock, patch

    from app.config import settings

    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test")
    servicio = EmailService()
    respuesta = Mock()
    respuesta.ok = False
    respuesta.status_code = 403
    respuesta.text = (
        "You can only send testing emails to your own email address. "
        "To send emails to other recipients, please verify a domain at resend.com/domains"
    )
    with patch("app.services.email.requests.post", return_value=respuesta):
        enviado = servicio._enviar_resend("otro@gmail.com", "asunto", "cuerpo", None)
    assert enviado is False
    assert "modo prueba" in servicio.ultimo_error.lower()
    assert "resend.com/domains" in servicio.ultimo_error


def test_brevo_envia_a_cualquier_destinatario(monkeypatch):
    from unittest.mock import Mock, patch

    from app.config import settings

    monkeypatch.setattr(settings, "BREVO_API_KEY", "brevo-test")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
    servicio = EmailService()
    brevo_ok = Mock()
    brevo_ok.ok = True
    brevo_ok.status_code = 201
    brevo_ok.text = "{}"
    with patch("app.services.email.requests.post", return_value=brevo_ok) as post:
        enviado = servicio.enviar_correo_sync(
            "usuario.nuevo@gmail.com",
            "asunto",
            "cuerpo",
            log_cuerpo=False,
        )
    assert enviado is True
    assert post.call_args.kwargs["headers"]["api-key"] == "brevo-test"
