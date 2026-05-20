from transformers import AutoTokenizer

# Compara como tokenizadores diferentes quebram o mesmo texto.
# Util para entender por que o mesmo prompt custa numeros distintos de tokens
# dependendo do modelo (e portanto, do tokenizer) que voce usa.
TOKENIZERS = [
    "gpt2",  # BPE classico — referencia historica
    "bert-base-uncased",  # WordPiece, lowercased
    "Xenova/gpt-4o",  # tiktoken o200k_base portado para HF (mesmo do GPT-4o)
]

TEXT = "Hello world! Bem-vindo ao estudo de tokenizadores. 🤗"


def main() -> None:
    print(f"Texto: {TEXT!r}\n")

    for name in TOKENIZERS:
        tokenizer = AutoTokenizer.from_pretrained(name)
        ids = tokenizer.encode(TEXT)
        pieces = tokenizer.convert_ids_to_tokens(ids)
        decoded = tokenizer.decode(ids)

        print(f"=== {name} ===")
        print(f"  n_tokens: {len(ids)}")
        print(f"  pieces:   {pieces}")
        print(f"  ids:      {ids}")
        print(f"  decoded:  {decoded!r}\n")


if __name__ == "__main__":
    main()
