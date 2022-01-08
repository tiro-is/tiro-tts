import argparse
import glob
import logging
import os
import textwrap

import torch

# From melgan:
from model.generator import Generator
from torch.utils.mobile_optimizer import optimize_for_mobile
from utils.hparams import HParam, load_hparam_str


def main(args: argparse.Namespace):
    logging.basicConfig(level=args.log_level)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(
        args.checkpoint_path,
        map_location=device,
    )
    hp = load_hparam_str(checkpoint["hp_str"])

    model = Generator(hp.audio.n_mel_channels).to(device)
    model.load_state_dict(checkpoint["model_g"])
    model.eval()
    model.requires_grad = False
    model.remove_weight_norm()

    melpaths = list(glob.glob(os.path.join(args.input_folder, "*.mel")))
    mel = torch.load(melpaths[0])
    if len(mel.shape) == 2:
        mel = mel.unsqueeze(0)
    mel = mel.cpu()

    scripted_model = torch.jit.script(model)

    if args.for_mobile:
        optimized_model = optimize_for_mobile(
            scripted_model, preserved_methods=["inference"]
        )
        optimized_model._save_for_lite_interpreter(args.output_path)
    else:
        frozen_model = torch.jit.freeze(scripted_model)
        # optimized_model = torch.jit.optimize_for_inference(frozen_model)
        torch.jit.save(scripted_model, args.output_path)


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
        help="directory of mel-spectrograms to invert into raw audio. ",
    )
    parser.add_argument(
        "--for_mobile",
        action="store_true",
        help="Should the output be optimized for mobile? And saved for the 'lite' interpreter?",
    )
    parser.add_argument(
        "--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO"
    )
    args = parser.parse_args()

    main(args)
