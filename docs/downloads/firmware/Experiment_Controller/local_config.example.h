#pragma once
// Copy this file to local_config.h in the Experiment_Controller folder.
// Enter your display controller MAC and a private AP name/password; then remove #error.
#error "Configure your device MAC and AP credentials locally before compiling."
static uint8_t DISPLAY_MAC[6] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
static const char* AP_SSID = "YOUR_LOCAL_AP_NAME";
static const char* AP_PASS = "YOUR_PRIVATE_PASSWORD";
