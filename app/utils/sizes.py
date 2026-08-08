from __future__ import annotations


def parse_size(value: float, unit: str) -> int:
    if value <= 0:
        raise ValueError("Giới hạn dung lượng phải lớn hơn 0")
    multiplier = 1024**3 if unit.upper() == "GB" else 1024**2
    return int(value * multiplier)


def format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} TB"
