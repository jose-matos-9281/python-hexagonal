from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_SURFACE = REPO_ROOT / "src/hexagonal/integrations/sqlalchemy.py"


def test_public_sqlalchemy_namespace_reexports_legacy_surface() -> None:
    module = ast.parse(PUBLIC_SURFACE.read_text(encoding="utf-8"))
    imported_names: set[str] = set()

    for node in module.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module not in {
            "hexagonal.adapters.drivens.repository.sqlalchemy",
            "hexagonal.adapters.drivens.repository.sqlalchemy.env_vars",
        }:
            continue
        imported_names.update(alias.name for alias in node.names)

    assert "SQLAlchemyUnitOfWork" in imported_names
    assert "SQLAlchemyRepositoryAdapter" in imported_names
    assert "SQLALCHEMY_DATABASE_URL" in imported_names


def test_public_sqlalchemy_namespace_declares_supported_exports() -> None:
    module = ast.parse(PUBLIC_SURFACE.read_text(encoding="utf-8"))
    exported_names: set[str] = set()

    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        if node.targets[0].id != "__all__" or not isinstance(node.value, ast.List):
            continue
        for item in node.value.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                exported_names.add(item.value)

    assert "SQLAlchemyUnitOfWork" in exported_names
    assert "SQLAlchemyRepositoryAdapter" in exported_names
    assert "SQLALCHEMY_DATABASE_URL" in exported_names
