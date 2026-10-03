CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2

.PHONY: test clean

test: tests/gesture_state_test tests/encoder_divider_state_test
	./tests/gesture_state_test
	./tests/encoder_divider_state_test
	python3 tests/keymap_editor_contract_test.py

tests/gesture_state_test: tests/gesture_state_test.c src/gesture_state.c include/roba/gesture_state.h
	$(CC) $(CFLAGS) -Iinclude tests/gesture_state_test.c src/gesture_state.c -o $@

tests/encoder_divider_state_test: tests/encoder_divider_state_test.c src/encoder_divider_state.c include/roba/encoder_divider_state.h
	$(CC) $(CFLAGS) -Iinclude tests/encoder_divider_state_test.c src/encoder_divider_state.c -o $@

clean:
	$(RM) tests/gesture_state_test tests/encoder_divider_state_test
