# Intent

Summaries from the Nimbus LLM API are cut off mid-JSON because the model spends its `max_tokens` budget on hidden reasoning. Turn reasoning off for Nimbus requests so the whole budget goes to the answer.
