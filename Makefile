# Entry points for working on this repo.
#
#   Repo conventions and skill layout      -> AGENTS.md
#   How the three eval layers fit together -> evals/README.md

SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help validate test triggers clean

help: ## List the available targets
	@grep -hE '^[a-z][a-z-]*:.*## ' $(MAKEFILE_LIST) \
	  | awk -F':.*## ' '{printf "  \033[1m%-9s\033[0m %s\n", $$1, $$2}'
	@echo
	@echo "  Add SKILL=<name> to test or triggers to run a single skill."

validate: ## Check the plugin manifest, skill frontmatter and registration
	@if command -v claude >/dev/null 2>&1; then claude plugin validate .; \
	else echo "  ~ claude CLI not found - skipping manifest validation"; fi
	@fail=0; \
	for dir in skills/*/; do \
	  name=$$(basename "$$dir"); \
	  declared=$$(sed -n '/^name:/{s/^name:[[:space:]]*//; s/"//g; p; q;}' "$$dir/SKILL.md"); \
	  if [ "$$declared" != "$$name" ]; then \
	    echo "  x $$name: frontmatter name is '$$declared'"; fail=1; \
	  fi; \
	  if ! grep -q "\"./skills/$$name\"" .claude-plugin/marketplace.json; then \
	    echo "  x $$name: not registered in .claude-plugin/marketplace.json"; fail=1; \
	  fi; \
	done; \
	if [ $$fail -eq 0 ]; then \
	  echo "  ok  every skill's frontmatter matches its directory and is registered"; \
	else exit 1; fi

test: ## Contract tests: do the OWID endpoints still match what the skills document?
	@./evals/run-contract-tests.sh $(SKILL)

triggers: ## Trigger evals: does the right skill fire? (needs the claude CLI, costs tokens)
	@./evals/run-trigger-eval.py $(if $(SKILL),--skill $(SKILL),--all)

clean: ## Delete eval run outputs (evals/results/)
	@rm -rf evals/results
