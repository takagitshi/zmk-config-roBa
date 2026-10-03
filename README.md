# roBa firmware configuration

This fork keeps roBa's original hardware path and adds the current moNa2-style
keymap and upper-level pointing features.

## Preserved roBa hardware behavior

- Right-central PMW3610 SPI wiring, orientation, smart algorithm and 125 Hz
  software polling remain on the original roBa driver lineage.
- The encoder stays at roBa's hardware-specific 12 steps. Its push switch is
  retained as the extra 43rd input at position 15; its current key binding is
  `&none` after the latest Keymap Editor edit.
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
- The PMW3610 uses a 500-CPI-equivalent low-speed baseline and accelerates from
  there through a faster mid-speed ramp toward a 3.0x high-speed upper
  bound. Scroll and Gesture layers bypass it.
- Scroll uses roBa's established axis directions with smooth, remainder-aware
  1/40 scaling. This compensates for roBa's 800 CPI so physical scroll speed
  stays close to moNa2's 1200 CPI at 1/60.
- The left encoder retains the moNa2-style layer roles and roBa's physical
  step count. Base and Mouse use LisM's two-input, 300 ms volume divider, with
  clockwise/up set to Volume Down and counter-clockwise/down to Volume Up.
  Rotation parameters remain editable in Keymap Editor; Scroll layers are not
  divided.
- The XIAO onboard RGB widget and adapter are not enabled, restoring the
  original roBa LED configuration because the assembled case hides the LED.

## Keymap Editor contract

`config/roBa.keymap` is the editable canonical keymap. Automated checks protect
the ten-layer structure, 43 input slots, safe momentary layer access and AML
exclusions. Layer display names, encoder directions, Gesture actions, tap
actions and mouse-button values remain editable. Mouse-layer key positions
also control AML's `excluded-positions`; CI checks that they stay in sync so
AML does not turn off before a Mouse-layer action runs.

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
