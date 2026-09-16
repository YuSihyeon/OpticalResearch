from __future__ import annotations

from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
from PIL import Image
import torch
from torch import nn


RESNET18_WEIGHTS_URL = "https://download.pytorch.org/models/resnet18-f37072fd.pth"
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def conv3x3(in_planes: int, out_planes: int, stride: int = 1) -> nn.Conv2d:
    return nn.Conv2d(
        in_planes,
        out_planes,
        kernel_size=3,
        stride=stride,
        padding=1,
        bias=False,
    )


def conv1x1(in_planes: int, out_planes: int, stride: int = 1) -> nn.Conv2d:
    return nn.Conv2d(in_planes, out_planes, kernel_size=1, stride=stride, bias=False)


class BasicBlock(nn.Module):
    expansion = 1

    def __init__(self, inplanes: int, planes: int, stride: int = 1, downsample: nn.Module | None = None):
        super().__init__()
        self.conv1 = conv3x3(inplanes, planes, stride)
        self.bn1 = nn.BatchNorm2d(planes)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = conv3x3(planes, planes)
        self.bn2 = nn.BatchNorm2d(planes)
        self.downsample = downsample
        self.stride = stride

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        if self.downsample is not None:
            identity = self.downsample(x)
        out += identity
        return self.relu(out)


class ResNet18FeatureExtractor(nn.Module):
    def __init__(self, output_layer: str = "layer3"):
        super().__init__()
        if output_layer not in {"layer1", "layer2", "layer3", "layer4"}:
            raise ValueError("output_layer must be one of layer1, layer2, layer3, layer4")
        self.output_layer = output_layer
        self.inplanes = 64
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.layer1 = self._make_layer(64, 2)
        self.layer2 = self._make_layer(128, 2, stride=2)
        self.layer3 = self._make_layer(256, 2, stride=2)
        self.layer4 = self._make_layer(512, 2, stride=2)
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, 1000)

    def _make_layer(self, planes: int, blocks: int, stride: int = 1) -> nn.Sequential:
        downsample = None
        if stride != 1 or self.inplanes != planes:
            downsample = nn.Sequential(
                conv1x1(self.inplanes, planes, stride),
                nn.BatchNorm2d(planes),
            )
        layers = [BasicBlock(self.inplanes, planes, stride, downsample)]
        self.inplanes = planes
        for _ in range(1, blocks):
            layers.append(BasicBlock(self.inplanes, planes))
        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        if self.output_layer == "layer1":
            return x
        x = self.layer2(x)
        if self.output_layer == "layer2":
            return x
        x = self.layer3(x)
        if self.output_layer == "layer3":
            return x
        return self.layer4(x)


def ensure_resnet18_weights(weights_path: str | Path) -> Path:
    weights_path = Path(weights_path)
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    if not weights_path.exists():
        urlretrieve(RESNET18_WEIGHTS_URL, weights_path)
    return weights_path


def load_resnet18_feature_extractor(weights_path: str | Path, output_layer: str = "layer3") -> ResNet18FeatureExtractor:
    model = ResNet18FeatureExtractor(output_layer=output_layer)
    state = torch.load(Path(weights_path), map_location="cpu")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def image_to_tensor(image_path: str | Path, size: int) -> torch.Tensor:
    image = Image.open(image_path).convert("RGB").resize((size, size), Image.Resampling.BILINEAR)
    arr = np.asarray(image, dtype=np.float32) / 255.0
    arr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    chw = np.transpose(arr, (2, 0, 1))
    return torch.from_numpy(chw)


def extract_features(
    image_paths: list[Path],
    output_path: str | Path,
    weights_path: str | Path,
    image_size: int,
    batch_size: int = 8,
    output_layer: str = "layer3",
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model = load_resnet18_feature_extractor(weights_path, output_layer=output_layer)

    batches: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[start : start + batch_size]
            batch = torch.stack([image_to_tensor(path, image_size) for path in batch_paths], dim=0)
            feats = model(batch).cpu().numpy().astype(np.float32)
            batches.append(feats)

    features = np.concatenate(batches, axis=0)
    np.savez_compressed(
        output_path,
        features=features,
        image_names=np.array([path.name for path in image_paths]),
        image_size=np.array([image_size, image_size], dtype=np.int32),
        output_layer=np.array(output_layer),
    )
    return output_path
