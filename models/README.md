# Grammatical error correction models

Models are either built into the image or can be attached to the
main [grammar-worker](https://github.com/tartunlp/grammar-worker) container by mounting a volume at `/app/models/`.

## Model configuration

By default, the `grammar-worker` looks for a `config.yaml` file on the `/app/models` volume (the `models/` directory
of the repository). This file should contain the following keys:

- `language` - ISO language code
- `checkpoint` - path of the model checkpoint file (usually named `checkpoint_best.pt`)
- `dict_dir` - the directory path that contains the model dictionary files (name pattern: `dict.{lang}.txt`)
- `sentencepiece_dir` - the directory that contains sentencepiece models
- `sentencepiece_prefix` - the prefix used on all sentencepiece model files
- `source_language` - input langauge code (as understood by the model)
- `target_language` - output langauge code (as understood by the model)

### Configuration samples

Sample configuration for a general domain Estonian-English single direction model:

```
language: et
checkpoint: models/checkpoint_best.pt
dict_dir: models/dicts/
sentencepiece_dir: models/sentencepiece/
sentencepiece_prefix: sp-model
source_language: et0
target_language: et1
```

The configuration above matches the following folder structure:

```
models/
├── checkpoint_best.pt
├── config.yaml
├── dicts
│   ├── dict.et0.txt
│   └── dict.et1.txt
└── sentencepiece
    ├── sp-model.et0.model
    ├── sp-model.et0.vocab
    ├── sp-model.et0.model
    └── sp-model.et1.vocab
```