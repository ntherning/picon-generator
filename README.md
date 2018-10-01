# Enigma2 Picon Generator

This script depends on the Imagemagick `convert` command being in your `PATH`
and it must be capable of handling SVG files. On macOS get it using homebrew:

```
brew install imagemagick
```

## Typical usage

This assumes that the root filesystem of the Enigma2 box has been mounted at
`/Volumes/Root/` which happens to be the case with my Zgemma H7 on my Macbook.

```
mkdir picons
cd picons/
git clone https://gitlab.com/picons/picons.git
git clone https://github.com/ntherning/picon-generator.git
mkdir -p /Volumes/Root/media/hdd/XPicons/picon
./picon-generator/picon-generator.py \
    -s 220x136 \
    -l /Volumes/Root/etc/enigma2/lamedb \
    -i ./picons/build-source/logos/ \
    -d /Volumes/Root/media/hdd/XPicons/picon/ \
    -m ./custom_mappings.txt
```
To generate the smaller set of picons for the Metrix skin used by my Zgemma I use this command line:

```
./picon-generator/picon-generator.py \
    -s 100x60 \
    -l /Volumes/Root/etc/enigma2/lamedb \
    -i ./picons/build-source/logos/ \
    -d /Volumes/Root/media/hdd/picon/ \
    -m ./custom_mappings.txt
```

## Custom mappings file format

Some networks use the same channel names so the script might pick the wrong
logo file for a particular channel. Or you might want to ignore some channels
entirely. The custom mappings file let's you do this. Here's an example:

```
Discovery HD Showcase=discoveryshowcasehd.light.png
Humax 1000 C=ignored
Humax 6000 C=ignored
Kanal 11=kanal11-cricroclot.default.svg
Kanal 11 HD=kanal11-cricroclot.default.svg
Rai Radio=ignored
YLE1 HD=ignored
YLE2 HD=ignored
```
