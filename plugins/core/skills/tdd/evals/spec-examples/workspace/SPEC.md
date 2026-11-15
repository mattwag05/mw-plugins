# shipcode

`make_code(n)` returns a shipment code for the integer `n`.

- Format: `SC-` + `n` zero-padded to 4 digits + `-` + one check digit.
- Check digit: take the 4 padded digits left to right, multiply the 1st and 3rd by 3 and the 2nd and 4th by 1, add them up, and keep the last digit of the sum.
- `n` outside 0 to 9999, or not an integer, raises `ValueError`.

Worked examples (from the spec, trust these):

| n    | result       |
| ---- | ------------ |
| 42   | `SC-0042-4`  |
| 1234 | `SC-1234-8`  |
| 0    | `SC-0000-0`  |
