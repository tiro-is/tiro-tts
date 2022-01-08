import torch
import torch.nn as nn
import torch.nn.functional as F

from .res_stack import ResStack


class Generator(nn.Module):
    def __init__(self, mel_channel: int):
        super(Generator, self).__init__()
        self.mel_channel: int = mel_channel

        self.generator = nn.Sequential(
            nn.ReflectionPad1d(3),
            nn.utils.weight_norm(nn.Conv1d(mel_channel, 512, kernel_size=7, stride=1)),

            nn.LeakyReLU(0.2),
            nn.utils.weight_norm(nn.ConvTranspose1d(512, 256, kernel_size=16, stride=8, padding=4)),

            ResStack(256),

            nn.LeakyReLU(0.2),
            nn.utils.weight_norm(nn.ConvTranspose1d(256, 128, kernel_size=16, stride=8, padding=4)),

            ResStack(128),

            nn.LeakyReLU(0.2),
            nn.utils.weight_norm(nn.ConvTranspose1d(128, 64, kernel_size=4, stride=2, padding=1)),

            ResStack(64),

            nn.LeakyReLU(0.2),
            nn.utils.weight_norm(nn.ConvTranspose1d(64, 32, kernel_size=4, stride=2, padding=1)),

            ResStack(32),

            nn.LeakyReLU(0.2),
            nn.ReflectionPad1d(3),
            nn.utils.weight_norm(nn.Conv1d(32, 1, kernel_size=7, stride=1)),
            nn.Tanh(),
        )

    def forward(self, mel: torch.Tensor) -> torch.Tensor:
        mel = (mel + 5.0) / 5.0 # roughly normalize spectrogram
        return self.generator(mel)

    def eval(self, inference=False):
        super(Generator, self).eval()

        # don't remove weight norm while validation in training loop
        if inference:
            self.remove_weight_norm()

    def remove_weight_norm(self):
        for idx, layer in enumerate(self.generator):
            if len(layer.state_dict()) != 0:
                try:
                    nn.utils.remove_weight_norm(layer)
                except:
                    layer.remove_weight_norm()

    @torch.jit.export
    def inference(self, mel: torch.Tensor) -> torch.Tensor:
        """Accepts the mel scale output from FastSpeech2 and returns a waveform in float.

        The sample rate will depend on the the training data, but the default is
        22050Hz. The caller is responsible for converting into int16.

        """
        mel = mel.transpose(1, 2)  # Necessary to handle output from FastSpeech2 module
        max_wav_value: float = 32768.0
        hop_length: int = 256
        # pad input mel with zeros to cut artifact
        # see https://github.com/seungwonpark/melgan/issues/8
        zero = torch.full((1, self.mel_channel, 10), -11.5129)
        mel = torch.cat((mel, zero), dim=2)

        audio = self.forward(mel)
        audio = audio.squeeze() # collapse all dimension except time axis
        audio = audio[:-(hop_length*10)]
        audio = max_wav_value * audio
        audio = audio.clamp(min=-max_wav_value, max=max_wav_value-1)
        # XXX: For some reason PyTorch Mobile Android can't handle converting to int16,
        #   converting to other types works:
        #   "at::Tensor scalar type is not supported on java side"
        #   So the caller has to handle it.
        # audio = audio.to(torch.int16)

        audio = audio * (20000 / torch.max(torch.abs(audio)))

        return audio


'''
    to run this, fix 
    from . import ResStack
    into
    from res_stack import ResStack
'''
if __name__ == '__main__':
    model = Generator(80)

    x = torch.randn(3, 80, 10)
    print(x.shape)

    y = model(x)
    print(y.shape)
    assert y.shape == torch.Size([3, 1, 2560])

    pytorch_total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(pytorch_total_params)