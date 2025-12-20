import os


class VerificationCodeGenerator:
    """Генератор кодов верификации в формате 000-000"""

    def generate(self) -> str:
        """Генерирует криптографически безопасный код верификации"""
        # Генерируем 2 байта (достаточно для двух трёхзначных чисел)
        random_bytes = os.urandom(2)

        # Преобразуем в два числа от 0 до 999
        part1 = int.from_bytes(random_bytes[0:1], byteorder='big') % 1000
        part2 = int.from_bytes(random_bytes[1:2], byteorder='big') % 1000

        return f"{part1:03d}-{part2:03d}"
