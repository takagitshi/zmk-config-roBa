# roBa firmware configuration

This fork keeps roBa's original hardware path and adds the current moNa2-style
keymap and upper-level pointing features.

## Preserved roBa hardware behavior

- Right-central PMW3610 SPI wiring, orientation, smart algorithm and 125 Hz
  software polling remain on the original roBa driver lineage.
- The encoder stays at roBa's hardware-specific 12 steps. Its push switch is
  retained as the extra 43rd input at position 15.
- The original sensor power behavior remains in use; `force-awake` is not
  enabled.
- Standard ZMK Studio, split battery reporting and Bluetooth roles are kept.

## Custom behavior

- Ten layers matching moNa2: Base, Mouse, Scroll, Gesture 1, Gesture 2,
  symbol, number, move, setting and User 9.
- Automatic Mouse Layer uses 300 ms prior-idle filtering, a 10-second timeout,
  and mouse-button activity refresh.
- Gesture actions are ordinary bindings on Layers 3 and 4, so GitHub Keymap
  Editor can change them without editing the gesture implementation.
- The PMW3610 keeps an effective low-speed sensitivity of 400 CPI while using
  a roBa-adapted acceleration curve. Scroll and Gesture layers bypass it.
- Scroll uses roBa's established axis directions with smooth, remainder-aware
  1/40 scaling. This compensates for roBa's 800 CPI so physical scroll speed
  stays close to moNa2's 1200 CPI at 1/60.
- The left encoder matches moNa2's layer roles while retaining roBa's physical
  step count.
- The onboard RGB LED in each XIAO nRF52840 is enabled. Central-side layer
  colors match moNa2: off, white, green, yellow, magenta, blue, green, cyan,
  red and yellow for Layers 0 through 9.

The XIAO LED can be partially obscured by the assembled roBa case, so actual
visibility must be checked on the finished keyboard.

## Keymap Editor contract

`config/roBa.keymap` is the editable canonical keymap. Automated checks protect
the ten-layer structure, 43 input slots, safe momentary layer access, dynamic
AML exclusions and editable Gesture slots without pinning Editor-owned tap
actions or mouse-button values.

## Firmware artifacts

- `roba-left-peripheral.uf2`
- `roba-right-central.uf2`
- `roba-pairing-reset-use-only-when-needed.uf2`

For the initial installation of this customization, flash the named left and
right normal images to their corresponding halves. Do not use the pairing-reset
image for a normal update; it erases saved Bluetooth bonds and is only for
recovery.

Source checks run with `make test`. CI also builds both normal halves, verifies
their generated Devicetree/Kconfig contracts and then produces the three named
artifacts.
