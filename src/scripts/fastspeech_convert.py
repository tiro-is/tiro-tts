import argparse
import collections
import logging
import textwrap
from pathlib import Path
from typing import Iterable, Literal, NewType, Tuple, Union

import torch
from torch.quantization import get_default_qconfig
from torch.quantization.quantize_fx import convert_fx, prepare_fx
from torch.utils.mobile_optimizer import optimize_for_mobile

from src.frontend.lexicon import SimpleInMemoryLexicon, read_kaldi_lexicon
from src.lib.fastspeech import hparams
from src.lib.fastspeech.synthesize import FastSpeech2
from src.lib.fastspeech.text import text_to_sequence

PronunciationAlphabet = Literal["x-sampa", "ipa"]


def calibration_seqs_from_lex_for_mobile(
    lexicon: Path,
    native_alphabet: PronunciationAlphabet = "x-sampa",
) -> Iterable[torch.Tensor]:
    return calibration_seqs_from_lex(
        lexicon,
        native_alphabet,
    )


def calibration_seqs_from_lex_for_server(
    lexicon: Path,
    native_alphabet: PronunciationAlphabet = "x-sampa",
) -> Iterable[Tuple[torch.Tensor, float, float, float]]:
    duration_control = pitch_control = energy_control = 1.0
    return (
        (t, duration_control, pitch_control, energy_control)
        for t in calibration_seqs_from_lex(
            lexicon,
            native_alphabet,
        )
    )


def calibration_seqs_from_lex(
    lexicon: Path,
    native_alphabet: PronunciationAlphabet = "x-sampa",
) -> Union[Iterable[torch.Tensor], Iterable[Tuple[torch.Tensor, float, float, float]]]:
    """Load lexicon as calibration data input for FastSpeech2 model.

    Yields:
      tuple of (text_seq, src_len, duration_control, pitch_control, energy_control)
    """
    words = list(read_kaldi_lexicon(lexicon).keys())
    lookup_lexicon = SimpleInMemoryLexicon(lexicon, native_alphabet)

    for word in words[:-1:20]:
        phone_seq = lookup_lexicon.get(word)
        text_seq = torch.tensor(
            [text_to_sequence("{%s}" % " ".join(phone_seq), hparams.text_cleaners)],
            dtype=torch.int64,
        )
        yield text_seq


def calibrate_for_server(
    model: torch.nn.Module,
    inputs: Iterable[Tuple[torch.Tensor, float, float, float]],
) -> None:
    model.eval()
    for (text_seq, duration_control, pitch_control, energy_control) in inputs:
        _ = model.inference(
            text_seq,
            d_control=duration_control,
            p_control=pitch_control,
            e_control=energy_control,
        )


def calibrate_for_mobile(
    model: torch.nn.Module,
    inputs: Iterable[torch.Tensor],
) -> None:
    model.eval()
    for text_seq in inputs:
        _ = model.mobile_inference(
            text_seq,
        )


