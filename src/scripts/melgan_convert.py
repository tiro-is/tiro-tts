import argparse
import glob
import os
import textwrap

import torch

# From melgan:
from model.generator import Generator
from utils.hparams import HParam, load_hparam_str


def main(args: argparse.Namespace):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(
        args.checkpoint_path,
        map_location=device,
    )
    hp = load_hparam_str(checkpoint["hp_str"])

    model = Generator(hp.audio.n_mel_channels).to(device)
    model.load_state_dict(checkpoint["model_g"])
    model.eval()

    with torch.no_grad():
        melpath = list(glob.glob(os.path.join(args.input_folder, "*.mel")))[0]
        mel = torch.load(melpath)
        if len(mel.shape) == 2:
            mel = mel.unsqueeze(0)
        mel = mel.cpu()

        traced_model = torch.jit.trace(model, mel)
        torch.jit.save(traced_model, args.output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """\
            Convert a [PyTorch MelGAN model](https://github.com/seungwonpark/melgan)
            to TorchScript.
            """
        )
    )
    parser.add_argument(
        "-p",
        "--checkpoint_path",
        type=str,
        required=True,
        help="path to checkpoint pt file for evaluation",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        required=True,
        help="path to output TorchScript pt file",
    )
    parser.add_argument(
        "-i",
        "--input_folder",
        type=str,
        required=True,
        help="directory of mel-spectrograms to invert into raw audio. ",
    )
    args = parser.parse_args()

    main(args)
