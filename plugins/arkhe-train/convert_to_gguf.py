#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  CONVERT TO GGUF — Script de conversão para llama.cpp          ║
# ║  Substrato 889.4 • ARKHE Cathedral                              ║
# ╚══════════════════════════════════════════════════════════════════╝

"""
Converte um checkpoint PyTorch treinado (Substrato 244.1) para GGUF v3.

Uso:
  python convert_to_gguf.py --input checkpoint.pt --output arkhe-os.gguf
"""

import argparse
import torch
import numpy as np
from pathlib import Path

def convert_checkpoint_to_gguf(input_path: str, output_path: str, quantization: str = "Q4_K_M"):
    """Converte checkpoint PyTorch para GGUF v3."""

    print(f"Loading checkpoint from {input_path}...")
    checkpoint = torch.load(input_path, map_location="cpu")

    # Extrair state_dict
    state_dict = checkpoint.get("model", checkpoint)

    print(f"Found {len(state_dict)} tensors")

    # Importar e usar a classe ArkheOSGGUF
    from arkhe_os_gguf import ArkheOSGGUF

    gguf = ArkheOSGGUF("arkhe-os")

    # Configurar metadados do treinamento
    gguf.set_metadata("general.name", "ARKHE-OS")
    gguf.set_metadata("general.architecture", "transformer")
    gguf.set_metadata("general.quantization_version", 3)
    gguf.set_metadata("general.file_type", 15)  # Q4_K_M

    # Adicionar tensores
    offset = 0
    for name, tensor in state_dict.items():
        shape = list(tensor.shape)
        dtype = str(tensor.dtype).replace("torch.", "").upper()

        # Mapear dtype PyTorch para GGUF
        dtype_map = {
            "FLOAT32": "F32",
            "FLOAT16": "F16",
            "INT8": "Q8_0",
        }
        gguf_dtype = dtype_map.get(dtype, "F32")

        gguf.add_tensor(name, shape, gguf_dtype, offset)

        # Calcular offset (simplificado)
        num_elements = np.prod(shape)
        element_size = 4 if dtype == "FLOAT32" else 2
        offset += num_elements * element_size

    # Gerar arquivo GGUF
    print(f"Writing GGUF to {output_path}...")
    gguf_data = gguf.to_gguf_binary()

    with open(output_path, "wb") as f:
        f.write(gguf_data)

    print(f"Done! File size: {len(gguf_data) / 1024 / 1024:.1f} MB")
    print(f"Checksum: {gguf.compute_checksum()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PyTorch checkpoint to GGUF")
    parser.add_argument("--input", required=True, help="Path to PyTorch checkpoint")
    parser.add_argument("--output", default="arkhe-os.gguf", help="Output GGUF file")
    parser.add_argument("--quantization", default="Q4_K_M", choices=["Q4_0", "Q4_K_M", "Q5_K_M", "Q8_0"])

    args = parser.parse_args()
    convert_checkpoint_to_gguf(args.input, args.output, args.quantization)
