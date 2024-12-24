# HOW TO USE THIS THING
## Prereq setup for dependencies:
- install ffmpeg: https://www.gyan.dev/ffmpeg/builds/
  - add ffmpeg to path
- install peppi-py (can parse slp files): `py -m pip install peppi-py`
- install psutil `py -m pip install psutil`
- install natsort `py -m pip install natsort`
- have config set up to point to proper directory and have desired settings (see below)

## CONFIG INFO
    - melee_iso points to melee iso
    - dolphin_dir points to where dolphin playback is
    - ffmpeg can just be "ffmpeg" as long as its defined on the PATH
        - just need to make sure `which ffmpeg` works in CLI

## Notes and Acknowledgements
This is just a fork from an out-of-date project: https://github.com/davisdude/slp2mp4 (which itself is a fork of another deprecated slp2mp4 project), with the goal being to update it to be usable once again.


## The Future
Now that this tool is usable, I aim to eventually use this as a jumping-off-point to automate posting sets to yt when combining this with the slp replay manager nicolet has made (which I wanna fork and make some adjustments to).
The vision is the following:
1) Player is given USB before going to do set
 - possible right now with slp-replay-manager & nintendont version high enough to support USB hotswapping
2) Player returns USB. We use replay slp-replay-manager to auto-fill start.gg with character+game data from the set.
 - possible with slp-replay-manager
3) SLP files that were used to populate start.gg info are copied to a parent directory (configged in replay-manager), and placed into a subdir named the same as the round + players (ex: UW-MELEE-W25-01/Winners-Round-1-Invalid-vs-Ratlover)
 - Need to alter slp-replay-manager to do this
4) Post-tournament, the UW-MELEE-W25-01 folder is passed into `TOURNAMENT-TO-YT` script (yet to be completed. Had this as a dependency) & everything
 - Would be cool to run during tournament (and this was the dream), but having completed this, I see now the way the dolphin runner would work is it'd take quiteee a bit of time to convert each set. Makes more sense to just do it all in bulk after tournament.
   - May dig into this code more later to see if it's possible to get the dump_frame from dolphin while running the replay at 2x speed or something. I worry it'd mess up the audio though
 - I believe YT also throttles the number of uploads per hour (I think GIMR has run into this before iirc when I was looking into this like half a year ago?), so may need to be creative with how this script works...

Sidenote: One major problem I have with all of this is I personally do not own a laptop right now, so even with replay-manager edited, this is all kinda impossible to do on the day of a tournament...but I plan on rectifying that soon(tm)