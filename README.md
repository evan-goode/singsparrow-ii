# SingSparrow II

SingSparrow II is software for operant conditioning used in the [Maney Lab](https://www.birdbrainlab.org/). This project is meant to implement some of the functionality of [SingSparrow](https://github.com/crodriguez-saltos/SingSparrow) by Carlos Rodríguez-Saltos in a simpler and more maintainable way. It's intended for the Raspberry Pi platform, but it's written in Python and should be easy to port to other environments.

## Installation

Install tools & dependencies:

```
sudo apt update
sudo apt install -y git python3-pip python3-gpiozero
```

Clone the repository:

```
git clone https://github.com/evan-goode/singsparrow-ii.git
cd singsparrow-ii/
```

Install:

```
sudo make install
```

The installation script will install a system-wide Python module, an example config file at `/etc/singsparrow-ii.toml`, and a systemd unit file, `singsparrow-ii.service`.

## Configuration & Usage

SingSparrow II looks for a [TOML](https://toml.io/en/) configuration file at `/etc/singsparrow-ii.toml`. The following example configuration is included:

```
schedule = "simple"
[[sensor]]
	label = "Key A"
	pin = 1
[[sensor]]
	label = "Key B"
	pin = 2
[[song]]
	label = "Song A"
	path = "/path/to/song-a.wav"
[[song]]
	label = "Song B"
	path = "/path/to/song-b.wav"
```

Two scheduling functions are available:

1. `simple`: A simple quota-based schedule. When a key is pressed and the quota for that key has not yet been reached, the song associated with that key will be played. After the quota for that key has been reached (currently set to 50 presses), no song will be played when the key is pressed. See the function `simple_quota_schedule`.

2. `self-balancing`: Try to balance the number of plays of each song while maintaining the associations between key and song. Initially, each key will have a high chance to play the song associated with that key, but as the associated song is played more and more, the odds of playing the associated song versus the other song approach 50/50. See `self_balancing_schedule`.

Note: new schedules should be easy to implement. A "schedule" is simply a function that takes the index of the pressed key, the time of the press, and the history of recent presses and returns the index of the sound to play, or None if no sound should be played.

Sensors and songs are associated by the order in which they're defined; i.e. the zeroth `[[sensor]]` block will be associated with the zeroth `[[song]]` block and so on.

Sensors are configured with a label (to be included in the output log) and a GPIO pin number (see https://gpiozero.readthedocs.io/en/stable/recipes.html#pin-numbering). Songs are configured with a label and the absolute path to a WAV file. WAV files can be anywhere on the filesystem, but make sure that the user running `singsparrow-ii` has read access!

A new log file is created each day in `/var/log/singsparrow-ii/` following the format `%Y-%m-%d.tsv`. The TSV files include the timestamp of a press, the sensor pressed, and the song played as a result.

To start the software:

```
sudo systemctl start singsparrow-ii.service
```

To run it automatically at boot:

```
sudo systemctl enable singsparrow-ii.service
```

To follow debug output:

```
sudo journalctl -fu singsparrow-ii
```

## License

[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
