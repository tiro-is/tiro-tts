import pytest

from src.frontend.ssml import OldSSMLParser


def test_feed_invalid_data_raises():
    parser = OldSSMLParser()
    with pytest.raises(ValueError, match="Start tag is not <speak>"):
        parser.feed("hehe")


def test_feed_valid_but_empty():
    parser = OldSSMLParser()
    parser.feed("<speak></speak>")
    parser.close()
    assert parser.get_fastspeech_string() == ""


def test_feed_missing_closing_tags():
    parser = OldSSMLParser()
    parser.feed("<speak>")
    parser.close()
    with pytest.raises(ValueError, match="malformed"):
        parser.get_fastspeech_string()


def test_one_letter_xsampa():
    ssml = "<speak>Halló <phoneme alphabet='x-sampa' ph='a'>aa</phoneme></speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    parser.close()
    assert parser.get_fastspeech_string() == "Halló {a}"


def test_multi_letter_xsampa():
    ssml = "<speak>hei <phoneme alphabet='x-sampa' ph='apa'>ABBA</phoneme></speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    parser.close()
    assert parser.get_fastspeech_string() == "hei {a p a}"


def test_no_phonemes():
    text = "hei þetta gengur bara ágætlega!"
    ssml = f"<speak>{text}</speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    parser.close()
    assert parser.get_fastspeech_string() == text
