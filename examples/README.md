# Image decomposition examples

![Computed synthetic examples](../figures/example_gallery.svg)

The gallery above is computed from three original deterministic test patterns using exact CDF 5/3 coefficients. They isolate edges, textures and checkerboard high-frequency content. Gray shows intensities; red/blue shows positive/negative detail coefficients. Detail contrast is enhanced for visibility, not a quantitative energy scale.

For natural image examples, install scikit-image and use its documented benchmark images:

```bash
pip install scikit-image
python python/gallery.py --natural
```

The script evaluates Camera, Astronaut and Chelsea (cat), plus the synthetic examples. Depending on the scikit-image installation, its own data loader may download assets. See https://scikit-image.org/docs/stable/api/skimage.data.html for dataset provenance and licensing. Photographs remain third-party material; they are not attributed to the project author.

To use a locally obtained Lena image or any other image you have permission to use:

```bash
python python/gallery.py --image /path/to/lena.png
make test H=32 W=32 TILE=4 IMAGE=/path/to/lena.png
```

Lena is not redistributed here. It is unsuitable for IEEE submissions under IEEE's Lena image policy. Use the natural alternatives for new publications.

For every image the gallery computes LL/LH/HL/HH with a shared signed detail scale, a three-level pyramid, reconstruction, absolute error and six-method coefficient agreement. The optional hardware vector generator resizes a selected image to H×W, converts it to grayscale and compares all six RTL schedules to the Q6 oracle when a simulator is run. MATLAB supports local images via its existing demo.
