"""
Schemas Pydantic para documentos
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


# Usuario Schema (anidado)
class UsuarioNested(BaseModel):
    """Schema anidado para información básica de usuario"""
    id: UUID
    nombre: str
    segundoNombre: Optional[str] = Field(None, validation_alias="segundo_nombre")
    primerApellido: Optional[str] = Field(None, validation_alias="primer_apellido")
    segundoApellido: Optional[str] = Field(None, validation_alias="segundo_apellido")
    correoElectronico: Optional[str] = Field(None, validation_alias="correo_electronico")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Documento Schemas
class DocumentoBase(BaseModel):
    codigo: str = Field(..., max_length=100)
    nombre: str = Field(..., max_length=300)
    descripcion: Optional[str] = None
    tipo_documento: str = Field(..., max_length=100)
    ruta_archivo: Optional[str] = None
    version_actual: str = Field(default='1.0', max_length=20)
    estado: str = Field(default='borrador', max_length=50)
    fecha_aprobacion: Optional[datetime] = None
    fecha_vigencia: Optional[datetime] = None
    creado_por: Optional[UUID] = None
    aprobado_por: Optional[UUID] = None
    revisado_por: Optional[UUID] = None


class DocumentoCreate(DocumentoBase):
    @field_validator('creado_por', 'aprobado_por', 'revisado_por', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class DocumentoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=300)
    descripcion: Optional[str] = None
    tipo_documento: Optional[str] = Field(None, max_length=100)
    ruta_archivo: Optional[str] = None
    version_actual: Optional[str] = Field(None, max_length=20)
    estado: Optional[str] = Field(None, max_length=50)
    fecha_aprobacion: Optional[datetime] = None
    fecha_vigencia: Optional[datetime] = None
    aprobado_por: Optional[UUID] = None
    revisado_por: Optional[UUID] = None

    @field_validator('aprobado_por', 'revisado_por', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


# VersionDocumento Schemas
class VersionDocumentoBase(BaseModel):
    documento_id: UUID
    version: str = Field(..., max_length=20)
    descripcion_cambios: Optional[str] = None
    ruta_archivo: Optional[str] = None
    creado_por: Optional[UUID] = None


class VersionDocumentoCreate(VersionDocumentoBase):
    pass


class VersionDocumentoResponse(VersionDocumentoBase):
    id: UUID
    creado_en: datetime
    creador: Optional[UsuarioNested] = None
    
    model_config = ConfigDict(from_attributes=True)


class DocumentoResponse(DocumentoBase):
    id: UUID
    creado_en: datetime
    actualizado_en: datetime
    creador: Optional[UsuarioNested] = None
    revisor: Optional[UsuarioNested] = None
    aprobador: Optional[UsuarioNested] = None
    versiones: Optional[list[VersionDocumentoResponse]] = []
    
    model_config = ConfigDict(from_attributes=True)


# DocumentoProceso Schemas
class DocumentoProcesoCreate(BaseModel):
    documento_id: UUID
    proceso_id: UUID
    tipo_relacion: str = Field(default='asociado', max_length=50)


class DocumentoProcesoResponse(BaseModel):
    id: UUID
    documento_id: UUID
    proceso_id: UUID
    tipo_relacion: str
    creado_en: datetime
    
    model_config = ConfigDict(from_attributes=True)
