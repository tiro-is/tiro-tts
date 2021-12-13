import argparse
import collections
import textwrap

import torch
from torch.utils.mobile_optimizer import optimize_for_mobile

from src.lib.fastspeech.synthesize import FastSpeech2


def main(args: argparse.Namespace):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    original_state_dict = torch.load(args.checkpoint_path, map_location=device)["model"]
    new_state_dict = collections.OrderedDict()
    for key, val in original_state_dict.items():
        new_state_dict[key.replace("module.", "")] = val

    model = FastSpeech2()
    model.load_state_dict(new_state_dict)
    model.requires_grad = False
    model.eval()

    scripted_model = torch.jit.script(model)
    if args.for_mobile:
        optimized_model = optimize_for_mobile(scripted_model)
        optimized_model._save_for_lite_interpreter(args.output_path)
    else:
        optimized_model = torch.jit.freeze(scripted_model)
        # TODO(rkjaran): Use this once PyTorch actually supports its serialization
        # optimized_model = torch.jit.optimize_for_inference(optimized_model)
        torch.jit.save(optimized_model, args.output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(
            """\
            Convert a [PyTorch Fastspeech2 model](https://github.com/cadia-lvl/fastspeech2)
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
        "--for-mobile",
        action="store_true",
        help="Should the output be optimized for mobile? And saved for the 'lite' interpreter?",
    )
    args = parser.parse_args()

    main(args)
