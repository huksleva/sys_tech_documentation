"""Проверяет покрытие исходников, локальные ссылки и воспроизводимость поставки."""

import ast
import re
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile

import pytest

from scripts.package_tools import (
    INCLUDED_ROOT_FILES,
    create_source_archive,
    iter_source_files,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs"
REQUIRED_PAGES = (
    "README.md",
    "architecture.md",
    "game-loop.md",
    "code-reference.md",
    "testing-and-delivery.md",
    "student-guide.md",
    "api/index.md",
    "api/runtime.md",
    "api/tooling-and-tests.md",
    "api/codebase-coverage.md",
)


def _python_files():
    """Возвращает только поставляемые Python-исходники из полного контура.

    Returns:
        Отсортированный список launcher и файлов src, scripts, tests.
    """
    result = [PROJECT_ROOT / "alien_invasion.py"]
    for directory in ("src", "scripts", "tests"):
        result.extend((PROJECT_ROOT / directory).rglob("*.py"))
    return sorted(result)


def _make_delivery_tree(root):
    """Создаёт маленький снимок поставки с разрешёнными и запрещёнными файлами.

    Args:
        root: Временный корень проекта pytest.
    """
    for name in INCLUDED_ROOT_FILES:
        (root / name).write_text("fixture\n", encoding="utf-8")
    for name in (
        "site/index.html",
        "docs/api/index.md",
        "src/demo.py",
        "src/__pycache__/demo.pyc",
        "tests/.pytest_cache/state",
        ".venv/private.txt",
        "dist/stale.zip",
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")


def test_required_documentation_is_present_and_not_empty():
    """Проверяет десять непустых страниц и наличие конфигурации MkDocs."""
    assert (PROJECT_ROOT / "mkdocs.yml").is_file()
    for name in REQUIRED_PAGES:
        assert (DOCS_ROOT / name).is_file(), name
        assert len((DOCS_ROOT / name).read_text(encoding="utf-8").strip()) > 50, name


def test_docstrings_cover_every_module_class_and_named_function():
    """Проверяет docstrings даже у внутренних методов и тестовых helper-функций."""
    missing = []
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                if not ast.get_docstring(node):
                    missing.append(
                        f"{path.relative_to(PROJECT_ROOT)}:{getattr(node, 'lineno', 1)}"
                    )
    assert not missing, missing


def test_documentation_links_resolve_recursively():
    """Проверяет относительные ссылки всех Markdown-файлов включая docs/api."""
    broken = []
    for path in DOCS_ROOT.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            url = urlsplit(target.strip().split(' "', 1)[0])
            if url.scheme or url.netloc or not url.path:
                continue
            destination = (path.parent / unquote(url.path)).resolve()
            if not destination.is_file():
                broken.append(f"{path.relative_to(PROJECT_ROOT)} -> {target}")
    assert not broken, broken


def test_navigation_lists_all_markdown_pages():
    """Проверяет совпадение дерева Markdown с файловыми путями nav MkDocs."""
    config = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    navigation = config.split("nav:", 1)[1]
    listed = set(re.findall(r":\s+([\w/-]+\.md)\s*$", navigation, re.MULTILINE))
    actual = {
        path.relative_to(DOCS_ROOT).as_posix() for path in DOCS_ROOT.rglob("*.md")
    }
    assert listed == actual


def test_coverage_matrix_lists_every_python_file_exactly_once():
    """Проверяет отсутствие пропущенных или лишних исходников в матрице."""
    matrix = (DOCS_ROOT / "api/codebase-coverage.md").read_text(encoding="utf-8")
    listed = re.findall(r"^\| `([^`]+\.py)` \|", matrix, re.MULTILINE)
    expected = {path.relative_to(PROJECT_ROOT).as_posix() for path in _python_files()}
    assert set(listed) == expected
    assert len(listed) == len(expected)


def test_api_pages_include_all_runtime_and_tooling_modules():
    """Проверяет директиву для каждого модуля и включение launcher как кода."""
    runtime = (DOCS_ROOT / "api/runtime.md").read_text(encoding="utf-8")
    tooling = (DOCS_ROOT / "api/tooling-and-tests.md").read_text(encoding="utf-8")
    for path in _python_files():
        relative = path.relative_to(PROJECT_ROOT)
        if relative.as_posix() == "alien_invasion.py":
            assert '--8<-- "alien_invasion.py"' in tooling
            continue
        parts = list(relative.with_suffix("").parts)
        if parts[0] == "src":
            parts.pop(0)
        if parts[-1] == "__init__":
            parts.pop()
        module = ".".join(parts)
        page = runtime if relative.parts[0] == "src" else tooling
        assert re.search(r"^::: " + re.escape(module) + r"$", page, re.MULTILINE), (
            module
        )


def test_poe_sequences_and_docs_group_match_delivery_contract():
    """Проверяет отдельную docs-группу, безопасный check и полный build."""
    project = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    poetry = project["tool"]["poetry"]
    tasks = project["tool"]["poe"]["tasks"]
    assert poetry["group"]["docs"]["optional"] is True
    assert tasks["check"]["sequence"] == [
        "format-check",
        "docs-check",
        "compile",
        "test",
    ]
    assert tasks["build"]["sequence"] == [
        "format",
        "check",
        "docs-site",
        "archive",
        {"cmd": "poetry build"},
    ]
    assert (
        tasks["format-check"]["cmd"]
        == "ruff format --check alien_invasion.py scripts src tests"
    )
    for entry in poetry["include"]:
        if entry["path"].startswith(("docs", "site", "mkdocs")):
            assert entry["format"] == ["sdist"]


def test_archive_is_reproducible_and_uses_a_whitelist(tmp_path):
    """Проверяет одинаковые ZIP-байты, сайт в архиве и исключение кэшей.

    Args:
        tmp_path: Временный корень маленького снимка поставки.
    """
    _make_delivery_tree(tmp_path)
    first = create_source_archive(tmp_path).read_bytes()
    destination = create_source_archive(tmp_path)
    assert destination.read_bytes() == first
    with ZipFile(destination) as archive:
        names = set(archive.namelist())
        assert {
            "mkdocs.yml",
            "site/index.html",
            "docs/api/index.md",
            "src/demo.py",
        } <= names
        assert not any(name.endswith(".pyc") or "__pycache__" in name for name in names)
        assert not any(
            name.startswith(("dist/", ".venv/")) or ".pytest_cache" in name
            for name in names
        )
        assert all(
            info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()
        )
    selected = {
        path.relative_to(tmp_path).as_posix() for path in iter_source_files(tmp_path)
    }
    assert selected == names


def test_archive_requires_a_built_site(tmp_path):
    """Проверяет отказ архиватора, если отсутствует готовый site/index.html.

    Args:
        tmp_path: Временный корень проекта без готового сайта.
    """
    _make_delivery_tree(tmp_path)
    (tmp_path / "site/index.html").unlink()
    with pytest.raises(FileNotFoundError, match="index.html"):
        create_source_archive(tmp_path)
