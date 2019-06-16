#!/usr/bin/env python3

from collections import namedtuple
import csv
from datetime import datetime
import os
import subprocess
import time  # TODO

import toml

CONFIG_PATH = "/etc/songsparrow-ii.toml"
OUTPUT_DIRECTORY = "/var/log/songsparrow-ii/"
LOG_EXTENSION = "tsv"
LOG_DELIMITER = "\t"

SIDE_A = "a"
SIDE_B = "b"
SIDE_NEITHER = "neither"


def other_side(side):
    return SIDE_A if side == SIDE_B else SIDE_B


Press = namedtuple("Press", ("when", "key", "song_played"))


def simple_quota_schedule(key, history):
    quota = 30

    """Given a pressed key and a list of previous presses from earlier in the
    day, return which song to play """

    spent = sum(1 for press in history if press.song_played == key)
    print("spent is: ", spent)
    return key if spent < quota else SIDE_NEITHER


def get_day(when):
    return when.strftime("%Y-%m-%d")


def get_log_path(when):
    return os.path.join(OUTPUT_DIRECTORY, f"{get_day(when)}.{LOG_EXTENSION}")


# serialization/deserialization


def log_press(config, press):
    path = get_log_path(press.when)
    existed_already = os.path.isfile(path)
    with open(path, "a") as log_file:
        writer = csv.DictWriter(
            log_file,
            delimiter=LOG_DELIMITER,
            fieldnames=["timestamp", "key", "song-played"],
        )
        if not existed_already:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": press.when.timestamp(),
                "key": config["key-labels"][press.key],
                "song_played": config["song-labels"][press.song_played],
            }
        )


def parse_log_row(config, row):
    def unlabel(the_label, labels):
        for side, label in labels.items():
            if label == the_label:
                return side
        raise ValueError(
            f'Couldn\'t tell which side "{the_label}" was on. '
            "Corrupt log, or maybe labels were changed in {CONFIG_PATH}?"
        )

    when = datetime.fromtimestamp(float(row["timestamp"]))
    key = unlabel(row["key"], config["key-labels"])
    song_played = unlabel(row["song-played"], config["song-labels"])
    return Press(when, key, song_played)


def parse_log(config, when):
    path = get_log_path(when)
    if not os.path.isfile(path):
        return []
    with open(path, "r") as log_file:
        reader = csv.DictReader(log_file, delimiter=LOG_DELIMITER)
        return [parse_log_row(config, row) for row in reader]


def read_config():
    with open(CONFIG_PATH, "r") as config_file:
        return toml.load(config_file)


def play_song(config, song):
    subprocess.call(["aplay", config["song-paths"][song]])


def main():
    config = read_config()
    history = parse_log(config, datetime.now())
    print(f"Read {len(history)} presses from history.")

    def handle_key_press(key_pressed):
        now = datetime.now()
        if history and get_day(now) != get_day(history[-1].when):
            print("It's a new day, clearing history...")
            history.clear()

        song = simple_quota_schedule(key_pressed, history)
        if song != SIDE_NEITHER:
            play_song(config, song)
        press = Press(now, key=key_pressed, song_played=song)
        print(f"Logging {press}...")
        history.append(press)
        log_press(config, press)

    # simulations TODO
    time.sleep(1)
    for _ in range(30):
        handle_key_press(SIDE_A)
        handle_key_press(SIDE_B)


if __name__ == "__main__":
    main()
