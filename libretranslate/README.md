# LibreTranslate

A LibreTranslate image that contains all models & does not need to download anything when running.

## Why do we need this?

The LibreTranslate image on dockerhub does not container models. If we build LibreTranslate from scratch,
this will always download models. Which will start failing after a few retries, since LibreTranslate does
rate-limit the model download. That's why we keep this repo which allows us to build the LibreTranslate
container without downloading the models from the internet.
