# Deterministic skill evals

Run `PYTHONDONTWRITEBYTECODE=1 python3 dev/evals/run.py --out /path/to/eval-output`.
Each skill's eval case has prompt.md, files/, graders/ and case.yaml. The YAML
records prompt, attached fixtures, deterministic checks and model grader paths.
This is a file-based skill-creator-style suite, not a claim of model execution.
The runner uses only synthetic/archived fixtures in an isolated local sandbox.
It never calls a Notion/Slack writer or a live harvest API.

Model graders explicitly require Claude. Triggering prompts are test sets, not
measured routing accuracy. No fresh-model pressure baseline, five-rep wording
comparison or Claude behavior run is claimed. The initial static safety-contract
test failed before SKILL.md existed; that is structural RED, not model RED.

Pressure prompts combine urgency, executive authority and sunk work; model
graders must check that these do not override the two legacy rules. A passing
fixture run establishes deterministic plumbing only, not autonomous reasoning.
