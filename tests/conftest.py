"""Test configuration.

Force the deterministic path (DISABLE_LLM=true) so the suite is fully reproducible
and never depends on network / Groq availability. The LLM path is exercised
separately and manually; correctness must hold without it.
"""
import os

os.environ["DISABLE_LLM"] = "true"
