# Repository Summary - Dark Data Docling Extractors

**Created**: November 2, 2025
**Purpose**: Lightweight extraction repository for Claude Code efficiency

---

## 📦 What This Repository Contains

This is a **focused extraction repository** containing only Docling-related tools and domain processors.

### Total Size: **70 MB**
- `domains/` - 37 MB (domain processors)
- `docling_layout/` - 34 MB (Docling infrastructure + outputs)

---

## 📁 Structure

```
dark-data-docling-extractors/
│
├── docling_layout/              # 34 MB - Docling extraction tools
│   ├── eaf_patch/               # EAF monkey patch engine
│   │   ├── core/                # Patch engine, detectors, post-processors
│   │   │   ├── eaf_patch_engine.py          # Main patch engine
│   │   │   ├── eaf_title_detector.py        # Title detection
│   │   │   ├── company_name_detector.py     # Company names
│   │   │   ├── power_line_classifier.py     # Power line detection
│   │   │   └── post_processors/             # Document-level fixes
│   │   │       ├── zona_fix.py              # Zona classification fix
│   │   │       └── __init__.py
│   │   └── scripts/             # Testing and development scripts
│   │
│   ├── METHODOLOGY/             # Complete documentation (15+ files)
│   │   ├── RESUMEN_METODOLOGIA.md           # ⭐ Start here
│   │   ├── EAF_PATCH_ARCHITECTURE.md        # Monkey patch architecture
│   │   ├── UNIVERSAL_DOCLING_METHODOLOGY.md # Complete guide
│   │   ├── QUICK_START_GUIDE.md             # 1-page reference
│   │   └── ... (10+ more docs)
│   │
│   ├── EXTRACT_ANY_CHAPTER.py   # ⭐ Universal extraction script
│   ├── capitulo_XX/             # Chapter outputs (gitignored PDFs/JSONs)
│   └── README.md                # Docling documentation
│
├── domains/                     # 37 MB - Domain processors
│   ├── operaciones/
│   │   ├── anexos_eaf/          # EAF annexes processing
│   │   │   ├── chapters/        # ANEXO 1, 2, informe_diario
│   │   │   └── shared/          # Cross-chapter utilities
│   │   ├── eaf/                 # Individual EAF reports
│   │   │   ├── chapters/        # 11 chapters (capitulo_01-11)
│   │   │   └── shared/          # Cross-chapter utilities
│   │   └── shared/              # Domain-wide utilities
│   ├── mercados/                # Energy markets (planned)
│   ├── legal/                   # Legal compliance (planned)
│   └── planificacion/           # Planning (planned)
│
├── requirements.txt             # Python dependencies (clean, project-only)
├── .gitignore                   # Ignore PDFs, outputs, venv
├── README.md                    # Main documentation
└── REPOSITORY_SUMMARY.md        # This file
```

---

## 🎯 Why This Repository Was Created

### Problem: Monorepo Too Large for Claude Code
The original `Proyecto Dark Data CEN` contained:
- Extraction tools (40 MB code)
- MCP servers (2 MB code)
- Database infrastructure
- Web dashboard
- AI platform
- **Total context: 50,000+ tokens for Claude**

### Solution: Split into 2 Repositories

**This repo** (`dark-data-docling-extractors`):
- ✅ Only extraction code
- ✅ Only Docling tools
- ✅ Only domain processors
- ✅ 70 MB total (lightweight)
- ✅ ~15,000 tokens context for Claude
- ✅ 90% of development time

**Other repo** (`dark-data-platform` - not created yet):
- MCP servers
- Database infrastructure
- Web dashboard
- AI platform
- ~2 MB (infrastructure only)
- ~10,000 tokens context
- 10% of development time

---

## ✅ What You Can Do Here

### Extract Any Chapter (1-11)
```bash
cd docling_layout
python3 EXTRACT_ANY_CHAPTER.py 6   # Extract Chapter 6
python3 EXTRACT_ANY_CHAPTER.py 7   # Extract Chapter 7
```

### Process All Chapters in Batch
```bash
for i in {1..11}; do
  python3 EXTRACT_ANY_CHAPTER.py $i
done
```

### Develop New Processors
```bash
cd domains/operaciones/eaf/chapters/capitulo_XX/processors
# Create new processor for specific chapter
```

