# Architecture

The package is layered bottom-up. `exceptions` and private `_utils`
underpin the other modules. `entropy` creates entropy from integers,
bytes, dice and the system CSPRNG; `mnemonic` loads word lists from
`_data/` and converts between words and indexes. `_rolls_prompts`
holds the dice prompts used by `entropy`.

`bip39` and `electrum` depend on `entropy` and `mnemonic`; `slip39`
depends on `mnemonic` only. The schemes do not import one another.
`dispatch` identifies a sentence's scheme, and `__main__` is the
`python -m btclib_mnemonics` entry point.
