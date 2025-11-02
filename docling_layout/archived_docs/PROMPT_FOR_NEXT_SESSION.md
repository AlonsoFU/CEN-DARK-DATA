# What to Say to Claude Next Time

Copy and paste this message to Claude in your next session:

---

## 📋 Quick Resume Prompt

```
I want to continue with the Docling extraction work.

Please read: shared_platform/utils/outputs/docling_layout/README_DOCLING.md

Then help me run the lightweight extraction for Chapter 1 that we prepared last session.
```

---

## 📋 Detailed Resume Prompt (If You Want More Context)

```
Hi Claude! I'm continuing our Docling work from the previous session.

Context:
- We set up Docling for layout extraction from PDF documents
- Created a lightweight configuration optimized for my 4GB GPU (GTX 1650)
- GPU crashed during testing and needs to be restored
- All scripts and documentation are ready to use

Please:
1. Read the README at: shared_platform/utils/outputs/docling_layout/README_DOCLING.md
2. Check the "START HERE NEXT TIME" section at the top
3. Help me verify the GPU is working after reboot
4. Run the lightweight extraction script for Chapter 1

The script is ready at:
shared_platform/utils/outputs/docling_layout/capitulo_01/scripts/lightweight_extract.py
```

---

## 📋 If You Haven't Rebooted Yet

```
I haven't rebooted yet from our last Docling session.

Can you remind me:
1. Why the GPU needs a reboot
2. What commands to run after rebooting
3. What to expect from the extraction

Please read: shared_platform/utils/outputs/docling_layout/README_DOCLING.md
```

---

## 📋 If GPU Still Not Working After Reboot

```
I rebooted but the GPU still isn't working for Docling.

Can you help me troubleshoot?

Please check:
1. shared_platform/utils/outputs/docling_layout/RESTORE_GPU.md
2. shared_platform/utils/outputs/docling_layout/WHY_REBOOT_NEEDED.md

Current status:
- nvidia-smi shows: [paste output here]
- torch.cuda.is_available() returns: [paste True/False]
```

---

## 📋 If You Want to Understand the Options Better

```
I want to understand the Docling configuration options better before running the extraction.

Please explain the options we're using in lightweight_extract.py and why.

Reference files:
- shared_platform/utils/outputs/docling_layout/DOCLING_OPTIONS_CHEATSHEET.md
- shared_platform/utils/outputs/docling_layout/LIGHTWEIGHT_MODES.md
```

---

## 📋 If Extraction Completed and You Want to Review Results

```
The Docling extraction completed!

Can you help me review the results?

Output files are in:
shared_platform/utils/outputs/docling_layout/capitulo_01/outputs/

Please:
1. Check what was extracted
2. Show me statistics
3. Compare with my existing PyMuPDF extractions if needed
```

---

## 🎯 Recommended: Simple Start

**Just use this** (shortest and clearest):

```
Continue Docling work. Read: shared_platform/utils/outputs/docling_layout/README_DOCLING.md
```

Claude will:
1. Read the README
2. See the "START HERE NEXT TIME" section
3. See the session summary
4. Know exactly what to do
5. Help you run the extraction

---

## 📁 Key Files Claude Should Read

Claude Code can read these automatically when you mention them:

1. **`README_DOCLING.md`** - Master index with "START HERE" section
2. **`START_HERE.md`** - Quick commands
3. **`DOCLING_OPTIONS_CHEATSHEET.md`** - Options reference
4. **`WHY_REBOOT_NEEDED.md`** - GPU crash explanation
5. **`EXTRACTION_STATUS.md`** - Current status

---

## 💡 Pro Tips

### If You Want Quick Help:
```
Read README_DOCLING.md and help me run the extraction
```

### If You Want Detailed Explanation:
```
Read README_DOCLING.md and DOCLING_OPTIONS_CHEATSHEET.md,
then explain what we're doing and help me run it
```

### If Something Went Wrong:
```
Read README_DOCLING.md and EXTRACTION_STATUS.md,
then help me troubleshoot [describe issue]
```

---

## ✅ Example Full Conversation Start

**You:**
```
Continue Docling extraction work.
Read: shared_platform/utils/outputs/docling_layout/README_DOCLING.md
I just rebooted.
```

**Claude will:**
1. Read the README
2. See you need to verify GPU
3. Ask you to run `nvidia-smi`
4. Verify CUDA is available
5. Run the extraction script
6. Monitor progress

---

## 🚀 Shortest Possible Prompt

```
Docling. Read README_DOCLING.md
```

That's it! Claude will figure out the rest from the README.

---

**Save this file** for easy reference next session! 📌
