index:
	python scripts/index.py --repo $(REPO)

analyze:
	python scripts/analyze.py symbol --name $(NAME) --change "$(CHANGE)" --repo $(REPO)

eval:
	python eval/run_eval.py

test:
	pytest -m "not integration"

test-all:
	pytest

clean:
	rm -rf .dep_impact/
