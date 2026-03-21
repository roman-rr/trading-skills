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
