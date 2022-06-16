# Copyright 2021-2022 Tiro ehf.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import re
from abc import ABC
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Tuple

import tokenizer

from src.frontend.lexicon import LangID
from src.frontend.phonemes import (
    ALIGNER_XSAMPA,
    ALIGNER_XSAMPA_SYLL_STRESS,
    PhoneSeq,
    align_ipa_from_xsampa,
)


# TODO(rkjaran): There are cases where we have to support nested SSML tags, e.g. we can
#   have nested prosody tags.
class SSMLProps(ABC):
    tag_type: str
    tag_val: str
    data: str

    def get_data(self):
        return self.data

    def is_multi(self, alternate_data: str = None) -> bool:
        data = alternate_data if alternate_data else self.data
        return len(data.split()) > 1


class SpeakProps(SSMLProps):
    def __init__(
        self,
        tag_val: str,
        data: str = "",
    ):
        self.tag_type = "speak"
        self.tag_val = tag_val
        self.data = data

    def __repr__(self):
        return "<SpeakProps(tag_type='{}', tag_val='{}', data='{}')>".format(
            self.tag_type,
            self.tag_val,
            self.data,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SpeakProps) and (
            self.tag_type == other.tag_type
            and self.tag_val == other.tag_val
            and self.data == other.data
        )


class PhonemeProps(SSMLProps):
    read: bool

    def __init__(
        self,
        tag_val: str,
        alphabet: Literal["x-sampa", "ipa"] = "",
        ph: str = "",
        data: str = "",
    ):
        self.tag_val = tag_val
        self.alphabet = alphabet
        self.ph = ph
        self.tag_type = "phoneme"
        self.data = data
        self.read = False

    def get_phone_sequence(
        self, alphabet: Literal["ipa", "x-sampa", "x-sampa+syll+stress"]
    ) -> List[str]:
        if alphabet not in ["ipa", "x-sampa", "x-sampa+syll+stress"]:
            raise ValueError("Illegal alphabet choice: {}".format(alphabet))

        if not self.read:
            self.read = True

            # SSML markup only allows x-sampa phone sequences in the phoneme tags. Some models,
            # like Fastspeech, only accept IPA phone sequences and, therefore, this function
            # offers conversion from x-sampa to IPA if required.

            try:
                # If alignment fails, the phone sequence (ph) is illegal.
                if alphabet == "ipa":
                    return align_ipa_from_xsampa(self.ph).split()
                if alphabet == "x-sampa":
                    return ALIGNER_XSAMPA.align(self.ph).split()
                if alphabet == "x-sampa+syll+stress":
                    return ALIGNER_XSAMPA_SYLL_STRESS.align(self.ph).split()
            except Exception as e:
                raise ValueError(
                    "<phoneme> error: Illegal phoneme sequence in 'ph' attribute\n{}".format(
                        e
                    )
                )
        return []

    def __repr__(self):
        return "<PhonemeProps(alphabet='{}', ph='{}', tag_type='{}', tag_val='{}', data='{}')>".format(
            self.alphabet,
            self.ph,
            self.tag_type,
            self.tag_val,
            self.data,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PhonemeProps) and (
            self.alphabet == other.alphabet
            and self.ph == other.ph
            and self.tag_type == other.tag_type
            and self.tag_val == other.tag_val
            and self.data == other.data
        )


class SubProps(SSMLProps):
    def __init__(
        self,
        tag_val: str,
        data: str,
        alias: str,
    ):
        self.tag_val = tag_val
        self.alias = alias
        self.tag_type = "sub"
        self.data = data

    def get_alias(self):
        return self.alias

    def __repr__(self):
        return "<SubProps(alias='{}', tag_type='{}', tag_val='{}', data='{}')>".format(
            self.alias,
            self.tag_type,
            self.tag_val,
            self.data,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SubProps) and (
            self.alias == other.alias
            and self.tag_type == other.tag_type
            and self.tag_val == other.tag_val
            and self.data == other.data
        )


