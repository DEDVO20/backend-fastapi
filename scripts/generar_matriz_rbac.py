from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]
APP_TSX = ROOT / "front-react" / "src" / "App.tsx"
API_DIR = ROOT / "back" / "app" / "api"
OUT = ROOT / "RBAC_MATRIZ_AUTOMATICA.md"


ROLE_PERMISSIONS = {
    "Administrador del Sistema": {
        "sistema.admin",
        "sistema.config",
        "usuarios.gestion",
        "usuarios.crear",
        "usuarios.editar",
        "usuarios.eliminar",
        "usuarios.ver",
    },
    "Coordinador/Gestor de Calidad": {
        "calidad.ver",
        "procesos.admin",
        "documentos.aprobar",
        "documentos.anular",
        "noconformidades.cerrar",
        "auditorias.planificar",
    },
    "Dueno de Proceso/Jefe de Area": {
        "documentos.crear",
        "documentos.revisar",
        "noconformidades.gestion",
        "riesgos.gestion",
    },
    "Auditor Interno/Externo": {
        "auditorias.ejecutar",
        "auditorias.ver",
    },
    "RRHH/Capacitacion": {
        "capacitaciones.gestion",
    },
    "Colaborador General": {
        "documentos.ver",
        "noconformidades.reportar",
        "riesgos.identificar",
        "riesgos.ver",
    },
}

PERMISSION_CATALOG = {
    "capacitaciones.gestion": "Capacitaciones",
    "riesgos.ver": "Riesgos",
    "documentos.revisar": "Documentos",
    "usuarios.eliminar": "Usuarios",
    "usuarios.crear": "Usuarios",
    "documentos.anular": "Documentos",
    "calidad.ver": "Calidad",
    "auditorias.ver": "Auditorias",
    "auditorias.planificar": "Auditorias",
    "documentos.crear": "Documentos",
    "sistema.admin": "Sistema",
    "procesos.admin": "Procesos",
    "riesgos.gestion": "Riesgos",
    "usuarios.gestion": "Usuarios",
    "auditorias.ejecutar": "Auditorias",
    "noconformidades.cerrar": "No Conformidades",
    "sistema.config": "Sistema",
    "documentos.aprobar": "Documentos",
    "documentos.ver": "Documentos",
    "usuarios.editar": "Usuarios",
    "noconformidades.gestion": "No Conformidades",
    "usuarios.ver": "Usuarios",
    "riesgos.identificar": "Riesgos",
    "noconformidades.reportar": "No Conformidades",
}

ROLE_DESIGNATED_MODULES = {
    "Administrador del Sistema": {"Sistema", "Usuarios"},
    "Coordinador/Gestor de Calidad": {"Calidad", "Procesos", "Documentos", "Auditorias", "No Conformidades"},
    "Dueno de Proceso/Jefe de Area": {"Documentos", "No Conformidades", "Riesgos"},
    "Auditor Interno/Externo": {"Auditorias"},
    "RRHH/Capacitacion": {"Capacitaciones"},
    "Colaborador General": {"Documentos", "No Conformidades", "Riesgos"},
}

ALIAS = {
    "sistema.config": {"sistema.config", "sistema.configurar"},
    "usuarios.gestion": {"usuarios.gestion", "usuarios.crear", "usuarios.editar", "usuarios.eliminar"},
    "areas.gestionar": {"areas.gestionar", "procesos.admin"},
    "noconformidades.gestion": {"noconformidades.gestion", "no_conformidades.gestionar", "acciones_correctivas.gestionar"},
    "noconformidades.reportar": {"noconformidades.reportar"},
    "noconformidades.cerrar": {"noconformidades.cerrar"},
    "riesgos.gestion": {"riesgos.gestion", "riesgos.administrar"},
    "capacitaciones.gestion": {"capacitaciones.gestion", "capacitaciones.gestionar"},
}


@dataclass
class FrontRoute:
    path: str
    permissions: list[str]


@dataclass
class ApiEndpoint:
    method: str
    path: str
    source: str
    permissions: list[str]
    auth_only: bool


def expand_permissions(perms: list[str]) -> set[str]:
    expanded: set[str] = set()
    for p in perms:
        expanded.update(ALIAS.get(p, {p}))
    return expanded


def role_can_access(role_perms: set[str], required: list[str], auth_only: bool = False) -> bool:
    if "sistema.admin" in role_perms:
        return True
    if auth_only:
        return True
    if not required:
        return False
    return bool(role_perms.intersection(expand_permissions(required)))


def parse_front_routes() -> list[FrontRoute]:
    lines = APP_TSX.read_text(encoding="utf-8").splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "<Route" in line and "path=" in line:
            block = line.strip()
            while "/>" not in block and i + 1 < len(lines):
                i += 1
                block += " " + lines[i].strip()
            blocks.append(block)
        i += 1

    out: list[FrontRoute] = []
    for block in blocks:
        m_path = re.search(r'path="([^"]+)"', block)
        if not m_path:
            continue
        path = m_path.group(1)
        if path in {"/", "/login", "*"}:
            continue

        perms: list[str] = []
        m_wp = re.search(r"withPermission\([^\[]*\[([^\]]+)\]", block)
        if m_wp:
            perms = re.findall(r'"([^"]+)"', m_wp.group(1))

        out.append(FrontRoute(path=path, permissions=perms))

    dedup = {}
    for r in out:
        dedup[(r.path, tuple(r.permissions))] = r
    return sorted(dedup.values(), key=lambda x: x.path)


