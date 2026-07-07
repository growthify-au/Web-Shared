# Publish a report in one step: copy in, encrypt, print URL + password.
#   make publish FILE="/path/to/report.html"
publish:
	@bash scripts/encrypt/publish.sh

encrypt:
	python3 scripts/encrypt/encrypt_public.py

encrypt-show:
	python3 scripts/encrypt/encrypt_public.py --show

encrypt-changed:
	python3 scripts/encrypt/encrypt_public.py --skip-unchanged

.PHONY: publish encrypt encrypt-show encrypt-changed
