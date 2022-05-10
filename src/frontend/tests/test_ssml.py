import pytest

from src.frontend.ssml import OldSSMLParser, SSMLValidationException


def test_feed_invalid_data_raises():
    parser = OldSSMLParser()
    with pytest.raises(SSMLValidationException, match="Start tag is not <speak>"):
        parser.feed("hehe")


def test_feed_empty():
    parser = OldSSMLParser()
    parser.feed("<speak></speak>")
    with pytest.raises(SSMLValidationException, match="The SSML did not contain any text!"):
        parser.get_text()
    parser.close()


def test_feed_missing_closing_tags():
    parser = OldSSMLParser()
    parser.feed("<speak>")
    parser.close()
    with pytest.raises(SSMLValidationException, match="malformed"):
        parser.get_text()


def test_get_text_phoneme_01():
    ssml = "<speak>Halló <phoneme alphabet='x-sampa' ph='a'>aa</phoneme></speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    parser.close()
    text = parser.get_text()
    assert text == "Halló aa"


def test_get_text_phoneme_02():
    ssml = "<speak>hei <phoneme alphabet='x-sampa' ph='apa'>ABBA</phoneme></speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    parser.close()
    text = parser.get_text()
    assert text == "hei ABBA"


def test_get_text_speak():
    text_original = "hei þetta gengur bara ágætlega!"
    ssml = f"<speak>{text_original}</speak>"
    parser = OldSSMLParser()
    parser.feed(ssml)
    text = parser.get_text()
    parser.close()
    assert text == text_original
