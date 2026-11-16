"""Compressão JPEG em lote, preservando os arquivos de entrada."""
from __future__ import annotations

import argparse
import csv
from io import BytesIO
from pathlib import Path
import time
from PIL import Image


def comprimir(origem: Path, destino: Path, limite_kb: int = 2091) -> list[dict]:
    origem, destino = origem.resolve(), destino.resolve()
    if not origem.is_dir():
        raise ValueError("A pasta de entrada não existe.")
    if origem == destino:
        raise ValueError("Entrada e saída precisam ser pastas diferentes.")
    if limite_kb <= 0:
        raise ValueError("O limite deve ser positivo.")
    destino.mkdir(parents=True, exist_ok=True)
    if (destino / "relatorio.csv").exists():
        raise FileExistsError("Já existe relatorio.csv na saída; escolha outra pasta.")
    resultados = []
    for arquivo in sorted(origem.iterdir()):
        if not arquivo.is_file() or arquivo.suffix.lower() not in (".jpg", ".jpeg"):
            continue
        saida = destino / arquivo.name
        inicio = time.perf_counter()
        linha = dict(arquivo=arquivo.name, bytes_antes=arquivo.stat().st_size,
                     bytes_depois="", qualidade="", status="", segundos="", detalhe="")
        try:
            if saida.exists():
                raise FileExistsError("Arquivo de saída já existe; escolha outra pasta.")
            conteudo = arquivo.read_bytes()
            # Valida inclusive os arquivos pequenos antes de copiá-los.
            with Image.open(BytesIO(conteudo)) as imagem:
                imagem.load()
                if len(conteudo) <= limite_kb * 1024:
                    payload, qualidade = conteudo, "original"
                else:
                    imagem = imagem.convert("RGB")
                    payload, qualidade = None, None
                    for q in range(95, 39, -5):
                        buffer = BytesIO()
                        # Mantém dimensões; não copia EXIF na recompressão.
                        imagem.save(buffer, format="JPEG", quality=q, optimize=True)
                        if buffer.tell() <= limite_kb * 1024:
                            payload, qualidade = buffer.getvalue(), q
                            break
            if payload is None:
                linha["status"] = "limite_nao_atingido"
                linha["detalhe"] = "Não salvo: exigiria qualidade abaixo de 40 ou redimensionamento."
            else:
                with saida.open("xb") as stream:
                    stream.write(payload)
                linha.update(bytes_depois=len(payload), qualidade=qualidade,
                             status="copiado" if qualidade == "original" else "comprimido")
        except Exception as erro:
            linha.update(status="erro", detalhe=str(erro))
        linha["segundos"] = round(time.perf_counter() - inicio, 4)
        resultados.append(linha)
        print(f"{linha['status']}: {arquivo.name}")
    relatorio = destino / "relatorio.csv"
    if relatorio.exists():
        raise FileExistsError("Já existe relatorio.csv na saída; escolha outra pasta.")
    campos = ["arquivo", "bytes_antes", "bytes_depois", "qualidade", "status", "segundos", "detalhe"]
    with relatorio.open("x", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=campos, delimiter=";")
        writer.writeheader()
        writer.writerows(resultados)
    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path)
    parser.add_argument("saida", type=Path)
    parser.add_argument("--limite-kb", type=int, default=2091)
    args = parser.parse_args()
    registros = comprimir(args.entrada, args.saida, args.limite_kb)
    print(f"Processados: {len(registros)}. Relatório salvo na pasta de saída.")
    raise SystemExit(1 if any(r["status"] in ("erro", "limite_nao_atingido") for r in registros) else 0)
