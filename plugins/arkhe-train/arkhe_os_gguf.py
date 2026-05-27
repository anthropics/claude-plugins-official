import struct
import numpy as np
import hashlib

class ArkheOSGGUF:
    def __init__(self, name):
        self.name = name
        self.metadata = {}
        self.tensors = {}
        self.magic = b"GGUF"
        self.version = 3

    def set_metadata(self, key, value):
        self.metadata[key] = value

    def add_tensor(self, name, shape, dtype, offset):
        self.tensors[name] = {"shape": shape, "dtype": dtype, "offset": offset}

    def to_gguf_binary(self):
        # A simple dummy binary output just for testing
        return self.magic + struct.pack("<I", self.version) + b"DUMMY_METADATA_AND_TENSORS"

    def compute_checksum(self):
        return hashlib.sha256(self.to_gguf_binary()).hexdigest()
