from email.message import EmailMessage
import logging
import re
import smtplib
import socket
import ssl
from typing import List, Optional

import requests

from ..config import settings
from ..models.usuario import Usuario
from ..models.calidad import AccionCorrectiva

logger = logging.getLogger(__name__)

REMITENTE_RESEND_SANDBOX = "SGC Calidad <beth.t@example.com>"
_DOMINIOS_REMITENTE_PLACEHOLDER = frozenset(
    {"example.com", "example.org", "example.net", "localhost", "test.com", "invalid"}
)
MENSAJE_SMTP_BLOQUEADO = (
    "No se pudo enviar el código al correo. "
    "En Render agregue BREVO_API_KEY (https://app.brevo.com/settings/keys/api) "
    "y en Brevo verifique el remitente calidad.iudc@gmail.com. "
    "Resend no envía el OTP a todos los usuarios."
)
_ERRORES_RED_SMTP = (
    "network is unreachable",
    "errno 101",
    "enotunreach",
    "eai_again",
    "name or service not known",
    "connection refused",
    "errno 111",
    "errno 113",
    "network unreachable",
    "no route to host",
)


def _entorno_permite_simulacion() -> bool:
    return settings.ENVIRONMENT.lower() in ("test", "local")


def extraer_remitente(valor: Optional[str], respaldo: str = "calidad.iudc@gmail.com") -> tuple[str, str]:
    texto = (valor or "").strip() or respaldo
    coincide = re.match(r"^(.*?)\s*<([^>]+)>$", texto)
    if coincide:
        nombre = coincide.group(1).strip().strip('"') or "SGC Calidad"
        return nombre, coincide.group(2).strip()
    return "SGC Calidad", texto


def es_restriccion_prueba_resend(error: str) -> bool:
    texto = (error or "").lower()
    return any(
        marca in texto
        for marca in (
            "modo prueba",
            "own email",
            "verify a domain",
            "verify your domain",
            "domain is not verified",
            "only send testing",
            "resend.com/domains",
        )
    )


def dominio_del_correo(valor: Optional[str]) -> str:
    _, direccion = extraer_remitente(valor, REMITENTE_RESEND_SANDBOX)
    if "@" not in direccion:
        return ""
    return direccion.rsplit("@", 1)[-1].strip().lower()


def es_remitente_resend_invalido(valor: Optional[str]) -> bool:
    dominio = dominio_del_correo(valor or "")
    return not dominio or dominio in _DOMINIOS_REMITENTE_PLACEHOLDER


def remitente_resend() -> str:
    """Resend no acepta example.com ni Gmail como remitente sin dominio verificado."""
    crudo = (settings.RESEND_FROM or "").strip()
    if es_remitente_resend_invalido(crudo):
        return REMITENTE_RESEND_SANDBOX
    return crudo


def normalizar_smtp_password(valor: Optional[str]) -> str:
    """Gmail muestra la clave de aplicación con espacios; SMTP no los acepta."""
    return re.sub(r"\s+", "", valor or "")


def es_error_red_smtp(error: Exception) -> bool:
    pendientes: list[BaseException] = [error]
    vistos: set[int] = set()
    while pendientes:
        actual = pendientes.pop()
        if actual is None or id(actual) in vistos:
            continue
        vistos.add(id(actual))
        if getattr(actual, "errno", None) in {101, 111, 113, 51}:
            return True
        texto = str(actual).lower()
        if any(marca in texto for marca in _ERRORES_RED_SMTP):
            return True
        for extra in (getattr(actual, "__cause__", None), getattr(actual, "__context__", None)):
            if isinstance(extra, BaseException):
                pendientes.append(extra)
    return False


def _conectar_ipv4(host: str, port: int, timeout: float) -> socket.socket:
    """Render suele fallar por IPv6 (Errno 101). Conectar solo por IPv4."""
    ultimo: Optional[OSError] = None
    try:
        destinos = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
    except OSError as exc:
        raise exc
    for family, socktype, proto, _, sockaddr in destinos:
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(timeout)
        try:
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            ultimo = exc
            sock.close()
    if ultimo:
        raise ultimo
    raise OSError(101, f"Network is unreachable: {host}:{port}")


