# Entry points for working on this repo.
#
#   Repo conventions and skill layout      -> AGENTS.md
#   How the three eval layers fit together -> evals/README.md

SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help validate lint test triggers clean

# The Agent Skills spec's own reference validator. Pinned to 0.1.x because
# skills-ref is pre-1.0, where a minor bump may change behaviour. Note the
# published package's executable is `agentskills`, not `skills-ref` as the spec
# page still shows.
SKILLS_REF := uvx --quiet --from 'skills-ref>=0.1.1,<0.2' agentskills

help: ## List the available targets
	@grep -hE '^[a-z][a-z-]*:.*## ' $(MAKEFILE_LIST) \
	  | awk -F':.*## ' '{printf "  \033[1m%-9s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "  test/triggers take SKILL=<name>. triggers also takes RUNS=<n>,"
	@echo "  MODEL=<id> and EFFORT=<low|medium|high>, which is where the cost is."

validate: ## Check spec conformance, the plugin manifest and marketplace registration
	@# Spec conformance, per skill, using the validator the spec itself recommends.
	@# Agent-agnostic: these skills are also read by Codex, Gemini CLI, Cursor, ...
	@if command -v uv >/dev/null 2>&1; then \
	  fail=0; \
	  for dir in skills/*/; do \
	    $(SKILLS_REF) validate "$${dir%/}" || fail=1; \
	  done; \
	  [ $$fail -eq 0 ] || exit 1; \
	else echo "  ~ uv not found - skipping spec validation"; fi
	@# The marketplace manifest is Claude-specific and outside the spec.
	@if command -v claude >/dev/null 2>&1; then claude plugin validate .; \
	else echo "  ~ claude CLI not found - skipping manifest validation"; fi
	@# Eval files must never be referenced from a SKILL.md. A reference would pull
	@# test prose into the context budget of every user who triggers the skill, and
	@# it is the one way the evals could leak into an agent's context at all.
	@if grep -rnE '(^|[^a-z-])evals?/|triggers\.json|evals\.json|contract\.sh' skills/*/SKILL.md; then \
	  echo "  x a SKILL.md references eval files - drop the reference or inline the content"; \
	  exit 1; \
	else echo "  ok  no SKILL.md references eval files"; fi
	@# Registration: neither validator above knows about marketplace.json, and an
	@# unregistered skill is installable by neither route.
	@fail=0; \
	for dir in skills/*/; do \
	  name=$$(basename "$$dir"); \
	  if ! grep -q "\"./skills/$$name\"" .claude-plugin/marketplace.json; then \
	    echo "  x $$name: not registered in .claude-plugin/marketplace.json"; fail=1; \
	  fi; \
	done; \
	if [ $$fail -eq 0 ]; then \
	  echo "  ok  every skill is registered in the marketplace"; \
	else exit 1; fi

lint: ## Lint the harness: shellcheck for shell, ruff for Python
	@# --external-sources lets shellcheck follow the dynamic `source "$$EVALS_LIB/..."`.
	@if command -v uv >/dev/null 2>&1; then \
	  uvx --quiet --from shellcheck-py shellcheck --severity=warning \
	    --external-sources --source-path=evals/lib \
	    evals/lib/assert.sh evals/skills/*/contract.sh evals/run-contract-tests.sh && \
	  uvx --quiet ruff check --select E,F,W,UP --line-length 130 \
	    evals/run-trigger-eval.py evals/skills/owid-catalog/contract_check.py && \
	  echo "  ok  shell and python lint clean"; \
	else echo "  ~ uv not found - skipping lint"; fi

test: ## Contract tests: do the OWID endpoints still match what the skills document?
	@./evals/run-contract-tests.sh $(SKILL)

triggers: ## Trigger evals: does the right skill fire? (needs the claude CLI, costs tokens)
	@# Cost scales as queries x RUNS x skills. While iterating on a description, pin
	@# SKILL and RUNS=1; use the defaults for a measurement you intend to record.
	@./evals/run-trigger-eval.py $(if $(SKILL),--skill $(SKILL),--all) \
	  $(if $(RUNS),--runs $(RUNS),) $(if $(MODEL),--model $(MODEL),) $(if $(EFFORT),--effort $(EFFORT),)

clean: ## Delete eval run outputs (evals/results/)
	@rm -rf evals/results
