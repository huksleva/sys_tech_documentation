"""Создаёт ZIP поставки по белому списку со стабильными метаданными."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INCLUDED_ROOT_FILES = (
    ".gitignore",
    "README.md",
    "alien_invasion.py",
    "mkdocs.yml",
    "poetry.lock",
    "poetry.toml",
    "pyproject.toml",
)
INCLUDED_DIRECTORIES = ("docs", "scripts", "site", "src", "tests")
EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    ".tools",
    ".tools-cache",
    ".poetry-cache",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
ARCHIVE_NAME = "alien-invasion-0.1.0-source.zip"
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def iter_source_files(project_root: Path):
    """Перечисляет разрешённые файлы в стабильном порядке без локальных кэшей.

    Args:
        project_root: Корень проекта, содержащий каталоги из белого списка.

    Yields:
        Абсолютные пути файлов поставки; символьные ссылки исключены.
    """
    project_root = project_root.resolve()
    candidates = [project_root / name for name in INCLUDED_ROOT_FILES]
    for directory in INCLUDED_DIRECTORIES:
        candidates.extend((project_root / directory).rglob("*"))
    for path in sorted(
        candidates, key=lambda item: item.relative_to(project_root).as_posix()
    ):
        relative = path.relative_to(project_root)
        if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
            continue
        if any(
            parent.is_symlink()
            for parent in [path, *path.parents]
            if parent != project_root
        ):
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue
        if path.is_file():
            yield path


def create_source_archive(project_root: Path = PROJECT_ROOT) -> Path:
    """Создаёт ZIP исходников с документацией и уже собранным сайтом.

    Белый список не включает ``dist`` и окружения. Порядок файлов,
    временные отметки и права фиксированы. Воспроизводимость относится
    к одному снимку исходных байтов и одной реализации сжатия.

    Args:
        project_root: Корень упаковываемого проекта; по умолчанию корень скрипта.

    Returns:
        Абсолютный путь созданного архива внутри ``dist``.

    Raises:
        FileNotFoundError: Если отсутствует обязательный корневой файл либо сайт.
        OSError: Если создание каталога, чтение или запись недоступны.
    """
    project_root = project_root.resolve()
    required = [project_root / name for name in INCLUDED_ROOT_FILES]
    required.append(project_root / "site" / "index.html")
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"Обязательный файл поставки отсутствует: {path}")
    destination = project_root / "dist" / ARCHIVE_NAME
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(
        destination, "w", compression=ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in iter_source_files(project_root):
            info = ZipInfo(path.relative_to(project_root).as_posix(), FIXED_TIMESTAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    return destination


def main():
    """Создаёт исходную поставку и печатает абсолютный путь готового ZIP."""
    print(create_source_archive())


if __name__ == "__main__":
    main()
