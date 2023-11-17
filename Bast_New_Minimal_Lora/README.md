# Bast_New_Minimal_Lora

This is a modified version of [RAK811_Minimal_Lora](https://github.com/Kongduino/RAK811_Minimal_Lora), for the [BastWAN](https://electroniccats.com/store/bastwan/), designed by Electronic Cats and produced by [RAKwireless](https://docs.rakwireless.com/Product-Categories/WisDuo/BastWAN/Quickstart/). In a way it's ironical, since the whole `Minimal_Lora` series started with the BastWAN...

## SETUP
For LoRa, I use Sandeep Mistry's library, which I know well and have patched to make it work slightly better. For this example to work, you don't need to use my version, but you do need to effect a small patch:

Lines 109-110 in the original source code of the header file must be moved **before** `private` on line 97:

```c
[...]
  void dumpRegisters(Stream& out);

  uint8_t readRegister(uint8_t address);
  void writeRegister(uint8_t address, uint8_t value);

private:
  void explicitHeaderMode();
[...]
```

These 2 functions are required to play a little bit of magic on registers, and verify settings are actually set properly.

```c
template class basic_string<char>; // https://github.com/esp8266/Arduino/issues/1136
// Required or the code won't compile!

namespace std _GLIBCXX_VISIBILITY(default) {
_GLIBCXX_BEGIN_NAMESPACE_VERSION
void __throw_length_error(char const*) {}
void __throw_bad_alloc() {}
void __throw_out_of_range(char const*) {}
void __throw_logic_error(char const*) {}
void __throw_out_of_range_fmt(char const*, ...) {}
}
```
This bit of code is required for the code to compile: the BastWAN framework is missing some things, and this is a stopgap.

## Minimal LoRa Commands

This version of Minimal LoRa comes with a subset of the commands available in other versions. It does come with my new commands engine, which is way easier to use and extend.

```
Available commands: 11
 . help: Shows this help.
 . lora: Gets the current LoRa settings.
 . fq: Gets/sets the working frequency.
 . bw: Gets/sets the working bandwidth.
 . sf: Gets/sets the spreading factor.
 . cr: Gets/sets the working coding rate.
 . tx: Gets/sets the Transmission Power.
 . ap: Gets/sets the auto-ping rate.
 . aes: Gets/sets the AES mode.
 . pwd: Gets/sets the AES password.
 . p: Sends a ping packet.
```

Commands start with a `/`, so `/fq 469.125`, `/bw 6`, etc. Anything else is considered as a message to be sent.

On the subject of BW, the bandwidth, and SF, the spreading factor. Contrary to LoRaWAN, which uses only a subset of LoRa's BW range, and only in a limited number of SF/BW combinations, in LoRa you can do (at least technically, what the law in your country might be... different) pretty much what you want, and use the whole range of BW settings:

```c
float myBWs[10] = {7.8, 10.4, 15.63, 20.83, 31.25, 41.67, 62.5, 125, 250, 500};
```

You can select independently any of the 10 BW values, `/bw 0` to `/bw 9`, and SF 6 to 12, knowing that `SF 6` is for special uses.

Since this is a modified version specifically for the [UniBaster](https://twitter.com/TheGrouchHK/status/1724690350978355290), feedback is provided on both SerialUSB and Serial1, albeit with a few differences: `SerialUSB` is for the Unihiker, so there's only "useful" information sent, whereas `Serial1`, which is for debug purposes, gets a lot more.

Note the calculation of the frequency from the SX1276's registers is a bit imprecise (floats and all that), so in that particular case I allow a variation of 1 Hz.

### AUTO PING

You can have the device send a PING automatically every x seconds (at least 10, but do try to space the PINGs out a little more than that). This is quite useful for testing: you set up one a static device to ping every minute, for example, and take another one (connected to a computer or else to get the information) and see whether the pings are coming in.

```
Evaluating: `/ap 30`
AutoPING set to: ON, every 30 secs.
Evaluating: `/lora`
Current settings:
 - Frequency: 470.00 MHz
 - BW: 7, ie 125.00KHz
 - SF: 12
 - CR 4/5
 - Tx power: 20
 - AutoPING: ON, every 30 secs.
Sending `This is a not so short PING!` done!
Time: 1648 ms.
```
### LoRa settings

The `lora` command shows all settings at once, as illustrated above.

### TODO

I will add a couple of commands, which are slightly less useful on this specific project (but could be used via the debug console, since the firmware accepts commands from `Serial1` too):

* `/s text`: send an ASCII text string
* `/h decafbad`: send an hex string (when sending encrypted text or non-text payload for example)
* `/b64 text`: send a base64-encoded (when sending encrypted text or non-text payload for example)

Abstraction of `SerialUSB` and `Serial1`. I will change all references to the two UARTs to something generic, like `MACHINE_PORT` and `DEBUG_PORT`, so that one could easily invert the ports when using it with another setup.

## AES

I tested, separately, that AES worked on the BastWAN – no reason it shouldn't, but... – and will add commands to set up a key, Iv (NEVER reuse an Iv, or use a predictable Iv!), and switch AES on/off. HMAC could also be added at some point.

AES has been added to the code, with `/pwd` to set up the key (16 bytes ASCII, or, preferred, 32 bytes hex-encoded binary). `/aes on` and `/aes off` turn the encryption on and off. The Iv is produced by the code every time, and sent with the ciphertext.

I am using the empty `/pwd` command to set up the key for you, which it shows once in the Serial Monitor. You can set up the same key manually in other devices.

That's it for now, but it is already quite usable for range tests. Happy LoRaWalks!

![demo](assets/demo.gif)