#!/usr/bin/env python3
import os, sys, json, subprocess, time, shutil, uuid, multiprocessing, psutil, glob
import argparse
import tempfile
import natsort
from pathlib import Path
from slippi import Game
from config import Config
from dolphinrunner import DolphinRunner
from ffmpegrunner import FfmpegRunner

FPS = 60
MIN_GAME_LENGTH = 30 * FPS
DURATION_BUFFER = 70              # Record for 70 additional frames

###############################################################################
# Misc utils
###############################################################################
def is_game_too_short(num_frames, remove_short):
    return num_frames < MIN_GAME_LENGTH and remove_short

def get_num_processes(conf):
    if conf.parallel_games == "recommended":
        return psutil.cpu_count(logical=False)
    else:
        return int(conf.parallel_games)

###############################################################################
# Run logic
###############################################################################
# Evaluate whether file should be run. The open in dolphin and combine video and audio with ffmpeg.
def record_file_slp(slp_file, outfile, conf):
    # Parse file with py-slippi to determine number of frames
    slippi_game = Game(slp_file)
    num_frames = slippi_game.metadata.duration + DURATION_BUFFER

    if is_game_too_short(slippi_game.metadata.duration, conf.remove_short):
        print("Warning: Game is less than 30 seconds and won't be recorded. Override in config.")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        with DolphinRunner(conf, conf.paths, tmpdir, uuid.uuid4()) as dolphin_runner:
            video_file, audio_file = dolphin_runner.run(slp_file, num_frames)

            # Encode
            ffmpeg_runner = FfmpegRunner(conf.ffmpeg)
            ffmpeg_runner.run(video_file, audio_file, outfile)

            print('Created {}'.format(outfile))

def combine(mp4s, out, conf):
    # Creates concat file
    tmp = tempfile.NamedTemporaryFile(mode='w+', delete=False)
    for mp4 in mp4s:
        mp4 = os.path.abspath(mp4)
        print(mp4)
        tmp.write(f"file '{mp4}'\n")
    tmp.close()
    out = os.path.abspath(out)

    ffmpeg_runner = FfmpegRunner(conf.ffmpeg)
    ffmpeg_runner.combine(tmp.name, out)

    os.unlink(tmp.name)

def get_mp4_name(slp):
    if slp.endswith('.slp'):
        slp = '.'.join(os.path.splitext(slp)[:-1])
    return slp + '.mp4'

def record_files(infiles, outdir, conf):
    file_mappings = [] # [(slp, mp4, conf), ...]
    to_combine = []    # [([vid1, vid2], out), ...]

    # Determines groupings and output names
    for infile in infiles:
        # Individual files just become mp4s and don't get combined
        if os.path.isfile(infile):
            outfile = get_mp4_name(os.path.join(outdir, Path(infile).parts[-1]))
            file_mappings.append((infile, outfile, conf))

        # Directories get grouped/combined by level
        elif os.path.isdir(infile):
            parent = Path(os.path.abspath(infile)).parts[-1]
            for subdir, _, fs in os.walk(infile):
                cur_outdir = os.path.join(
                    outdir,
                    parent,
                    os.path.relpath(subdir, infile)
                )
                os.makedirs(cur_outdir, exist_ok=True)
                cur_combine = []
                for f in fs:
                    mp4_name = os.path.join(cur_outdir, get_mp4_name(f))
                    file_mappings.append((os.path.join(subdir, f), mp4_name, conf))
                    cur_combine.append(mp4_name)
                cur_combine = natsort.natsorted(cur_combine)
                final_mp4_name = '-'.join(Path(cur_outdir).parts[1:]) + '.mp4'
                to_combine.append((cur_combine, os.path.join(outdir, final_mp4_name)))

    # Records mp4s
    num_processes = get_num_processes(conf)
    pool = multiprocessing.Pool(processes=num_processes)
    pool.starmap(record_file_slp, file_mappings)
    pool.close()

    # Combines mp4s
    if conf.combine:
        for files in to_combine:
            combine(files[0], files[1], conf)

        # Cleans up intermediate mp4s - done after to prevent premature dir deletion
        for files in to_combine:
            shutil.rmtree(
                os.path.join(*(Path(files[0][0]).parts[:-1])),
                ignore_errors=True
            )

###############################################################################
# Argument parsing
###############################################################################
def config_script(_=None):
    # TODO: Read slippi's config script to get ISO location?
    # TODO: Tab completion
    print('Entering configuration script...')
    conf = Config(False)
    with open(conf.paths.config_json, 'r+', encoding='utf-8') as f:
        data = json.load(f)
        for k, v in data.items():
            print(f"{k} (blank = '{v}'): ", end='')
            val = input()
            if val != '':
                data[k] = attempt_data_conversion(val)
        f.seek(0)
        json.dump(data, f, indent=4)
        f.truncate()

def run(args):
    os.makedirs(args.output_directory, exist_ok=True)
    while True:
        try:
            conf = Config()
            break
        except RuntimeError as e:
            print(e, file=sys.stderr)
            config_script()
    record_files(args.path, args.output_directory, conf)

# Parser configuration
def attempt_data_conversion(val):
    if val.lower() == 'false':
        return False
    elif val.lower() == 'true':
        return True
    else:
        try:
            return int(val)
        except ValueError:
            return val

def parser_is_file_or_dir(path):
    if os.path.isfile(path) or os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(f"'{path}' is not a valid file or directory")

parser = argparse.ArgumentParser(
    prog='slp2mp4',
    description='Convert slippi replay files for Super Smash Bros Melee to videos',
)
subparser = parser.add_subparsers(
    title='mode',
    help='Choose which action to execute',
    required=True
)

config_parser = subparser.add_parser('config', help='Run configuration helper')
config_parser.set_defaults(func=config_script)

run_parser = subparser.add_parser('run', help='Convert slps to mp4s')
run_parser.set_defaults(func=run)
run_parser.add_argument(
    '-o', '--output_directory',
    metavar='dir',
    help='Directory to put created mp4s',
    type=str,
    default='.',
)
run_parser.add_argument(
    'path',
    help='Slippi files/directories containing slippi files to convert',
    default='.',
    nargs='+',
    type=parser_is_file_or_dir,
)

def main():
    # Parse arguments
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
