# Why Is It Called "Monkey Patch"? 🐵

## Origin of the Name

The term "monkey patch" comes from **"guerrilla patch"** → **"gorilla patch"** → **"monkey patch"**

### Etymology Evolution:

1. **Guerrilla Patch** (original concept)
   - Like guerrilla warfare: quick, unofficial, improvised
   - You're making changes "in the field" without official support
   - Fast, tactical modifications to get the job done

2. **Gorilla Patch** (mishearing/wordplay)
   - "Guerrilla" sounds like "gorilla" (the animal)
   - People started using "gorilla patch" as a pun
   - Idea: A gorilla is strong and can force changes

3. **Monkey Patch** (final evolution)
   - Softened from "gorilla" to "monkey"
   - Monkeys are known for:
     - **Mischievous behavior** - doing things they shouldn't
     - **Tampering with things** - opening boxes, pulling levers
     - **Clever improvisation** - finding creative solutions
   - Perfect metaphor for dynamically modifying code at runtime!

### First Known Use:
- Appeared in Python community around **2001**
- Popularized by Ruby community around **2005**
- Now used across all dynamic programming languages

---

## What Does "Monkey Patching" Mean?

**Monkey patching** = Modifying or extending code **at runtime** without changing the original source files

### Key Characteristics:

1. **Dynamic** - Happens while program is running
2. **Non-invasive** - Doesn't modify original files
3. **Temporary** - Only affects current program instance
4. **Risky** - Like a monkey tampering with machinery!

---

## Why "Monkey" Is the Perfect Metaphor

Think of a monkey in a factory:

```
Original Code (Factory Machine):
┌─────────────────────────┐
│  Docling's              │
│  LayoutPostprocessor    │
│  ┌─────────────────┐   │
│  │ _process_reg... │   │  ← This method does layout analysis
│  └─────────────────┘   │
└─────────────────────────┘

Monkey Patch (Monkey tampering):
         🐵
        /│\   "I'm going to swap this part!"
         │
         ↓
┌─────────────────────────┐
│  Docling's              │
│  LayoutPostprocessor    │
│  ┌─────────────────┐   │
│  │ YOUR_custom_... │   │  ← Monkey swapped the method!
│  └─────────────────┘   │
└─────────────────────────┘
```

The monkey:
- ✅ Didn't rebuild the factory (no fork)
- ✅ Didn't ask permission (no official API)
- ✅ Just swapped one part while machine is running
- ⚠️ Might break things if done wrong!

---

## Other Names You Might Hear

| Term | Meaning | Usage |
|------|---------|-------|
| **Monkey Patch** | Most common term | Python, Ruby, JavaScript |
| **Duck Punching** | Aggressive version | "If it walks like a duck, punch it!" |
| **Hot Patching** | System-level term | Operating systems, game modding |
| **Runtime Patching** | Formal term | Academic papers |
| **Method Swizzling** | Objective-C term | iOS/macOS development |

---

## Example: The Monkey in Action

### What Docling Expects:
```python
class LayoutPostprocessor:
    def _process_regular_clusters(self):
        # Docling's original method
        return ai_clusters
```

### What the Monkey Does:
```python
# Store original (like monkey remembering the old part)
_original = LayoutPostprocessor._process_regular_clusters

# Create replacement (monkey builds a new part)
def _custom_method(self):
    print("🐵 Monkey was here!")
    custom_clusters = my_custom_detector()
    return _original(self) + custom_clusters

# Swap it! (monkey replaces the part)
LayoutPostprocessor._process_regular_clusters = _custom_method
```

When Docling runs:
```python
processor = LayoutPostprocessor(...)
result = processor._process_regular_clusters()  # ← Calls YOUR method now!
```

**Docling has NO IDEA** it's running your code instead of its own! 🐵

---

## Why This Works in Python

Python is **dynamically typed** and uses **late binding**:

```python
# When you write this:
obj.method()

# Python does this at RUNTIME:
1. Look up "method" in obj.__dict__
2. If not found, look in obj.__class__.__dict__  ← This is where we patch!
3. If not found, look in parent classes
4. Call whatever you found

# So we can change what's in __class__.__dict__ ANYTIME!
```

**This is why it's called monkey patching** - you're reaching into Python's internal dictionaries and swapping things around, just like a monkey tampering with machinery!

---

## When Monkey Patching Is Used

### ✅ Good Uses:
1. **Testing** - Mock external APIs
2. **Hotfixes** - Fix bugs in libraries you can't modify
3. **Feature injection** - Add features to closed-source libraries
4. **Debugging** - Add logging to third-party code
5. **Compatibility** - Make old libraries work with new code

### ❌ Bad Uses:
1. **Replacing core functionality** - Too risky
2. **Production shortcuts** - Use proper solutions
3. **Avoiding proper APIs** - If API exists, use it
4. **Making libraries do things they shouldn't** - Architectural smell

---

## Our Use Case: Injecting Custom Detectors into Docling

We're using monkey patching because:

1. ✅ **Docling has no official API** for custom detectors
2. ✅ **We need to modify mid-pipeline** (can't do it externally)
3. ✅ **We want to keep Docling's updates** (don't want to fork)
4. ✅ **It's cleaner than maintaining a fork**

**This is a perfect legitimate use case** for monkey patching! 🎯

---

## The Monkey Patch Philosophy

```
          🐵 "If I can reach it, I can change it!"

Traditional Approach:
- Fork the code
- Modify the source
- Maintain forever
- Cry when updates come

Monkey Patch Approach:
- Find the method you need
- Swap it at runtime
- Keep using official library
- Update anytime! 🎉
```

---

## Fun Fact: Duck Punching

Some developers don't like the cute "monkey" term and prefer **"duck punching"**:

> "If it walks like a duck and talks like a duck, but you want it to quack differently, you PUNCH it!" 🦆👊

Same concept, more aggressive name! 😄

---

## Summary

**Why "Monkey Patch"?**
- Comes from "guerrilla" → "gorilla" → "monkey"
- Monkeys are mischievous and tamper with things
- Perfect metaphor for runtime code modification

**What it means:**
- Dynamically swapping methods at runtime
- Without modifying original source files
- Like a monkey swapping parts in a running machine

**Why we use it:**
- Inject custom detectors into Docling's pipeline
- No official API for this
- Don't want to maintain a fork
- Want to keep getting Docling updates

---

**Remember:** You're not doing anything wrong - you're just being a clever monkey! 🐵✨
