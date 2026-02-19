from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException
from typing import Optional

from ...models.auditoria import HallazgoAuditoria
from ...models.calidad import NoConformidad, AccionCorrectiva
from ...models.historial import HistorialEstado
from ...schemas.calidad import NoConformidadCreate
from ...models.proceso import Proceso

class HallazgoService:
    @staticmethod
    def crear_hallazgo(db: Session, hallazgo_data: dict, usuario_id: UUID) -> HallazgoAuditoria:
        proceso_id = hallazgo_data.get("proceso_id")
        if proceso_id:
            proceso = db.query(Proceso).filter(Proceso.id == proceso_id).first()
            if not proceso:
                raise HTTPException(status_code=400, detail="El proceso especificado no existe")

        hallazgo = HallazgoAuditoria(**hallazgo_data)
        hallazgo.estado = hallazgo.estado or "abierto"
        db.add(hallazgo)
        db.flush()

        if hallazgo.tipo_hallazgo in ("no_conformidad_mayor", "no_conformidad_menor") and hallazgo.no_conformidad_id:
            codigo = f"AC-AUTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            accion = AccionCorrectiva(
                no_conformidad_id=hallazgo.no_conformidad_id,
                codigo=codigo,
                descripcion=f"Acción correctiva para hallazgo {hallazgo.codigo}",
                estado="borrador",
                tipo="correctiva",
                creado_por=usuario_id,
            )
            db.add(accion)

        historial = HistorialEstado(
            entidad_tipo='hallazgo',
            entidad_id=hallazgo.id,
            estado_anterior=None,
            estado_nuevo=hallazgo.estado,
            usuario_id=usuario_id,
            comentario="Creación de hallazgo"
        )
        db.add(historial)
        db.commit()
        db.refresh(hallazgo)
        return hallazgo

    @staticmethod
    def generar_nc(db: Session, hallazgo_id: UUID, usuario_id: UUID) -> NoConformidad:
        # 1. Obtener Hallazgo
        hallazgo = db.query(HallazgoAuditoria).filter(HallazgoAuditoria.id == hallazgo_id).first()
        if not hallazgo:
            raise HTTPException(status_code=404, detail="Hallazgo no encontrado")

        if hallazgo.no_conformidad_id:
            raise HTTPException(status_code=400, detail="El hallazgo ya tiene una No Conformidad asociada")

        # 2. Validar Tipo
        if hallazgo.tipo_hallazgo not in ['no_conformidad_mayor', 'no_conformidad_menor']:
            raise HTTPException(status_code=400, detail="Solo se pueden generar NC para hallazgos de tipo No Conformidad")

        # 3. Crear No Conformidad
        count = db.query(NoConformidad).count()
        year = datetime.now().year
        codigo_nc = f"NC-{year}-{str(count + 1).zfill(3)}"

        nueva_nc = NoConformidad(
            codigo=codigo_nc,
            descripcion=hallazgo.descripcion,
            tipo="Auditoria", # Origen
            fuente=f"Auditoría {hallazgo.auditoria.codigo}",
            detectado_por=usuario_id,
            fecha_deteccion=datetime.now(),
            gravedad="Critica" if hallazgo.tipo_hallazgo == 'no_conformidad_mayor' else "Menor", # Mapping simple
            estado="abierta",
            evidencias=hallazgo.evidencia # Asumiendo string simple por ahora
        )
        
        db.add(nueva_nc)
        db.flush() # Para obtener el ID

        # 4. Vincular
        hallazgo.no_conformidad_id = nueva_nc.id
        
        # 5. Historial
        historial = HistorialEstado(
            entidad_tipo='hallazgo',
            entidad_id=hallazgo.id,
            estado_anterior=hallazgo.estado,
            estado_nuevo=hallazgo.estado, # No cambia estado del hallazgo, solo vincula
            usuario_id=usuario_id,
            comentario=f"Generada No Conformidad {codigo_nc}"
        )
        db.add(historial)
        
        db.commit()
        db.refresh(nueva_nc)
        return nueva_nc

    @staticmethod
    def verificar_hallazgo(db: Session, hallazgo_id: UUID, usuario_id: UUID, resultado: str, estado_nuevo: str = 'cerrado') -> HallazgoAuditoria:
        hallazgo = db.query(HallazgoAuditoria).filter(HallazgoAuditoria.id == hallazgo_id).first()
        if not hallazgo:
            raise HTTPException(status_code=404, detail="Hallazgo no encontrado")

        # Si tiene NC asociada, verificar que esté cerrada
        if hallazgo.no_conformidad_id:
            nc = db.query(NoConformidad).filter(NoConformidad.id == hallazgo.no_conformidad_id).first()
            if nc and nc.estado != 'cerrada':
                 raise HTTPException(status_code=400, detail="La No Conformidad asociada debe estar cerrada antes de cerrar el hallazgo")

        estado_anterior = hallazgo.estado
        hallazgo.verificado_por = usuario_id
        hallazgo.fecha_verificacion = datetime.now()
        hallazgo.resultado_verificacion = resultado
        hallazgo.estado = estado_nuevo

        # Historial
        historial = HistorialEstado(
            entidad_tipo='hallazgo',
            entidad_id=hallazgo.id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            usuario_id=usuario_id,
            comentario=f"Verificación: {resultado}"
        )
        db.add(historial)
        db.commit()
        db.refresh(hallazgo)
        return hallazgo
