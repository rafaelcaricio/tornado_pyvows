
test:
	@env PYTHONPATH=. pyvows vows/

setup:
	@pip install -Ue.\[test\]
