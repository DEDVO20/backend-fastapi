"""Pruebas de utilidades de carga masiva de usuarios."""
from types import SimpleNamespace

from app.utils.carga_masiva import (
    generar_plantilla_excel,
    leer_archivo,
    normalizar_nombre_columna,
    parse_documento,
    validar_columnas,
    valor_texto,
)


def test_normaliza_encabezados_en_espanol():
    assert normalizar_nombre_columna("Documento") == "documento"
    assert normalizar_nombre_columna("Correo Electronico") == "correo_electronico"
    assert normalizar_nombre_columna("Contraseña") == "contrasena"
    assert normalizar_nombre_columna("Codigo de Area") == "area_codigo"
    assert normalizar_nombre_columna("Nombre Usuario") == "nombre_usuario"
    assert normalizar_nombre_columna("\ufeffdocumento") == "documento"


def test_lee_csv_con_encabezados_visibles_y_punto_y_coma():
    contenido = (
        "Documento;Nombre;Primer Apellido;Correo Electronico;"
        "Nombre Usuario;Contraseña;Codigo de Area;Roles\n"
        "1001;Ana;Gomez;ana@empresa.com;agomez;Password123;CAL;auxiliar\n"
    ).encode("utf-8")

    df = leer_archivo(contenido, "usuarios.csv")

    assert validar_columnas(df) == []
    assert len(df) == 1
    assert df.iloc[0]["nombre"] == "Ana"
    assert df.iloc[0]["area_codigo"] == "CAL"


def test_parse_documento_acepta_decimales_de_excel():
    assert parse_documento("12345678.0") == 12345678
    assert parse_documento(12345678.0) == 12345678
    assert parse_documento("") is None


def test_valor_texto_ignora_nan_textual():
    assert valor_texto("nan") == ""
    assert valor_texto("  Juan  ") == "Juan"


def test_lee_filas_json_normaliza_encabezados():
    from app.utils.carga_masiva import leer_filas_json

    df = leer_filas_json([
        {
            "Documento": "1001",
            "Nombre": "Ana",
            "Primer Apellido": "Gomez",
            "Correo Electronico": "ana@empresa.com",
            "Nombre Usuario": "agomez",
            "Contraseña": "Password123",
            "Codigo de Area": "CAL",
            "Roles": "auxiliar",
        }
    ])

    assert validar_columnas(df) == []
    assert df.iloc[0]["nombre"] == "Ana"
    assert df.iloc[0]["area_codigo"] == "CAL"


def test_plantilla_excel_incluye_hojas_de_catalogo():
    areas = [SimpleNamespace(codigo="CAL", nombre="Calidad")]
    roles = [SimpleNamespace(clave="auxiliar", nombre="Auxiliar", descripcion="")]

    contenido = generar_plantilla_excel(areas, roles)
    df = leer_archivo(contenido, "plantilla.xlsx")

    assert validar_columnas(df) == []
    assert "area_codigo" in df.columns
    assert df.iloc[0]["area_codigo"] == "CAL"
    assert df.iloc[0]["roles"] == "auxiliar"
