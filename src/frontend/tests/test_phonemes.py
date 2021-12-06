from ..phonemes import convert_ipa_to_xsampa, convert_xsampa_to_ipa, align_ipa_from_xsampa, _align_ipa

class TestConvertIpaToXsampa:
    def test_one_empty_lis(self):
        assert convert_ipa_to_xsampa([]) == []