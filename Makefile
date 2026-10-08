SKILL_DIRS := $(shell find . -maxdepth 2 -name 'SKILL.md' -exec dirname {} \;)

.PHONY: link unlink build clean

link:
	@for dir in $(SKILL_DIRS); do \
		name=$$(basename $$dir); \
		echo "Linking $$name..."; \
		ln -sfn $$(pwd)/$$dir ~/.claude/skills/$$name 2>/dev/null || true; \
		ln -sfn $$(pwd)/$$dir ~/.codex/skills/$$name 2>/dev/null || true; \
	done
	@echo "Done. Skills linked to ~/.claude/skills/ and ~/.codex/skills/"

unlink:
	@for dir in $(SKILL_DIRS); do \
		name=$$(basename $$dir); \
		rm -f ~/.claude/skills/$$name; \
		rm -f ~/.codex/skills/$$name; \
	done
	@echo "Unlinked all skills."

build:
	@mkdir -p dist
	@for dir in $(SKILL_DIRS); do \
		name=$$(basename $$dir); \
		mkdir -p dist/$$name; \
		cp $$dir/SKILL.md dist/$$name/; \
		[ -d $$dir/references ] && cp -r $$dir/references dist/$$name/ || true; \
		[ -d $$dir/agents ] && cp -r $$dir/agents dist/$$name/ || true; \
	done
	@echo "Built to dist/"

clean:
	rm -rf dist

# ── Paper-trading bot (bots/paper-trader) ──────────────────────────────────
.PHONY: bot-test sync-fixtures
PYTHONS ?= $(shell for v in 3.8 3.9 3.10 3.11 3.12 3.13 3.14; do command -v python$$v; done; command -v python3)
SIGNALS_REPO ?= ../signals

bot-test:
	@for py in $(sort $(PYTHONS)); do \
		printf "%s: " "$$($$py --version 2>&1)"; \
		if out=$$($$py -m unittest discover -s bots/paper-trader/tests 2>&1); then \
			echo "$$out" | tail -1; \
		else \
			echo "FAILED"; echo "$$out"; exit 1; \
		fi; \
	done

sync-fixtures:
	cp $(SIGNALS_REPO)/tests/fixtures/skill-api/*.json bots/paper-trader/tests/fixtures/
