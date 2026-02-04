from typing import List, Optional
import logging
from ..models.usuario import Usuario
from ..models.calidad import AccionCorrectiva

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Aquí se inicializaría la conexión SMTP real
        pass

    async def enviar_correo(self, destinatario: str, asunto: str, cuerpo: str):
        """Simula el envío de un correo electrónico"""
        # En producción, aquí iría la lógica real de envío
        logger.info(f"==================================================")
        logger.info(f"📧 SIMULACIÓN ENVÍO DE CORREO")
        logger.info(f"Para: {destinatario}")
        logger.info(f"Asunto: {asunto}")
        logger.info(f"Cuerpo: {cuerpo}")
        logger.info(f"==================================================")
        return True

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
        
        # Evitar enviar correo al autor del comentario
        emails_enviados = set()
        for usuario in destinatarios:
            if usuario.id != autor.id and usuario.correo_electronico and usuario.correo_electronico not in emails_enviados:
                await self.enviar_correo(usuario.correo_electronico, asunto, cuerpo)
                emails_enviados.add(usuario.correo_electronico)

email_service = EmailService()
