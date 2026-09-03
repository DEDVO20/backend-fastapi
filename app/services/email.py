from email.message import EmailMessage
import logging
import re
import smtplib
import ssl
from typing import List, Optional

import requests

from ..config import settings
from ..models.usuario import Usuario
from ..models.calidad import AccionCorrectiva

logger = logging.getLogger(__name__)

MENSAJE_SMTP_BLOQUEADO = (
    "Render no puede conectar con Gmail por SMTP (Network is unreachable). "
    "Cree una API key en https://resend.com y agregue RESEND_API_KEY en Render."
)


def _entorno_permite_simulacion() -> bool:
    return settings.ENVIRONMENT.lower() in ("test", "local")


def normalizar_smtp_password(valor: Optional[str]) -> str:
    """Gmail muestra la clave de aplicación con espacios; SMTP no los acepta."""
    return re.sub(r"\s+", "", valor or "")


def es_error_red_smtp(error: Exception) -> bool:
    texto = str(error).lower()
    return any(
        marca in texto
        for marca in (
            "network is unreachable",
            "errno 101",
            "enotunreach",
            "eai_again",
            "name or service not known",
            "connection refused",
        )
    )


class EmailService:
    def __init__(self) -> None:
        self.ultimo_error = ""

    def resend_configurado(self) -> bool:
        return bool((settings.RESEND_API_KEY or "").strip())

    def smtp_configurado(self) -> bool:
        usuario = (settings.SMTP_USER or "").strip()
        password = normalizar_smtp_password(settings.SMTP_PASSWORD)
        return bool(settings.SMTP_HOST and usuario and password)

    def envio_configurado(self) -> bool:
        return self.resend_configurado() or self.smtp_configurado()

    def _enviar_resend(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        html: Optional[str],
    ) -> bool:
        clave = (settings.RESEND_API_KEY or "").strip()
        remitente = (settings.RESEND_FROM or settings.SMTP_FROM or "SGC Calidad <beth.t@example.com>").strip()
        payload = {
            "from": remitente,
            "to": [destinatario],
            "subject": asunto,
            "text": cuerpo,
        }
        if html:
            payload["html"] = html
        respuesta = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {clave}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        if respuesta.ok:
            logger.info("Correo OTP enviado por Resend a %s", destinatario)
            return True
        detalle = respuesta.text[:180]
        self.ultimo_error = f"Resend rechazó el envío ({respuesta.status_code}): {detalle}"
        logger.error("Resend error %s: %s", respuesta.status_code, detalle)
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
        """Envía el correo por HTTPS (Resend) o SMTP. En test/local puede simular."""
        self.ultimo_error = ""
        if self.resend_configurado():
            try:
                return self._enviar_resend(destinatario, asunto, cuerpo, html)
            except Exception as exc:
                self.ultimo_error = f"No se pudo contactar Resend: {exc}"[:180]
                logger.exception("Fallo Resend hacia %s", destinatario)
                return False

        if not self.smtp_configurado():
            logger.info("==================================================")
            logger.info("SIMULACIÓN ENVÍO DE CORREO (SMTP/Resend no configurado)")
            logger.info("Para: %s", destinatario)
            logger.info("Asunto: %s", asunto)
            if log_cuerpo:
                logger.info("Cuerpo: %s", cuerpo)
            logger.info("==================================================")
            if _entorno_permite_simulacion():
                return True
            self.ultimo_error = MENSAJE_SMTP_BLOQUEADO
            return False

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

        try:
            if settings.SMTP_PORT == 465:
                contexto = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    settings.SMTP_HOST,
                    settings.SMTP_PORT,
                    timeout=15,
                    context=contexto,
                ) as servidor:
                    servidor.login(usuario, password)
                    servidor.send_message(mensaje)
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as servidor:
                    servidor.ehlo()
                    if settings.SMTP_USE_TLS:
                        servidor.starttls(context=ssl.create_default_context())
                        servidor.ehlo()
                    servidor.login(usuario, password)
                    servidor.send_message(mensaje)
            logger.info("Correo enviado a %s (%s)", destinatario, asunto)
            return True
        except smtplib.SMTPAuthenticationError:
            self.ultimo_error = (
                "Gmail rechazó el usuario o la contraseña. "
                "Use una contraseña de aplicación de 16 letras, sin espacios."
            )
            logger.exception("No se pudo autenticar SMTP hacia %s", destinatario)
            return False
        except TimeoutError:
            self.ultimo_error = MENSAJE_SMTP_BLOQUEADO
            logger.exception("Timeout SMTP hacia %s", destinatario)
            return False
        except Exception as exc:
            if es_error_red_smtp(exc):
                self.ultimo_error = MENSAJE_SMTP_BLOQUEADO
            else:
                texto = str(exc).replace(password, "***") if password else str(exc)
                self.ultimo_error = texto[:180]
            logger.exception("No se pudo enviar el correo a %s", destinatario)
            return False

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
