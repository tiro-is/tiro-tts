from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from transformer.Models import Encoder, Decoder
from transformer.Layers import PostNet
from modules import VarianceAdaptor
from utils import get_mask_from_lengths
import hparams as hp

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class FastSpeech2(nn.Module):
    """ FastSpeech2 """

    def __init__(self, use_postnet=True):
        super(FastSpeech2, self).__init__()

        self.encoder = Encoder()
        self.variance_adaptor = VarianceAdaptor()

        self.decoder = Decoder()
        self.mel_linear = nn.Linear(hp.decoder_hidden, hp.n_mel_channels)

        self.use_postnet = use_postnet
        if self.use_postnet:
            self.postnet = PostNet()

    def forward(
            self,
            src_seq: torch.Tensor,
            src_len: torch.Tensor,
            mel_len: Optional[torch.Tensor] = None,
            d_target: Optional[torch.Tensor] = None,
            p_target: Optional[torch.Tensor] = None,
            e_target: Optional[torch.Tensor] = None,
            max_src_len: Optional[int] = None,
            max_mel_len: Optional[int] = None,
            d_control: float = 1.0,
            p_control: float = 1.0,
            e_control: float = 1.0,
    ) -> Tuple[
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor
    ]:
        src_mask = get_mask_from_lengths(src_len, max_src_len)
        mel_mask = get_mask_from_lengths(
            mel_len, max_mel_len) if mel_len is not None else None

        encoder_output = self.encoder(src_seq, src_mask)
        # if d_target is not None:
        #     # XXX: This branch is broken, self.decode.forward requires mel_mask to not be None
        #     variance_adaptor_output, d_prediction, p_prediction, e_prediction, _, _ = self.variance_adaptor(
        #         encoder_output, src_mask, mel_mask, d_target, p_target, e_target, max_mel_len, d_control, p_control, e_control)
        # else:
        variance_adaptor_output, d_prediction, p_prediction, e_prediction, mel_len, mel_mask = self.variance_adaptor(
            encoder_output, src_mask, mel_mask, d_target, p_target, e_target, max_mel_len, d_control, p_control, e_control)

        decoder_output = self.decoder(variance_adaptor_output, mel_mask)
        mel_output = self.mel_linear(decoder_output)

        if self.use_postnet:
            mel_output_postnet = self.postnet(mel_output) + mel_output
        else:
            mel_output_postnet = mel_output

        return mel_output, mel_output_postnet, d_prediction, p_prediction, e_prediction, src_mask, mel_mask, mel_len

    @torch.jit.export
    def inference(
        self,
        src_seq: torch.Tensor,
        d_control: float = 1.0,
        p_control: float = 1.0,
        e_control: float = 1.0,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Run inference using minimal inputs and outputs

        Returns:
          A tuple of tensors (mel_postnot, duration_prediction)
        """
        src_len = torch.tensor([src_seq.shape[1]])
        mel_len: Optional[torch.Tensor] = None
        d_target: Optional[torch.Tensor] = None
        p_target: Optional[torch.Tensor] = None
        e_target: Optional[torch.Tensor] = None
        max_src_len: Optional[int] = None
        max_mel_len: Optional[int] = None

        _, mel_postnet, d_prediction, *_ = self.forward(
            src_seq,
            src_len,
            mel_len,
            d_target,
            p_target,
            e_target,
            max_src_len,
            max_mel_len,
            d_control,
            p_control,
            e_control,
        )

        return mel_postnet, d_prediction

    @torch.jit.export
    def mobile_inference(
        self,
        src_seq: torch.Tensor,
    ) -> torch.Tensor:
        d_control: float = 1.0
        p_control: float = 1.0
        e_control: float = 1.0
        mel_postnet, _ = self.inference(src_seq, d_control, p_control, e_control)
        return mel_postnet


if __name__ == "__main__":
    # Test
    model = FastSpeech2(use_postnet=False)
    print("Model:")
    print(model)
    print(sum(param.numel() for param in model.parameters()))
