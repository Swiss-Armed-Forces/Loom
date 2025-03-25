# libretranslate

A libretranslate image that contains all models & does not need to download anything when running

## Why do we need this?

Some projects use libretranslate. Sadly, the libretranslate image on dockerhub does not container models.
If we build libretranslate from scratch, this will always download models. Which will start failing after
a few retries, since libretranslate does rate-limit the model download. That's why we keep this repo
which allows us to build the libretranslate container without downloading the models from the internet.

## Usage

*  To test that the dockerfile bulds correctly, in git-root (i.e. libretranslate/) run:
> docker build -f Dockerfile .
