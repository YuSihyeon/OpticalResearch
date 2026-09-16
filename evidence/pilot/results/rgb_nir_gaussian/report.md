# RGB-NIR Gaussian Cue Check Report

## Summary

This run shares 2D Gaussian geometry between RGB and NIR branches and visualizes where learned RGB and NIR reflectance disagree.

## Metrics

RGB-only MAE: 0.0349. Shared RGB MAE: 0.0342. Shared NIR MAE: 0.0362.

## Interpretation

Bright regions in the RGB/NIR difference heatmap are candidate material cues. They do not prove relighting, but they can guide material priors in a full inverse-rendering system.