class SayAsProps(SSMLProps):
    interpret_as: str

    DIGITS_DIC: Dict[str, str] = {
        "0": "núll",
        "1": "einn",
        "2": "tveir",
        "3": "þrír",
        "4": "fjórir",
        "5": "fimm",
        "6": "sex",
        "7": "sjö",
        "8": "átta",
        "9": "níu",
    }

    KENNITALA_DIC: Dict[str, str] = {
        "10": "tíu",
        "11": "ellefu",
        "12": "tólf",
        "13": "þrettán",
        "14": "fjórtán",
        "15": "fimmtán",
        "16": "sextán",
        "17": "sautján",
        "18": "átján",
        "19": "nítján",
        "2": "tuttugu og",
        "3": "þrjátíu og",
        "4": "fjörtíu og",
        "5": "fimmtíu og",
        "6": "sextíu og",
        "7": "sjötíu og",
        "8": "áttatíu og",
        "9": "níutíu og",
    }

    CHARACTERS_DIC: Dict[str, str] = {
        ".": "punktur",
        ",": "komma",
        " ": "bil",
        ":": "tvípunktur",
        ";": "semi komma",
        "?": "spurningarmerki",
        "!": "upphrópunarmerki",
        "+": "plús",
        "-": "bandstrik",
        "/": "skástrik",
        "*": "stjarna",
        "%": "prósentumerki",
        "„": "gæsalappir opnast",
        "“": "gæsalappir lokast",
        '"': "gæsalappir",
        "'": "gæsalappir",
        "#": "myllumerki",
        "$": "dollaramerki",
        "&": "og, merki",
        "(": "svigi opnast",
        ")": "svigi lokast",
        "[": "hornklofi opnast",
        "]": "hornklofi lokast",
        "{": "slaufusvigi opnast",
        "}": "slaufusvigi lokast",
        "=": "jafnaðarmerki",
        "~": "tilda",
        "°": "gráðumerki",
    }

    TELEPHONE_SPECIAL_CASES: Dict[str, str] = {
        "118": "hundrað og átján",
        "5885522": "fimm, átta, átta, fimm, fimm, tveir, tveir",
    }

    DELIMITER: str = ", "

    CHARACTERS: str = "characters"
    SPELL_OUT: str = "spell-out"
    DIGITS: str = "digits"
    KENNITALA: str = "kennitala"
    TELEPHONE: str = "telephone"

    def __init__(
        self,
        tag_val: str,
        interpret_as: str,
        data: str,
    ):
        self.tag_val = tag_val
        self.interpret_as = interpret_as
        self.data = data
        self.tag_type = "say-as"

        self.CHARACTERS_DIC.update(self.DIGITS_DIC)

    def _process_kennitala(self) -> str:
        """
        Determines if data is on an Icelandic kennitala format.
        Does NOT determine if kennitala is an actual legal kennitala.
        A kennitala should consist of exactly 10 digits with leading and trailing whitespace characters and dashes optionally allowed.

        Therefore, these formats are legal:
        1. "######-####"
        2. "##########"

        # "###### ####" is not allowed for now, as Regina normalizer crashes during its processing.

        Used for validation and processing of <say-as interpret-as='kennitala'> tags.
        """

        if self.get_interpret_as() != self.KENNITALA:
            raise ValueError(
                "Incorrect usage! say-as->interpret-as value must be 'kennitala' for kennitala processing."
            )

        err_msg: str = "Malformed 'kennitala' value in <say-as interpret-as='kennitala'> tag: '{}'\nAllowed formats are:\n1. ######-####\n2. ##########"

        # TODO(Smári): Strip internal whitespace chars too when Regina has been patched. (and not char.isspace())
        data = "".join(
            [char for char in self.get_data().strip() if char != "-"]   # We strip all leading and trailing whitespace characters along with any dash characters, leaving only digits.
        )
        if (
            len(data) != 10 or not data.isdecimal()                     # 10 is min. length for kennitala. If there are nonnumerical characters present, the string is illegal.
        ):
            raise ValueError(err_msg.format(data))

        PAIR_SIZE: int = 2
        kt_pairs: List[Tuple[str, str]] = [
            (data[i], data[i + 1]) for i in range(0, len(data), PAIR_SIZE)  # We split the string into pairs: "2810895479" -> [('2', '8'), ('1', '0'), ('8', '9'), ('5', '4'), ('7', '9')]
        ]

        # Now we map the digit pairs to their spoken text strings.
        kt_text_vals: List[str] = []
        for pair in kt_pairs:
            if pair[0] == "0":
                kt_text_vals.extend(
                    [
                        self.DIGITS_DIC[pair[0]],
                        self.DIGITS_DIC[pair[1]],
                    ]
                )
            elif pair[0] == "1":
                kt_text_vals.append(self.KENNITALA_DIC[f"{pair[0]}{pair[1]}"])
            else:
                kt_text_vals.append(
                    f"{self.KENNITALA_DIC[pair[0]]} {self.DIGITS_DIC[pair[1]]}"
                )
                
        #                                        [('2', '8'), ('1', '0'), ('8', '9'), ('5', '4'), ('7', '9')]
        # Finally, we return a string like this: "tuttugu og átta, tíu, áttatíu og níu, fimmtíu og fjórir, sjötíu og níu"
        return self.DELIMITER.join(
            kt_text_vals
        )

    def _process_number_pairs(self, pairs: List[Tuple[str, str]]) -> List[str]:
        """
        Turns number pairs into spoken values.
        """
        # TODO(Smári): Let _process_kennitala() utilize this function.

        text_vals: List[str] = []
        for pair in pairs:
            if pair[0] == "0":
                text_vals.extend(
                    [
                        self.DIGITS_DIC[pair[0]],
                        self.DIGITS_DIC[pair[1]],
                    ]
                )
            elif pair[0] == "1":
                text_vals.append(self.KENNITALA_DIC[f"{pair[0]}{pair[1]}"])
            else:
                text_vals.append(
                    f"{self.KENNITALA_DIC[pair[0]]} {self.DIGITS_DIC[pair[1]]}"
                )
        return text_vals

    def _clean_telephone_num(self, number: str, country_code: bool = False) -> str:
        """
        Gets rid of dashes and whitespace characters from number.
        Validates that number contains only digits afterwards.
        country_code: If set, the function will give a special treatment to country codes
        that additionally require removal of the "+" symbol.
        """
        remove_lis = ["-"]
        if country_code:
            remove_lis.append("+")

        # Strip all whitespaces and dashes from string.
        number = "".join([digit for digit in number if not digit.isspace() and digit not in remove_lis])

        err_msg: str = "Malformed 'telephone' value in <say-as interpret-as='telephone'> tag: '{}'\n{}"
        if not number.isdecimal():
            # If the stripped string contains nonnumerical characters then it is not a valid phone number.
            raise ValueError(
                err_msg.format(
                    number, 
                    "{} must be digits only with optionally allowed {}.".format(
                        "country code" if country_code else "telephone number",
                        "single '+' symbol in front" if country_code else "whitespace characters and dashes",
                    )
                )
            )
        return number

    def _process_telephone(self):
        """
        Determines if data is on a telephone format.
        Does NOT determine if telephone data value holds an actual valid telephone number.
        A telephone data value should consist of exactly three, four or seven digits with whitespace characters and dashes optionally allowed.
        A country code prefix is allowed and should start with a "+" and end with a whitespace.

        Used for validation and processing of <say-as interpret-as='telephone'> tags.
        """
        # Icelandic phone numbers are exclusively of these lengths. (According to Wikipedia!)
        ICELANDIC_NUMBER_LENGTHS: List[int] = [3, 4, 7]
        err_msg: str = "Malformed 'telephone' value in <say-as interpret-as='telephone'> tag: '{}'\n{}"
        
        pn_text_vals: List[str] = []
        if self.get_data().startswith("+"):
            raise NotImplemented("Country code telephone number processing is yet to be implemented!")

            # Country code processing
            telephone_info: List[str] = self.get_data().strip().split(maxsplit=1)
            if len(telephone_info) > 2:
                raise ValueError(err_msg.format(self.get_data(), "Country codes must start with a '+' and be separated by whitespace from the remainder of the telephone number."))
            
            country_code: str = telephone_info[0]   # TODO: Clean individually using _clean_telephone_num() to isolate number and validate it.
            phone_number: str = telephone_info[1]   # TODO: Clean individually using _clean_telephone_num() to isolate number and validate it.
            # To be continued...
        else:
            # With no country code provided, we assume the input number is Icelandic. Thus we deny further processing
            # if it is not of a correct length.
            telephone: str = self._clean_telephone_num(
                self.get_data()
            )

            number_length: int = len(telephone)
            if not number_length in ICELANDIC_NUMBER_LENGTHS:
                raise ValueError(err_msg.format(self.get_data(), "Icelandic phone number must be either 3, 4 or 7 digit long. For non-Icelandic phonenumbers, please add a country code."))
            
            if telephone in self.TELEPHONE_SPECIAL_CASES:
                pn_text_vals.append(
                    self.TELEPHONE_SPECIAL_CASES["telephone"]
                )
            elif number_length == 7:
                # We split the last four digits into pairs: "553-8000" -> [('8', '0'), ('0', '0')]
                first_three: List[str] = telephone[:3]
                last_four: List[str] = telephone[3:]
                
                PAIR_SIZE: int = 2
                last_four_pairs: List[Tuple[str, str]] = [
                    (last_four[i], last_four[i + 1]) for i in range(0, 4, PAIR_SIZE)
                ]

                for digit in first_three:
                    pn_text_vals.append(
                        self.DIGITS_DIC[digit]
                    )

                # If the latter pair is 00 ("x000", "0x00", "xx00" where x != "0"), we want the whole four to be pronounced as a single number.
                # "563-5000" -> "fimm, sex, þrír, fimm þúsund", "587-3300" -> "fimm, átta, sjö, þrjú þúsund og þrjú hundruð", "848 0500" -> "átta, fjórir, átta, núll, fimm hundruð"
                if (
                    last_four_pairs[1][0] == "0" 
                    and last_four_pairs[1][1] == "0"
                ):
                    # Determine which of the three cases we are dealing with ("x000", "0x00", "xx00" where x != "0").

                    # This is a special case of only four values, so no need to add to the class constant dictionaries.
                    DIGITS_NEUTRAL: Dict[str, str] = {
                        "1": "eitt",
                        "2": "tvö",
                        "3": "þrjú",
                        "4": "fjögur",
                    }
                    thousand_special = last_four_pairs[0][0] in DIGITS_NEUTRAL
                    hundred_special = last_four_pairs[0][1] in DIGITS_NEUTRAL
                    
                    if last_four_pairs[0][0] != "0" and last_four_pairs[0][1] == "0":       # x000
                        # append "x þúsund"
                        pn_text_vals.extend(
                            [
                                DIGITS_NEUTRAL[
                                    last_four_pairs[0][0]
                                ] if thousand_special else
                                self.DIGITS_DIC[
                                    last_four_pairs[0][0]
                                ],
                                "þúsund"
                            ]
                        )
                    elif last_four_pairs[0][0] == "0" and last_four_pairs[0][1] != "0":     # 0x00
                        # append "núll x hundruð"
                        pn_text_vals.extend(
                            [
                                "núll",
                                DIGITS_NEUTRAL[
                                    last_four_pairs[0][1]
                                ] if hundred_special else
                                self.DIGITS_DIC[
                                    last_four_pairs[0][1]
                                ],
                                "hundruð"
                            ]
                        )
                    elif last_four_pairs[0][0] != "0" and last_four_pairs[0][1] != "0":     # xx00
                        # append "x þúsund og x hundruð"
                        pn_text_vals.extend(
                            [
                                DIGITS_NEUTRAL[
                                    last_four_pairs[0][0]
                                ] if thousand_special else
                                self.DIGITS_DIC[
                                    last_four_pairs[0][0]
                                ],
                                "og",
                                DIGITS_NEUTRAL[
                                    last_four_pairs[0][1]
                                ] if hundred_special else
                                self.DIGITS_DIC[
                                    last_four_pairs[0][1]
                                ],
                                "hundruð"
                            ]
                        )
                else:
                    pn_text_vals.extend(
                        self._process_number_pairs(
                            last_four_pairs
                        )
                    )
            elif number_length == 4:
                pn_text_vals.extend(
                        self._process_number_pairs(
                            last_four_pairs
                        )
                )
            else:
                # Three digit Icelandic phonenumbers
                for digit in telephone:
                    pn_text_vals.append(
                        self.DIGITS_DIC[digit]
                    )

            return self.DELIMITER.join(
                pn_text_vals
            )

    def get_interpret_as(self):
        return self.interpret_as

    def get_interpretation(self, token: str = ""):
        type: Literal["characters", "spell-out", "digits", "kennitala", "telephone"] = self.get_interpret_as()
        if type in [self.CHARACTERS, self.SPELL_OUT]:
            return self.DELIMITER.join(
                [
                    self.CHARACTERS_DIC[char]
                    if char in self.CHARACTERS_DIC
                    else char.lower()
                    for char in self.get_data()
                ]
            )
        elif type == self.DIGITS:
            return self.DELIMITER.join(
                [
                    self.CHARACTERS_DIC[char]
                    if char in self.CHARACTERS_DIC
                    else char.lower()
                    for char in token
                ]
            )
        elif type == self.KENNITALA:
            return self._process_kennitala()
        elif type == self.TELEPHONE:
            return self._process_telephone()

        raise ValueError(
            '<say-as> error: Encountered unsupported interpretation type: "{}"'.format(
                type
            )
        )

    def __repr__(self):
        return "<SayAsProps(interpret-as='{}', tag_type='{}', tag_val='{}', data='{}')>".format(
            self.interpret_as,
            self.tag_type,
            self.tag_val,
            self.data,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SayAsProps) and (
            self.interpret_as == other.interpret_as
            and self.tag_type == other.tag_type
            and self.tag_val == other.tag_val
            and self.data == other.data
        )