### Work with Claude Code
```bash
cd dark-data-docling-extractors
claude "help me extract chapter 8 with monkey patch"
# Claude sees only extraction context (fast, focused)
```

---

## 🚫 What You CANNOT Do Here

❌ Run MCP servers → See `dark-data-platform` repo (when created)
❌ Access database → See `dark-data-platform` repo
❌ Use web dashboard → See `dark-data-platform` repo
❌ Query with AI → See `dark-data-platform` repo

This repo is **extraction-only** by design.

---

## 📊 Key Features

### 1. EAF Monkey Patch (Automatic)
- Detects missing titles automatically
- Cross-page list detection
- Company name detection
- Power line classification
- No manual intervention required

### 2. Universal Extraction Script
- One script for ALL chapters (1-11)
- Only change: chapter number
- Automatic outputs:
  - JSON: `capitulo_XX/outputs/layout_WITH_PATCH.json`
  - PDF: `capitulo_XX/outputs/chapterXX_WITH_PATCH_annotated.pdf`

### 3. Complete Documentation
15+ methodology documents in `METHODOLOGY/`:
- Architecture guides
- Configuration references
- Quick start guides
- Troubleshooting docs

### 4. GPU Optimization
- Lightweight mode: 1.3 GB VRAM (fits 4GB GPU)
- Standard mode: 4.2 GB VRAM (requires 6GB+ GPU)
- CPU fallback: 400 MB RAM (slow but works)

---

## 🔧 Dependencies (Clean)

See `requirements.txt` for complete list. Key dependencies:

**Core:**
- `docling==2.17.0` - IBM Docling Granite-258M
- `PyMuPDF==1.25.1` - PDF text extraction
- `torch==2.5.1` - AI model inference

**Optional:**
- `anthropic==0.40.0` - Claude API (validation)
- `pandas==2.2.3` - Data processing

**Total:** ~46 packages (clean, project-only dependencies)

---

## 📈 Comparison: Before vs After

| Aspect | Monorepo (Before) | This Repo (After) |
|--------|------------------|-------------------|
| **Total size** | 230 MB | 70 MB (70% reduction) |
| **Code size** | 40 MB extraction + 2 MB platform | 70 MB extraction only |
| **Claude context** | 50,000+ tokens | ~15,000 tokens (70% reduction) |
| **Search speed** | Slow (searches all code) | Fast (searches extraction only) |
| **Focus** | Confusing (sees everything) | Clear (sees extraction only) |
| **Git operations** | Slow | Fast |
| **Claude sessions** | "What's this MCP server?" | "Extract chapter 8" ✅ |

---

## 🚀 Next Steps

### For This Repository
1. ✅ Repository created with Docling tools + domains
2. ✅ Clean requirements.txt generated
3. ✅ Git initialized
4. ⏳ Push to GitHub (when ready)
5. ⏳ Add CI/CD for automated testing

### For Platform Repository (Future)
1. ⏳ Create `dark-data-platform` repository
2. ⏳ Copy MCP servers, database, web UI
3. ⏳ Connect via JSON export/import
4. ⏳ Push to GitHub

---

## 📝 Usage Tips

### Working with Claude Code
```bash
# In this repo:
cd dark-data-docling-extractors
claude "fix title detection in Chapter 6"
# Claude sees only extraction code ✅

# In platform repo (future):
cd dark-data-platform
claude "add MCP tool to query chapter titles"
# Claude sees only platform code ✅
```

### Connecting the Two Repos
```bash
# 1. Extract in this repo
cd dark-data-docling-extractors/docling_layout
python3 EXTRACT_ANY_CHAPTER.py 6

# 2. Copy JSON to platform (manual for now)
cp capitulo_06/outputs/layout_WITH_PATCH.json \
   ../../dark-data-platform/data/universal_json/

# 3. Ingest in platform repo
cd ../../dark-data-platform
make ingest-data
```

---

## 🎯 Success Metrics

This repository is successful if:
- ✅ Claude Code sessions are fast and focused
- ✅ Extraction development is streamlined
- ✅ No confusion about "what goes where"
- ✅ Search/grep operations are instant
- ✅ Git operations are quick
- ✅ New developers understand structure immediately

---

**Repository optimized for Claude Code efficiency and extraction development** 🚀