def parse_api_endpoints() -> tuple[list[ApiEndpoint], list[ApiEndpoint]]:
    controlled: list[ApiEndpoint] = []
    auth_only: list[ApiEndpoint] = []

    for py in sorted(API_DIR.glob("*.py")):
        text = py.read_text(encoding="utf-8")

        m_prefix = re.search(r'APIRouter\(prefix="([^"]+)"', text)
        prefix = m_prefix.group(1) if m_prefix else ""

        pattern = re.compile(
            r'@router\.(get|post|put|patch|delete)\("([^"]+)"[^\n]*\)\s*\ndef\s+([a-zA-Z0-9_]+)\((.*?)\):',
            re.DOTALL,
        )

        matches = list(pattern.finditer(text))
        for idx, m in enumerate(matches):
            method = m.group(1).upper()
            path = prefix + m.group(2)
            fn_name = m.group(3)
            args = m.group(4)

            start_body = m.end()
            end_body = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            body = text[start_body:end_body]

            perms: list[str] = []

            m_req = re.search(r"require_any_permission\(\[([^\]]+)\]\)", args)
            if m_req:
                perms = re.findall(r'"([^"]+)"', m_req.group(1))

            manual = re.findall(r'rp\.permiso\.codigo\s*==\s*"([^"]+)"', body)
            for p in manual:
                if p not in perms:
                    perms.append(p)

            src = f"{py.name}:{fn_name}"
            ep = ApiEndpoint(method=method, path=path, source=src, permissions=perms, auth_only=False)

            if perms:
                controlled.append(ep)
            else:
                has_current_user = "Depends(get_current_user)" in args
                if has_current_user:
                    ep.auth_only = True
                    auth_only.append(ep)

    controlled.sort(key=lambda x: (x.path, x.method))
    auth_only.sort(key=lambda x: (x.path, x.method))
    return controlled, auth_only


def bool_mark(v: bool) -> str:
    return "SI" if v else "NO"


def md_table_headers(role_names: List[str]) -> str:
    cols = " | ".join(["Recurso", "Permisos requeridos", *role_names])
    sep = " | ".join(["---", "---", *("---" for _ in role_names)])
    return f"| {cols} |\n| {sep} |\n"


def build_matrix() -> str:
    roles = list(ROLE_PERMISSIONS.keys())
    front = parse_front_routes()
    api_controlled, api_auth_only = parse_api_endpoints()

    out: list[str] = []
    out.append("# Matriz RBAC Automatica")
    out.append("")
    out.append(f"Generada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    out.append("")
    out.append("## Roles Base (entrada del usuario)")
    for role, perms in ROLE_PERMISSIONS.items():
        out.append(f"- `{role}`: {', '.join(sorted(perms))}")

    out.append("")
    out.append("## Rutas Frontend")
    out.append(md_table_headers(roles))
    for r in front:
        perms_label = ", ".join(r.permissions) if r.permissions else "SOLO AUTENTICADO"
        marks = [bool_mark(role_can_access(ROLE_PERMISSIONS[role], r.permissions, auth_only=not r.permissions)) for role in roles]
        out.append(f"| `{r.path}` | `{perms_label}` | " + " | ".join(marks) + " |")

    out.append("")
    out.append("## Endpoints Backend con permiso explicito")
    out.append(md_table_headers(roles))
    for ep in api_controlled:
        label = f"`{ep.method} {ep.path}` ({ep.source})"
        perms_label = ", ".join(ep.permissions)
        marks = [bool_mark(role_can_access(ROLE_PERMISSIONS[role], ep.permissions, auth_only=False)) for role in roles]
        out.append(f"| {label} | `{perms_label}` | " + " | ".join(marks) + " |")

    out.append("")
    out.append("## Endpoints Backend solo autenticacion (sin permiso explicito)")
    out.append(f"Total detectados: **{len(api_auth_only)}**")
    out.append("")
    out.append("| Endpoint | Fuente |")
    out.append("| --- | --- |")
    for ep in api_auth_only:
        out.append(f"| `{ep.method} {ep.path}` | `{ep.source}` |")

    out.append("")
    out.append("## Observaciones")
    out.append("- La matriz usa alias de permisos para compatibilidad (`sistema.config/configurar`, `capacitaciones.gestion/gestionar`, etc.).")
    out.append("- `SOLO AUTENTICADO` significa que cualquier usuario activo autenticado puede entrar.")
    out.append("")
    out.append("## Validacion de Modulos Designados por Rol")
    out.append("| Rol | Modulos designados | Modulos derivados de permisos | Cumple |")
    out.append("| --- | --- | --- | --- |")
    for role, perms in ROLE_PERMISSIONS.items():
        designed = ROLE_DESIGNATED_MODULES.get(role, set())
        derived = {PERMISSION_CATALOG[p] for p in perms if p in PERMISSION_CATALOG}
        unknown = sorted(p for p in perms if p not in PERMISSION_CATALOG)
        cumple = designed.issuperset(derived) and not unknown
        designed_label = ", ".join(sorted(designed)) if designed else "-"
        derived_label = ", ".join(sorted(derived)) if derived else "-"
        if unknown:
            derived_label += f" | permisos no catalogados: {', '.join(unknown)}"
        out.append(f"| `{role}` | `{designed_label}` | `{derived_label}` | `{bool_mark(cumple)}` |")

    return "\n".join(out) + "\n"


def main() -> None:
    content = build_matrix()
    OUT.write_text(content, encoding="utf-8")
    print(f"Matriz generada en: {OUT}")


if __name__ == "__main__":
    main()