class ProsodyProps(SSMLProps):
    rate: float
    PREDEFINED_RATES: Dict[str, float] = {
        "x-slow": 0.5,
        "slow": 0.75,
        "medium": 1.0,
        "fast": 1.25,
        "x-fast": 1.75,
    }
    RATE_MIN = 0.2
    RATE_MAX = 2.0

    pitch: float
    PREDEFINED_PITCH: Dict[str, float] = {
        "default": 1.0,
        "x-low": 0.8,
        "low": 0.9,
        "medium": 1.0,
        "high": 1.1,
        "x-high": 1.2,
    }
    PITCH_MIN = 0.5
    PITCH_MAX = 2.0

    # in decibels
    volume: float
    PREDEFINED_VOLUME: Dict[str, float] = {
        "default": 0.0,
        "silent": -20.0,
        "x-soft": -10.0,
        "soft": -6.0,
        "medium": 0.0,
        "loud": 6.0,
        "x-loud": 10.0,
    }

    def __init__(
        self,
        *,
        tag_val: str,
        data: str,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        volume: Optional[str] = None,
    ):
        """Prosody properties

        Args:
          rate:
            x-slow, slow, medium, fast, x-fast. Sets the pitch to a predefined value for
            the selected voice.

            n%: A non-negative percentage change in the speaking rate. For example, a
            value of 100% means no change in speaking rate, a value of 200% means a
            speaking rate twice the default rate, and a value of 50% means a speaking
            rate of half the default rate. This value has a range of 20-200%.

          pitch:
            default: Resets pitch to the default level for the current voice.

            x-low, low, medium, high, x-high: Sets the pitch to a predefined value for
            the current voice.

            +n% or -n%: Adjusts pitch by a relative percentage. For example, a value of
            +0% means no baseline pitch change, +5% gives a little higher baseline
            pitch, and -5% results in a little lower baseline pitch.

          volume:
            default: Resets volume to the default level for the current voice.

            silent, x-soft, soft, medium, loud, x-loud: Sets the volume to a predefined
            value for the current voice.

            +ndB, -ndB: Changes volume relative to the current level. A value of +0dB
            means no change, +6dB means approximately twice the current volume, and -6dB
            means approximately half the current volume.


        NOTE: "default" is supposed to reset the pitch/volume, while everything else
          accumulates. We do not currently support nested <prosody> tags so there's
          nothing to accumulate.

        """
        self.tag_val = tag_val
        self.tag_type = "prosody"
        self.data = data

        if rate is not None:
            if rate.endswith("%"):
                self.rate = float(rate[:-1]) / 100
                if self.rate > ProsodyProps.RATE_MAX:
                    self.rate = ProsodyProps.RATE_MAX
                elif self.rate < ProsodyProps.RATE_MIN:
                    self.rate = ProsodyProps.RATE_MIN
            else:
                try:
                    self.rate = ProsodyProps.PREDEFINED_RATES[rate]
                except KeyError:
                    raise ValueError("Non-existent prosody rate specifier")
        else:
            self.rate = 1.0

        if pitch is not None:
            try:
                m = re.match(r"([\-+])([0-9]{1,3})%", pitch)
                if not m:
                    self.pitch = ProsodyProps.PREDEFINED_PITCH[pitch]
                else:
                    op, percent = m[1], m[2]
                    adjustment = float(percent) / 100
                    self.pitch = 1.0 + (-adjustment if op == "-" else adjustment)
                    if self.pitch < ProsodyProps.PITCH_MIN:
                        self.pitch = ProsodyProps.PITCH_MIN
                    elif self.pitch > ProsodyProps.PITCH_MAX:
                        self.pitch = ProsodyProps.PITCH_MAX
            except (KeyError, ValueError):
                raise ValueError("Non-existent prosody pitch specifier")
        else:
            self.pitch = 1.0

        if volume is not None:
            try:
                m = re.match(r"([\-+][0-9]{1,2})d[Bb]", volume)
                if not m:
                    self.volume = ProsodyProps.PREDEFINED_VOLUME[volume]
                else:
                    self.volume = float(m[1])
            except (KeyError, ValueError):
                raise ValueError("Non-existent prosody volume specifier")
        else:
            self.volume = 0.0

    def __repr__(self):
        return "<ProsodyProps(rate='{}', pitch='{}', volume='{}', tag_type='{}', tag_val='{}', data='{}')>".format(
            self.rate,
            self.pitch,
            self.volume,
            self.tag_type,
            self.tag_val,
            self.data,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ProsodyProps) and (
            self.rate == other.rate
            and self.pitch == other.pitch
            and self.volume == other.volume
            and self.tag_type == other.tag_type
            and self.tag_val == other.tag_val
            and self.data == other.data
        )


