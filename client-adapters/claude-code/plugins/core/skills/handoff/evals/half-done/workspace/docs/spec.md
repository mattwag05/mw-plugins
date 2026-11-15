# Spec: slugify
Goal: `slugify.py` exposes `slugify(text)` returning a lowercase, hyphen-separated slug.
Done-check: `python3 test_slugify.py` exits 0.
Cases: spaces become hyphens; punctuation dropped; repeated hyphens collapse.
