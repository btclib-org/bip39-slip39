# Copyright (c) The btclib developers
# Distributed under the MIT software license, see the accompanying
# LICENSE file or https://opensource.org/license/mit for the full text.

"""The texts `entropy.collect_rolls` shows, in each language of a word list.

Only what the user reads is here. What `collect_rolls` accepts as an
answer is in `entropy.py` and is the same for every language: the dice
sides it lists, ASCII decimal digits, and the ASCII letter `a` to
automate the rolls. A translation can confuse the user, but it cannot
change what is accepted, and so it cannot weaken the entropy collected.

A text in the wrong language, or with a wrong meaning, is a defect to
report, not a security matter. The placeholders are the same in every
language, and `tests/rolls_prompts_test.py` holds that to English's.
"""

from __future__ import annotations

from typing import NamedTuple

__all__ = ["ROLLS_PROMPTS", "RollsPrompts"]


class RollsPrompts(NamedTuple):
    """The texts of `collect_rolls`, as `str.format` templates.

    - `dice_sides` asks for the dice: `{choices}` is the list of sides.
    - `usable` says which rolls count: `{base}` is the highest.
    - `roll` asks for one roll: `{n}` of `{total}`.
    - `collected` reports the end: `{total}` rolls of `D{sides}` dice.
    """

    dice_sides: str
    usable: str
    roll: str
    collected: str


ROLLS_PROMPTS = {
    "cs": RollsPrompts(
        dice_sides=(
            "počet stěn kostky ({choices}; předpona 'a' zapne automatické hody, "
            "Enter znamená 'a6'): "
        ),
        usable="hody se použijí, jen pokud jsou v rozsahu 1..{base}",
        roll="hod #{n}/{total}: ",
        collected="shromážděno {total} použitelných hodů kostkou D{sides}",
    ),
    "en": RollsPrompts(
        dice_sides=(
            "dice sides ({choices}; prefix with 'a' to automate rolls, "
            "hit enter for 'a6'): "
        ),
        usable="rolls are used only if in 1..{base}",
        roll="roll #{n}/{total}: ",
        collected="collected {total} usable D{sides} rolls",
    ),
    "es": RollsPrompts(
        dice_sides=(
            "caras del dado ({choices}; antepón 'a' para automatizar las "
            "tiradas, pulsa Intro para 'a6'): "
        ),
        usable="las tiradas solo se usan si están en 1..{base}",
        roll="tirada #{n}/{total}: ",
        collected="se reunieron {total} tiradas D{sides} utilizables",
    ),
    "fr": RollsPrompts(
        dice_sides=(
            "faces du dé ({choices} ; préfixez par 'a' pour automatiser les "
            "lancers, appuyez sur Entrée pour 'a6') : "
        ),
        usable="les lancers ne sont utilisés que s'ils sont dans 1..{base}",
        roll="lancer #{n}/{total} : ",
        collected="{total} lancers D{sides} utilisables collectés",
    ),
    "it": RollsPrompts(
        dice_sides=(
            "facce del dado ({choices}; anteponi 'a' per automatizzare i "
            "lanci, premi Invio per 'a6'): "
        ),
        usable="i lanci sono usati solo se compresi in 1..{base}",
        roll="lancio #{n}/{total}: ",
        collected="raccolti {total} lanci D{sides} utilizzabili",
    ),
    "ja": RollsPrompts(
        dice_sides=(
            "サイコロの面の数 ({choices}; 先頭に 'a' を付けると自動で振ります。"
            "Enter で 'a6'): "
        ),
        usable="出目は 1..{base} の範囲内のときだけ使われます",
        roll="{n}/{total} 回目の出目: ",
        collected="使える D{sides} の出目を {total} 個集めました",
    ),
    "ko": RollsPrompts(
        dice_sides=(
            "주사위 면의 수 ({choices}; 자동으로 굴리려면 앞에 'a'를 붙이고, "
            "Enter를 누르면 'a6'): "
        ),
        usable="굴림은 1..{base} 범위 안일 때만 사용됩니다",
        roll="굴림 #{n}/{total}: ",
        collected="사용할 수 있는 D{sides} 굴림 {total}개를 모았습니다",
    ),
    "pt": RollsPrompts(
        dice_sides=(
            "faces do dado ({choices}; prefixe com 'a' para automatizar as "
            "jogadas, tecle Enter para 'a6'): "
        ),
        usable="as jogadas só são usadas se estiverem em 1..{base}",
        roll="jogada #{n}/{total}: ",
        collected="{total} jogadas D{sides} utilizáveis reunidas",
    ),
    "ru": RollsPrompts(
        dice_sides=(
            "число граней кубика ({choices}; добавьте в начале 'a', чтобы "
            "бросать автоматически, Enter означает 'a6'): "
        ),
        usable="броски используются, только если они в диапазоне 1..{base}",
        roll="бросок #{n}/{total}: ",
        collected="собрано {total} пригодных бросков D{sides}",
    ),
    "tr": RollsPrompts(
        dice_sides=(
            "zarın yüz sayısı ({choices}; atışları otomatikleştirmek için "
            "başına 'a' ekleyin, 'a6' için Enter'a basın): "
        ),
        usable="atışlar yalnızca 1..{base} aralığındaysa kullanılır",
        roll="atış #{n}/{total}: ",
        collected="{total} kullanılabilir D{sides} atışı toplandı",
    ),
    "zh": RollsPrompts(
        dice_sides=(
            "骰子面数 ({choices}；在前面加 'a' 可自动掷骰，直接按 Enter 表示 'a6'): "
        ),
        usable="只有在 1..{base} 范围内的掷骰结果才会被使用",
        roll="第 {n}/{total} 次掷骰: ",
        collected="已收集 {total} 个可用的 D{sides} 掷骰结果",
    ),
    "zh_tw": RollsPrompts(
        dice_sides=(
            "骰子面數 ({choices}；在前面加 'a' 可自動擲骰，直接按 Enter 表示 'a6'): "
        ),
        usable="只有在 1..{base} 範圍內的擲骰結果才會被使用",
        roll="第 {n}/{total} 次擲骰: ",
        collected="已收集 {total} 個可用的 D{sides} 擲骰結果",
    ),
}
