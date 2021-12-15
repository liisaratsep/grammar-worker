# Grammatical error correction models

Models can be attached to the main [grammar-worker](https://github.com/tartunlp/grammar-worker) container by
mounting a volume at `/app/models/`. Official grammar models can be downloaded from the 
[releases](https://github.com/tartunlp/grammar-worker/releases) section of this repository. Due to GitHub's 
file size limitations, these may be uploaded as multipart zip files which have to unpacked first.

Alternatively, models are built into the [`grammar-model`](https://ghcr.io/tartunlp/grammar-model) images 
published alongside this repository. These are `busybox` images that simply contain all model files in the 
`/models/` directory. They can be used as init containers to populate the `/app/models/` volume of the 
[`grammar-worker`](https://ghcr.io/tartunlp/grammar-worker) instance. 

Each model is published as a separate image and corresponds to a specific release. Compatibility between 
[`grammar-worker`](https://ghcr.io/tartunlp/grammar-worker) and 
[`grammar-model`](https://ghcr.io/tartunlp/grammar-model) versions will be specified in the release notes.

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

The included Dockerfile can be used to publish new model versions. The build-time argument `MODEL_DIR` can be used to
specify a subdirectory to be copied to `/models/` instead of the current directory.

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