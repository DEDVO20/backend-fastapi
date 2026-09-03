from email.message import EmailMessage
import logging
import smtplib
import ssl
from typing import List, Optional

from ..config import settings
from ..models.usuario import Usuario
from ..models.calidad import AccionCorrectiva

logger = logging.getLogger(__name__)


def _entorno_permite_simulacion() -> bool:
    return settings.ENVIRONMENT.lower() in ("test", "local")


class EmailService:
    def smtp_configurado(self) -> bool:
        password = (settings.SMTP_PASSWORD or "").strip()
        return bool(settings.SMTP_HOST and settings.SMTP_USER and password)

    def enviar_correo_sync(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        *,
        html: Optional[str] = None,
        log_cuerpo: bool = True,
    ) -> bool:
        """Envía un correo por SMTP. Si no hay SMTP, solo simula en test/local."""
        if not self.smtp_configurado():
            logger.info("==================================================")
            logger.info("SIMULACIÓN ENVÍO DE CORREO (SMTP no configurado)")
            logger.info("Para: %s", destinatario)
            logger.info("Asunto: %s", asunto)
            if log_cuerpo:
                logger.info("Cuerpo: %s", cuerpo)
            logger.info("==================================================")
            return _entorno_permite_simulacion()

        remitente = settings.SMTP_FROM or settings.SMTP_USER or "noreply@localhost"
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
                    timeout=20,
                    context=contexto,
                ) as servidor:
                    if settings.SMTP_USER:
                        servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
                    servidor.send_message(mensaje)
            else:
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as servidor:
                    if settings.SMTP_USE_TLS:
                        servidor.starttls(context=ssl.create_default_context())
                    if settings.SMTP_USER:
                        servidor.login(settings.SMTP_USER, settings.SMTP_PASSWORD or "")
                    servidor.send_message(mensaje)
            logger.info("Correo enviado a %s (%s)", destinatario, asunto)
            return True
        except Exception:
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
        log_cuerpo = _entorno_permite_simulacion() and not self.smtp_configurado()
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
