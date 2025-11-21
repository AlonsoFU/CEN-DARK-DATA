#!/usr/bin/env python3
"""
Quick GPU VRAM check
"""
import sys

try:
    import torch

    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        vram_allocated = torch.cuda.memory_allocated(0) / (1024**3)
        vram_reserved = torch.cuda.memory_reserved(0) / (1024**3)
        vram_free = vram_total - vram_reserved

        print("=" * 60)
        print("🔍 GPU INFORMATION")
        print("=" * 60)
        print(f"Device: {device_name}")
        print(f"Total VRAM: {vram_total:.2f} GB")
        print(f"Allocated: {vram_allocated:.2f} GB")
        print(f"Reserved: {vram_reserved:.2f} GB")
        print(f"Free: {vram_free:.2f} GB")
        print()
        print("Recommended Mode:")
        if vram_total >= 3.0:
            print("✅ Optimized Safe mode (ACCURATE tables + SmolVLM)")
            print("   - 97.9% table accuracy")
            print("   - Picture descriptions enabled")
            print("   - ~3.0 GB VRAM required")
        else:
            print("⚠️  Lightweight mode (FAST tables)")
            print("   - 90-95% table accuracy")
            print("   - Limited features")
            print("   - ~1.5 GB VRAM required")
        print("=" * 60)

        sys.exit(0)
    else:
        print("=" * 60)
        print("⚠️  NO GPU DETECTED")
        print("=" * 60)
        print("CPU mode will be used (10x slower)")
        print("Expected processing time: ~30-40 hours for all chapters")
        print("=" * 60)
        sys.exit(1)

except ImportError:
    print("❌ torch not installed")
    print("Run: pip install torch")
    sys.exit(1)
