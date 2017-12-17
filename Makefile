

deps:
	sudo pip install sqlalchemy

clean:
	rm -rf *.pyc
	rm -rf Fit/*.pyc
	rm -rf GarminSqlite/*.pyc

TEST_DB=garmin.db
test_clean:
	rm -f $(TEST_DB)

test_file:
	python import.py --input_file "$(TEST_DIR)/$(TEST_FILE)" --database $(TEST_DB)

test_dir:
	python import.py --input_dir "$(TEST_DIR)" --database $(TEST_DB)
