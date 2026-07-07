encrypt:
	python3 scripts/encrypt/encrypt_public.py

encrypt-show:
	python3 scripts/encrypt/encrypt_public.py --show

encrypt-changed:
	python3 scripts/encrypt/encrypt_public.py --skip-unchanged

.PHONY: encrypt encrypt-show encrypt-changed
