import numpy as np

from view_to_gaussian_poc.src.aggregation import (
    aggregate_observations,
    leave_one_out_scores,
)
from view_to_gaussian_poc.src.geometry import Camera, project_points
from view_to_gaussian_poc.src.sampling import bilinear_sample_chw


def test_project_points_places_points_in_pixel_coordinates():
    camera = Camera(
        width=100,
        height=80,
        focal=50.0,
        c2w=np.eye(4, dtype=np.float64),
    )
    points = np.array(
        [
            [0.0, 0.0, -2.0],
            [0.2, -0.2, -2.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )

    uv, depth, valid = project_points(points, camera)

    np.testing.assert_allclose(uv[0], [50.0, 40.0], atol=1e-6)
    np.testing.assert_allclose(uv[1], [55.0, 45.0], atol=1e-6)
    assert depth[0] > 0.0
    assert valid.tolist() == [True, True, False]


def test_bilinear_sample_chw_interpolates_features():
    feature_map = np.array(
        [
            [[0.0, 2.0], [4.0, 6.0]],
            [[10.0, 14.0], [18.0, 22.0]],
        ],
        dtype=np.float32,
    )
    coords = np.array([[0.5, 0.5], [1.0, 0.0]], dtype=np.float32)

    sampled = bilinear_sample_chw(feature_map, coords)

    np.testing.assert_allclose(sampled[0], [3.0, 16.0], atol=1e-6)
    np.testing.assert_allclose(sampled[1], [2.0, 14.0], atol=1e-6)


def test_aggregate_observations_supports_mean_and_weights():
    observations = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 1.0],
        ],
        dtype=np.float32,
    )

    mean = aggregate_observations(observations)
    weighted = aggregate_observations(observations, weights=np.array([1.0, 1.0, 2.0]))

    np.testing.assert_allclose(mean, [2.0 / 3.0, 2.0 / 3.0], atol=1e-6)
    np.testing.assert_allclose(weighted, [0.75, 0.75], atol=1e-6)


def test_leave_one_out_scores_prefers_multi_view_when_noise_averages_out():
    observations_by_point = {
        0: np.array(
            [
                [1.0, 0.0],
                [0.8, 0.2],
                [1.0, -0.1],
            ],
            dtype=np.float32,
        )
    }

    scores = leave_one_out_scores(observations_by_point)

    assert len(scores) == 3
    assert np.mean([row["multi_cosine"] for row in scores]) > np.mean(
        [row["single_cosine"] for row in scores]
    )
