import pytest

from src.frontend.ssml import OldSSMLParser
from src.frontend.words import PhonemeProps, SpeakProps, Word


def test_feed_invalid_data_raises():
    parser = OldSSMLParser()
    with pytest.raises(ValueError, match="Start tag is not <speak>"):
        parser.feed("hehe")


def test_feed_valid_but_empty():
    parser = OldSSMLParser()
    parser.feed("<speak></speak>")
    parser.close()
    assert len(parser.get_words()) == 0


def test_feed_missing_closing_tags():
    parser = OldSSMLParser()
    parser.feed("<speak>")
    parser.close()
    with pytest.raises(ValueError, match="malformed"):
        parser.get_words()


def test_one_letter_xsampa():
    ssml = "<speak>Halló <phoneme alphabet='x-sampa' ph='a'>aa</phoneme></speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    parser.close()
    words = parser.get_words()
    assert words[0] == Word(
        original_symbol="Halló",
        ssml_props=SpeakProps("Halló "),
    )
    assert words[1] == Word(
        original_symbol="aa",
        phone_sequence=["a"],
        ssml_props=PhonemeProps(
            alphabet="x-sampa",
            ph="a",
            data="aa",
        ),
    )


def test_multi_letter_xsampa():
    ssml = "<speak>hei <phoneme alphabet='x-sampa' ph='apa'>ABBA</phoneme></speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    parser.close()
    words = parser.get_words()
    assert words[0] == Word(
        original_symbol="hei",
        ssml_props=SpeakProps("hei "),
    )
    assert words[1] == Word(
        original_symbol="ABBA",
        phone_sequence=["a", "p", "a"],
        ssml_props=PhonemeProps(
            alphabet="x-sampa",
            ph="apa",
            data="ABBA"
        ),
    )


def test_no_phonemes():
    text = "hei þetta gengur bara ágætlega!"
    ssml = f"<speak>{text}</speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    parser.close()

    for word, word_original in list(zip(parser.get_words(), text.split())):
        assert word == Word(
            original_symbol=word_original,
            ssml_props=SpeakProps(text)
        )
