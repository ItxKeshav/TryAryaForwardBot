import re

def _extract_range_from_text(text):
    c = text
    # Step 1: Strip file extension
    dot = c.rfind('.')
    if dot > 0 and (len(c) - dot) <= 5: c = c[:dot]
    # Step 2: Strip trailing copy-counter suffixes
    c = re.sub(r'\s*\(\d+\)\s*$', '', c).strip()

    # 1. Comma/space sequence
    s = re.search(r'(?<!\d)(\d{1,4}(?:(?:,\s*|\s+)\d{1,4}){2,})(?!\d)', c)
    if s:
        nums = [int(x) for x in re.findall(r'\d+', s.group(1))]
        if max(nums) < 5000: return (min(nums), max(nums), True)

    # 2. Explicit range
    r = re.search(r'(?<!\d)(\d{1,4}(?:(?:\s*[-\u2013\u2014]|(?i:\s+to\s+))\s*\d{1,4})+)(?!\d)', c)
    if r:
        nums = [int(x) for x in re.findall(r'\d+', r.group(1))]
        if max(nums) < 5000 and len(nums) >= 2 and nums == sorted(nums) and len(set(nums)) == len(nums):
            if (nums[-1] - nums[0]) < 1000:
                return (min(nums), max(nums), True)

    # 3. Zero-padded prefix
    m = re.match(r'^0*(\d{1,4})(?:[^0-9]|$)', c)
    if m:
        n = int(m.group(1))
        if 0 < n < 5000: return (n, n, False)

    # 4. Explicit keywords
    kw = re.search(r'(?i)(?:ep|episode|e|ch|chapter|part)[\\s\\-\\:\\.\\#]*(\d{1,4})(?!\d)', c)
    if kw:
        n = int(kw.group(1))
        if 0 < n < 5000: return (n, n, False)

    # 5. Last number fallback
    c2 = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', c)
    c2 = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', c2)
    c2 = re.sub(r'(?i)\b19\d{2}\b|\b20\d{2}\b', ' ', c2)
    nums = [int(x) for x in re.findall(r'(?<!\d)(\d{1,4})(?!\d)', c2) if 0 < int(x) < 5000]
    if nums:
        return (nums[-1], nums[-1], False)

    return None

test_cases = [
    ("Shadow 86 (1).mp3", 86),
    ("Shadow 87 (1).mp3", 87),
    ("Shadow 100 (1).mp3", 100),
    ("Shadow 290 (1).mp3", 290),
    ("Mr. Shadow 388-389.mp3", (388, 389)),
    ("Mr. Shadow 390-391.mp3", (390, 391)),
    ("Mr. Shadow 467.mp3", 467),
    ("Mr. Shadow 600.mp3", 600),
    ("Mr. Shadow 613.mp3", 613),
    ("Shadow 1.mp3", 1),
    ("Shadow 784.mp3", 784),
    ("Shadow 44 (1).mp3", 44),
    ("Shadow 35 (2).mp3", 35),
]

print("=== TESTING FIXED EXTRACTOR ===\n")
all_pass = True
for fname, expected in test_cases:
    result = _extract_range_from_text(fname)
    if isinstance(expected, tuple):
        got = (result[0], result[1]) if result else None
        ok = got == expected
    else:
        got = result[0] if result else None
        ok = got == expected
    status = "✅ PASS" if ok else "❌ FAIL"
    if not ok: all_pass = False
    print(f"  {status}  '{fname}' -> got={result}, expected={expected}")

print()
if all_pass:
    print("ALL TESTS PASSED ✅")
else:
    print("SOME TESTS FAILED ❌")