def quantize(
    float_model: FastSpeech2,
    calibration_lexicon: Path,
    lexicon_alphabet: PronunciationAlphabet,
    engine: Literal["fbgemm", "qnnpack"] = "fbgemm",
) -> torch.nn.Module:
    """Quantize model using FX Graph mode post training static quantization."""
    logging.info("Before quantization: %s", float_model)

    qconfig = get_default_qconfig(engine)
    qconfig_dict = {
        "": qconfig,
    }

    float_model.postnet = prepare_fx(float_model.postnet, qconfig_dict)
    float_model.mel_linear = prepare_fx(float_model.mel_linear, qconfig_dict)

    encoder = float_model.encoder
    for idx, layer in enumerate(encoder.layer_stack):
        layer.pos_ffn = prepare_fx(layer.pos_ffn, qconfig_dict)
        layer.slf_attn.w_qs = prepare_fx(layer.slf_attn.w_qs, qconfig_dict)
        layer.slf_attn.w_ks = prepare_fx(layer.slf_attn.w_ks, qconfig_dict)
        layer.slf_attn.w_vs = prepare_fx(layer.slf_attn.w_vs, qconfig_dict)
        layer.slf_attn.layer_norm = prepare_fx(layer.slf_attn.layer_norm, qconfig_dict)
        layer.slf_attn.fc = prepare_fx(layer.slf_attn.fc, qconfig_dict)
    encoder.src_word_emb = prepare_fx(encoder.src_word_emb, qconfig_dict)

    decoder = float_model.decoder
    for idx, layer in enumerate(decoder.layer_stack):
        layer.pos_ffn = prepare_fx(layer.pos_ffn, qconfig_dict)
        layer.slf_attn.w_qs = prepare_fx(layer.slf_attn.w_qs, qconfig_dict)
        layer.slf_attn.w_ks = prepare_fx(layer.slf_attn.w_ks, qconfig_dict)
        layer.slf_attn.w_vs = prepare_fx(layer.slf_attn.w_vs, qconfig_dict)
        layer.slf_attn.layer_norm = prepare_fx(layer.slf_attn.layer_norm, qconfig_dict)
        layer.slf_attn.fc = prepare_fx(layer.slf_attn.fc, qconfig_dict)

    if engine == "qnnpack":
        calibrate_for_mobile(
            float_model,
            calibration_seqs_from_lex_for_mobile(calibration_lexicon, lexicon_alphabet),
        )
    else:
        calibrate_for_server(
            float_model,
            calibration_seqs_from_lex_for_server(calibration_lexicon, lexicon_alphabet),
        )

    float_model.postnet = convert_fx(float_model.postnet)
    float_model.mel_linear = convert_fx(float_model.mel_linear)

    for idx, layer in enumerate(encoder.layer_stack):
        layer.pos_ffn = convert_fx(layer.pos_ffn)
        layer.slf_attn.w_qs = convert_fx(layer.slf_attn.w_qs)
        layer.slf_attn.w_ks = convert_fx(layer.slf_attn.w_ks)
        layer.slf_attn.w_vs = convert_fx(layer.slf_attn.w_vs)
        layer.slf_attn.layer_norm = convert_fx(layer.slf_attn.layer_norm)
        layer.slf_attn.fc = convert_fx(layer.slf_attn.fc)
    encoder.src_word_emb = convert_fx(encoder.src_word_emb)

    for idx, layer in enumerate(decoder.layer_stack):
        layer.pos_ffn = convert_fx(layer.pos_ffn)
        layer.slf_attn.w_qs = convert_fx(layer.slf_attn.w_qs)
        layer.slf_attn.w_ks = convert_fx(layer.slf_attn.w_ks)
        layer.slf_attn.w_vs = convert_fx(layer.slf_attn.w_vs)
        layer.slf_attn.layer_norm = convert_fx(layer.slf_attn.layer_norm)
        layer.slf_attn.fc = convert_fx(layer.slf_attn.fc)

    logging.info("After quantization: %s", float_model)

    return float_model


def main(args: argparse.Namespace):
    logging.basicConfig(level=args.log_level)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    original_state_dict = torch.load(args.checkpoint_path, map_location=device)["model"]
    new_state_dict = collections.OrderedDict()
    for key, val in original_state_dict.items():
        new_state_dict[key.replace("module.", "")] = val

    model = FastSpeech2()
    model.load_state_dict(new_state_dict)
    model.requires_grad = False
    model.eval()

    if args.quantize:
        if not args.calibration_lexicon:
            raise RuntimeError("Quantization requires --calibration-lexicon!")
        model = quantize(
            model,
            args.calibration_lexicon,
            args.lexicon_alphabet,
            engine="qnnpack" if args.for_mobile else "fbgemm",
        )

    scripted_model = torch.jit.script(model)
    if args.for_mobile:
        optimized_model = optimize_for_mobile(
            scripted_model, preserved_methods=["mobile_inference"]
        )
        optimized_model._save_for_lite_interpreter(args.output_path)
    else:
        optimized_model = torch.jit.freeze(
            scripted_model, preserved_attrs=["inference"]
        )
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
        "--for_mobile",
        action="store_true",
        help="Should the output be optimized for mobile? And saved for the 'lite' interpreter?",
    )
    parser.add_argument(
        "--quantize",
        action="store_true",
        help="Should the model be quantized into int8?",
    )
    parser.add_argument(
        "--calibration_lexicon",
        type=Path,
    )
    parser.add_argument(
        "--lexicon_alphabet",
        choices=("ipa", "x-sampa"),
        default="x-sampa",
        help="Pronunciation alphabet used by CALIBRATION_LEXICON.",
    )
    parser.add_argument(
        "--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO"
    )
    args = parser.parse_args()

    main(args)
