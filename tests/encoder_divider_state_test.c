/* SPDX-License-Identifier: MIT */

#include <assert.h>
#include <stdio.h>

#include <roba/encoder_divider_state.h>

#define UP 1U
#define DOWN 2U
#define TIMEOUT_MS 300U

static bool update(struct roba_encoder_divider_state *state, uint32_t direction, int64_t now_ms) {
    return roba_encoder_divider_state_update(state, direction, 2, now_ms, TIMEOUT_MS);
}

int main(void) {
    struct roba_encoder_divider_state state;

    roba_encoder_divider_state_reset(&state);
    assert(!update(&state, UP, 100));
    assert(update(&state, UP, 400));
    assert(!state.has_direction && state.count == 0);
    assert(!update(&state, UP, 500));
    assert(update(&state, UP, 501));

    roba_encoder_divider_state_reset(&state);
    assert(!update(&state, DOWN, 100));
    assert(update(&state, DOWN, 399));

    /* A timed-out input becomes the new first input instead of being discarded. */
    roba_encoder_divider_state_reset(&state);
    assert(!update(&state, UP, 100));
    assert(!update(&state, UP, 401));
    assert(update(&state, UP, 701));

    /* A reversed input becomes the first input in the new direction. */
    roba_encoder_divider_state_reset(&state);
    assert(!update(&state, UP, 100));
    assert(!update(&state, DOWN, 200));
    assert(update(&state, DOWN, 300));
    assert(!update(&state, UP, 400));
    assert(update(&state, UP, 700));

    /* Alternating directions never combine into a completed pair. */
    roba_encoder_divider_state_reset(&state);
    assert(!update(&state, UP, 100));
    assert(!update(&state, DOWN, 200));
    assert(!update(&state, UP, 300));

    roba_encoder_divider_state_reset(&state);
    for (uint32_t i = 0; i < 8; i++) {
        assert(!update(&state, i % 2 == 0 ? UP : DOWN, i * 10));
    }

    /* A non-monotonic timestamp starts a new pair defensively. */
    roba_encoder_divider_state_reset(&state);
    assert(!update(&state, UP, 200));
    assert(!update(&state, UP, 100));
    assert(update(&state, UP, 400));

    roba_encoder_divider_state_reset(&state);
    assert(!update(&state, UP, 100));
    roba_encoder_divider_state_reset(&state);
    assert(!update(&state, UP, 200));
    assert(update(&state, UP, 500));

    roba_encoder_divider_state_reset(&state);
    assert(roba_encoder_divider_state_update(&state, UP, 1, 100, TIMEOUT_MS));
    assert(roba_encoder_divider_state_update(&state, DOWN, 1, 200, TIMEOUT_MS));

    roba_encoder_divider_state_reset(&state);
    assert(!roba_encoder_divider_state_update(&state, UP, 0, 100, TIMEOUT_MS));
    assert(!state.has_direction && state.count == 0);

    puts("encoder_divider_state_test: PASS");
    return 0;
}
