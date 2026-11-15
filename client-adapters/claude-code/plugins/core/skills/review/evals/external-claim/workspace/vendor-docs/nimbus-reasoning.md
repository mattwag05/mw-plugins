# Nimbus API: reasoning parameters

`reasoning.hide` (boolean): when true, reasoning is removed from the response. The model still reasons. Hidden reasoning tokens are billed and count against `max_tokens`.

`reasoning.effort` (string): `"high"`, `"low"`, or `"off"`. `"off"` disables reasoning, so no reasoning tokens are generated.