class Word:
    """A wrapper for individual symbol and its metadata."""

    def __init__(
        self,
        original_symbol: str = "",
        symbol: str = "",
        phone_sequence: List[str] = [],
        start_byte_offset: int = 0,
        end_byte_offset: int = 0,
        start_time_milli: int = 0,
        ssml_props: SSMLProps = None,
    ):
        self.original_symbol = original_symbol
        self.symbol = symbol
        self.phone_sequence = phone_sequence
        self.start_byte_offset = start_byte_offset
        self.end_byte_offset = end_byte_offset
        self.start_time_milli = start_time_milli
        self.ssml_props = ssml_props

    def __repr__(self):
        return "<Word(original_symbol='{}', symbol='{}', phone_sequence={}, start_byte_offset={}, end_byte_offset={}, start_time_milli={}, ssml_props={})>".format(
            self.original_symbol,
            self.symbol,
            self.phone_sequence,
            self.start_byte_offset,
            self.end_byte_offset,
            self.start_time_milli,
            self.ssml_props,
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Word) and (
            self.original_symbol == other.original_symbol
            and self.symbol == other.symbol
            and self.phone_sequence == other.phone_sequence
            and self.start_byte_offset == other.start_byte_offset
            and self.end_byte_offset == other.end_byte_offset
            and self.start_time_milli == other.start_time_milli
            # and self.ssml_props == other.ssml_props
        )

    def is_spoken(self):
        return self.original_symbol not in tokenizer.definitions.PUNCTUATION

    def is_from_ssml(self):
        return self.ssml_props != None

    def to_json(self):
        """Serialize Word to JSON."""
        return json.dumps(
            {
                "time": round(self.start_time_milli),
                "type": "word",
                "start": self.start_byte_offset,
                "end": self.end_byte_offset,
                "value": self.original_symbol,
            },
            ensure_ascii=False,
        )


