# ImageIO FreeImage

[![CI](https://github.com/imageio/imageio-freeimage/actions/workflows/ci.yaml/badge.svg?branch=master)](https://github.com/imageio/imageio-freeimage/actions/workflows/ci.yaml)

> **Warning**
> 
> This repo is licensed under the *FreeImage Open Source Dual-License* and
> **not** the typical *BSD-2* license we use for everything else. Check out the
> LICENSE document in this repo and make sure you understand the consequences of
> it.

ImageIO FreeImage is a ImageIO plugin for the FreeImage library. In other words,
it allows using [FreeImage](https://freeimage.sourceforge.io/) with
[ImageIO](https://github.com/imageio/imageio).

## Installation

```
pip install imageio-freeimage
```

## Usage (and Examples)

To use it simply import the library. It will auto-register with ImageIO.

```python
import imageio.v3 as iio
import imageio_freeimage

img = iio.imread("imageio:chelsea.png", plugin="PNG-FI")
```

## Why ImageIO FreeImage

Based on discussions over at ImageIO's main repository, we have decided to spin
out the FreeImage plugin. This was done for two reasons

1. It is/was unclear how permissible the FreeImage license is, how exactly it
interacts with BSD (ImageIO's license), and what that means for downstream users
who don't need FreeImage. Instead of having to deal with the fallout of this
interaction, we decided to spin out the FreeImage plugin. This way, users don't
have to worry, unless they explicitly need FreeImage, in which case they will
likely be aware of how FreeImage is licensed, and what it means for their
project.

2. The FreeImage bindings we provide are based on ctypes. In many cases this is
not a problem; however, for some users it causes complications, because they,
for example, use pypy or other non-cpython interpreters or they want to complile
their python code in a browser via pyodide. Those use-cases are more prone to
problems when ctypes are involved and having them in a dedicated optional
dependency make this situation easier.

3. Having a dedicated repo for the FreeImage plugin will eventually allow us to
install the FreeImage library at install time, instead of having to ask users to
perform post-install steps to download the library. This might also have
positive implications on platform availability and introspection as we can
eventually compile FreeImage while building the package.
