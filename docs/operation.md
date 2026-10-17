---
title: Operating procedure
description: Controller setup, trial execution and shutdown.
section: Operation
---
This procedure follows the included master and LED programs. The background and thermal ring operate on separate temperature controllers.

## Before a run

1. Load the appropriate program onto each controller. Configure the master's display address and network settings using the [configuration example](downloads/firmware/Master_Controller/local_config.example.h).
2. Check target labels A–D against the [wiring table](build/four-channels.md#target-controller-pin-map). Confirm the display orientation and panel connections.
3. Check the background and ring sensor readings, then allow the temperatures to settle. Verify target surface temperatures separately.
4. Start video and temperature recording. Record the target order and the time at which the sequence is started.

## Start a sequence

Open the master serial connection at **115200 baud** and enter a sequence, for example:

```text
EXP A-D-C-D
```

The program accepts **1–16 target selections**. It preheats all four targets for five minutes, then runs each cooling step for five minutes. The example above lasts 25 minutes including preheat.

At each step, the selected target cools and the display receives the corresponding letter. The other three targets heat. See [target control](build/four-channels.md#trial-sequence) for the PWM stages.

## Stop and shut down

Enter `STOP` on the master to stop the four targets and blank the display. The program also does this when the sequence finishes.

The background and ring remain active. Stop the background through its own serial connection and switch off the ring heater supply separately. The ring program has no `STOP` command. Allow the heat sinks to cool before switching off the fan.

[Controller programs](firmware/index.md) · [Thermal-camera output](firmware/camera.md)