class SMTPIPv4(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        if self.debuglevel > 0:
            self._print_debug("connect:", (host, port))
        return _conectar_ipv4(host, port, timeout)


class SMTPSSLIPv4(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        if self.debuglevel > 0:
            self._print_debug("connect:", (host, port))
        sock = _conectar_ipv4(host, port, timeout)
        return self.context.wrap_socket(sock, server_hostname=self._host)


class EmailService:
    def __init__(self) -> None:
        self.ultimo_error = ""

    def resend_configurado(self) -> bool:
        return bool((settings.RESEND_API_KEY or "").strip())

    def brevo_configurado(self) -> bool:
        return bool((settings.BREVO_API_KEY or "").strip())

    def smtp_configurado(self) -> bool:
        usuario = (settings.SMTP_USER or "").strip()
        password = normalizar_smtp_password(settings.SMTP_PASSWORD)
        return bool(settings.SMTP_HOST and usuario and password)

    def envio_configurado(self) -> bool:
        return self.brevo_configurado() or self.resend_configurado() or self.smtp_configurado()

    def _post_resend(
        self,
        clave: str,
        remitente: str,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        html: Optional[str],
    ):
        payload = {
            "from": remitente,
            "to": [destinatario],
            "subject": asunto,
            "text": cuerpo,
        }
        if html:
            payload["html"] = html
        return requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {clave}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )

    def _enviar_resend(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        html: Optional[str],
    ) -> bool:
        clave = (settings.RESEND_API_KEY or "").strip()
        remitente = remitente_resend()
        respuesta = self._post_resend(clave, remitente, destinatario, asunto, cuerpo, html)
        if (
            not respuesta.ok
            and es_restriccion_prueba_resend(respuesta.text)
            and "resend.dev" not in remitente.lower()
        ):
            logger.warning(
                "Resend rechazó remitente %s; reintento con %s",
                remitente,
                REMITENTE_RESEND_SANDBOX,
            )
            remitente = REMITENTE_RESEND_SANDBOX
            respuesta = self._post_resend(
                clave, remitente, destinatario, asunto, cuerpo, html
            )
        if respuesta.ok:
            logger.info("Correo OTP enviado por Resend a %s desde %s", destinatario, remitente)
            return True
        detalle = respuesta.text[:240]
        texto = detalle.lower()
        if es_restriccion_prueba_resend(detalle) or "own email" in texto:
            self.ultimo_error = (
                "Resend no puede usar ese remitente (falta verificar el dominio). "
                "En https://resend.com/domains agregue el dominio y en Render ponga "
                "RESEND_FROM con un correo de ese dominio, por ejemplo "
                "SGC Calidad <noreply@su-dominio.com>."
            )
        else:
            self.ultimo_error = f"Resend rechazó el envío ({respuesta.status_code}): {detalle}"
        logger.error("Resend error %s: %s", respuesta.status_code, detalle)
        return False

    def _enviar_brevo(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        html: Optional[str],
    ) -> bool:
        clave = (settings.BREVO_API_KEY or "").strip()
        nombre, correo_remitente = extraer_remitente(
            settings.BREVO_FROM or settings.SMTP_FROM,
            "calidad.iudc@gmail.com",
        )
        payload = {
            "sender": {"name": nombre, "email": correo_remitente},
            "to": [{"email": destinatario}],
            "subject": asunto,
            "textContent": cuerpo,
        }
        if html:
            payload["htmlContent"] = html
        respuesta = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": clave,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        if respuesta.ok:
            logger.info("Correo OTP enviado por Brevo a %s", destinatario)
            return True
        detalle = respuesta.text[:240]
        texto = detalle.lower()
        if "sender" in texto and (
            "not valid" in texto
            or "not verified" in texto
            or "unrecognised" in texto
            or "unrecognized" in texto
            or "does not exist" in texto
        ):
            self.ultimo_error = (
                f"Brevo no tiene verificado el remitente {correo_remitente}. "
                "En https://app.brevo.com/senders agréguelo y confirme el correo."
            )
        elif respuesta.status_code in {401, 403}:
            self.ultimo_error = (
                "Brevo rechazó la API key. En Render revise BREVO_API_KEY "
                "(https://app.brevo.com/settings/keys/api)."
            )
        else:
            self.ultimo_error = f"Brevo rechazó el envío ({respuesta.status_code}): {detalle}"
        logger.error("Brevo error %s: %s", respuesta.status_code, detalle)
        return False

    def enviar_correo_sync(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        *,
        html: Optional[str] = None,
        log_cuerpo: bool = True,
    ) -> bool:
        """Envía el correo por Brevo (HTTPS). Resend no se usa: no llega a todos los Gmail."""
        self.ultimo_error = ""

        if self.brevo_configurado():
            try:
                if self._enviar_brevo(destinatario, asunto, cuerpo, html):
                    return True
            except Exception as exc:
                self.ultimo_error = f"No se pudo contactar Brevo: {exc}"[:180]
                logger.exception("Fallo Brevo hacia %s", destinatario)
            if not self.ultimo_error:
                self.ultimo_error = MENSAJE_SMTP_BLOQUEADO
            return False

        if _entorno_permite_simulacion() and not self.smtp_configurado():
            logger.info("==================================================")
            logger.info("SIMULACIÓN ENVÍO DE CORREO (Brevo no configurado)")
            logger.info("Para: %s", destinatario)
            logger.info("Asunto: %s", asunto)
            if log_cuerpo:
                logger.info("Cuerpo: %s", cuerpo)
            logger.info("==================================================")
            return True

        if self.smtp_configurado() and _entorno_permite_simulacion():
            return self._enviar_smtp_mensaje(destinatario, asunto, cuerpo, html)

        self.ultimo_error = MENSAJE_SMTP_BLOQUEADO
        return False

    def _enviar_smtp_mensaje(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        html: Optional[str],
    ) -> bool:
        usuario = (settings.SMTP_USER or "").strip()
        password = normalizar_smtp_password(settings.SMTP_PASSWORD)
        remitente = (settings.SMTP_FROM or usuario or "noreply@localhost").strip()
        mensaje = EmailMessage()
        mensaje["Subject"] = asunto
        mensaje["From"] = remitente
        mensaje["To"] = destinatario
        mensaje.set_content(cuerpo)
        if html:
            mensaje.add_alternative(html, subtype="html")

        ultimo_red: Optional[Exception] = None
        for puerto, ssl_directo in self._intentos_smtp():
            try:
                self._enviar_por_smtp(mensaje, usuario, password, puerto, ssl_directo)
                logger.info(
                    "Correo enviado a %s (%s) por SMTP %s:%s",
                    destinatario,
                    asunto,
                    settings.SMTP_HOST,
                    puerto,
                )
                return True
            except smtplib.SMTPAuthenticationError:
                self.ultimo_error = (
                    "Gmail rechazó el usuario o la contraseña. "
                    "Use una contraseña de aplicación de 16 letras, sin espacios."
                )
                logger.exception("No se pudo autenticar SMTP hacia %s", destinatario)
                return False
            except Exception as exc:
                if es_error_red_smtp(exc) or isinstance(exc, TimeoutError):
                    ultimo_red = exc
                    logger.warning(
                        "SMTP %s:%s no alcanzable: %s",
                        settings.SMTP_HOST,
                        puerto,
                        exc,
                    )
                    continue
                texto = str(exc).replace(password, "***") if password else str(exc)
                self.ultimo_error = texto[:180]
                logger.exception("No se pudo enviar el correo a %s", destinatario)
                return False

        self.ultimo_error = MENSAJE_SMTP_BLOQUEADO
        logger.error(
            "No se pudo enviar el correo a %s por SMTP: %s",
            destinatario,
            ultimo_red,
        )
        return False

    def _intentos_smtp(self) -> list[tuple[int, bool]]:
        puerto = int(settings.SMTP_PORT or 587)
        ssl_directo = puerto == 465
        intentos = [(puerto, ssl_directo)]
        alterno = (465, True) if puerto != 465 else (587, False)
        if alterno not in intentos:
            intentos.append(alterno)
        return intentos

    def _enviar_por_smtp(
        self,
        mensaje: EmailMessage,
        usuario: str,
        password: str,
        puerto: int,
        ssl_directo: bool,
    ) -> None:
        host = settings.SMTP_HOST or "smtp.gmail.com"
        timeout = 8
        if ssl_directo:
            contexto = ssl.create_default_context()
            with SMTPSSLIPv4(host, puerto, timeout=timeout, context=contexto) as servidor:
                servidor.login(usuario, password)
                servidor.send_message(mensaje)
            return
        with SMTPIPv4(host, puerto, timeout=timeout) as servidor:
            servidor.ehlo()
            if settings.SMTP_USE_TLS or puerto == 587:
                servidor.starttls(context=ssl.create_default_context())
                servidor.ehlo()
            servidor.login(usuario, password)
            servidor.send_message(mensaje)

    async def enviar_correo(self, destinatario: str, asunto: str, cuerpo: str):
        return self.enviar_correo_sync(destinatario, asunto, cuerpo)

    def enviar_codigo_otp(self, destinatario: str, nombre: str, codigo: str) -> bool:
        minutos = settings.OTP_EXPIRE_MINUTES
        asunto = "Código de verificación — Sistema de Gestión de Calidad"
        cuerpo = (
            f"Hola {nombre},\n\n"
            "Tu código de verificación para ingresar al Sistema de Gestión de Calidad es:\n\n"
            f"    {codigo}\n\n"
            f"Este código vence en {minutos} minutos.\n"
            "Si no intentaste iniciar sesión, ignora este mensaje.\n\n"
            "Institución Universitaria de Colombia"
        )
        html = f"""
        <p>Hola {nombre},</p>
        <p>Tu código de verificación para ingresar al Sistema de Gestión de Calidad es:</p>
        <p style="font-size:28px;letter-spacing:6px;font-weight:bold;">{codigo}</p>
        <p>Este código vence en {minutos} minutos. Si no intentaste iniciar sesión, ignora este mensaje.</p>
        """
        log_cuerpo = _entorno_permite_simulacion() and not self.envio_configurado()
        if log_cuerpo:
            logger.info("OTP de desarrollo para %s: %s", destinatario, codigo)
        return self.enviar_correo_sync(
            destinatario,
            asunto,
            cuerpo,
            html=html,
            log_cuerpo=log_cuerpo,
        )

    async def notificar_asignacion_accion(self, accion: AccionCorrectiva, responsable: Usuario):
        """Notificar al responsable que se le ha asignado una acción correctiva"""
        asunto = f"Nueva Acción Correctiva Asignada: {accion.codigo}"
        cuerpo = f"""
        Hola {responsable.nombre},

        Se te ha asignado una nueva acción correctiva.
        
        Código: {accion.codigo}
        Tipo: {accion.tipo}
        Descripción: {accion.descripcion}
        Fecha Compromiso: {accion.fecha_compromiso}

        Por favor ingresa al sistema para revisarla.
        """
        await self.enviar_correo(responsable.correo_electronico, asunto, cuerpo)

    async def notificar_nuevo_comentario(self, accion: AccionCorrectiva, autor: Usuario, comentario: str, destinatarios: List[Usuario]):
        """Notificar un nuevo comentario a los involucrados"""
        asunto = f"Nuevo comentario en Acción {accion.codigo}"
        cuerpo = f"""
        Hola,

        {autor.nombre} ha comentado en la acción {accion.codigo}:

        "{comentario}"

        Ingresa al sistema para responder.
        """
        
        emails_enviados = set()
        for usuario in destinatarios:
            if usuario.id != autor.id and usuario.correo_electronico and usuario.correo_electronico not in emails_enviados:
                await self.enviar_correo(usuario.correo_electronico, asunto, cuerpo)
                emails_enviados.add(usuario.correo_electronico)

email_service = EmailService()