# Use an empty initialized word as a sentence separator
WORD_SENTENCE_SEPARATOR = Word()


MAX_WORDS_PER_SEGMENT = 30


def preprocess_sentences(
    text_string: str,
    ssml_reqs: Dict,
    normalize_fn: Callable[[str], Iterable[Word]],
    translator_fn: Callable[[Iterable[Word]], Iterable[Word]],
) -> Iterable[Tuple[List[Word], PhoneSeq, List[int]]]:
    """Preprocess text into sentences of phonetized words

    Yields:
      A tuple (List[Word], PhoneSeq, List[int]) of the words in the segment, a flattened
        phoneme sequence of each segment and list of phoneme counts per word in the
        segment.

    """
    # TODO(rkjaran): The language code shouldn't be hardcoded here.
    words = list(translator_fn(normalize_fn(text_string, ssml_reqs), LangID("is-IS")))
    sentences: List[List[Word]] = [[]]
    for idx, word in enumerate(words):
        if word == WORD_SENTENCE_SEPARATOR:
            if idx != len(words) - 1:
                sentences.append([])
        else:
            sentences[-1].append(word)

    for sentence in sentences:
        for idx in range(0, len(sentence), MAX_WORDS_PER_SEGMENT):
            segment_words = sentence[idx : idx + MAX_WORDS_PER_SEGMENT]

            phone_counts: List[int] = []
            phone_seq = []

            for word in segment_words:
                phone_counts.append(len(word.phone_sequence))
                phone_seq.extend(word.phone_sequence)

            if not phone_seq:
                # If none of the words in this segment got a phone sequence we skip the
                # rest
                continue

            yield segment_words, phone_seq, phone_counts
