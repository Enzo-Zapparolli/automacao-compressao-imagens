"""Gera somente imagens abstratas sintéticas; sem pessoas ou dados reais."""
import random
from pathlib import Path
from PIL import Image, ImageDraw


def gerar(pasta: Path):
    pasta.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2026)
    for nome, lado in (("textura_grande.jpg", 2200), ("textura_media.jpg", 1400), ("textura_pequena.jpg", 480)):
        destino = pasta / nome
        if destino.exists():
            raise FileExistsError(f"Não sobrescrevo {destino}")
        imagem = Image.frombytes("RGB", (lado, lado), rng.randbytes(lado * lado * 3))
        ImageDraw.Draw(imagem).rectangle((20, 20, lado-20, 140), fill="#10243a")
        ImageDraw.Draw(imagem).text((40, 60), "DEMONSTRACAO - IMAGEM SINTETICA", fill="white", font_size=24)
        imagem.save(destino, quality=99)


if __name__ == "__main__":
    gerar(Path(__file__).parent / "exemplos" / "entrada")
