#! /usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

r"""
Abstract base module for all BoTorch models.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from torch import Tensor
from torch.nn import Module

from ..posteriors import Posterior
from ..sampling.samplers import MCSampler


class Model(Module, ABC):
    r"""Abstract base class for BoTorch models."""

    @abstractmethod
    def posterior(
        self,
        X: Tensor,
        output_indices: Optional[List[int]] = None,
        observation_noise: bool = False,
        **kwargs: Any,
    ) -> Posterior:
        r"""Computes the posterior over model outputs at the provided points.

        Args:
            X: A `b x q x d`-dim Tensor, where `d` is the dimension of the
                feature space, `q` is the number of points considered jointly,
                and `b` is the batch dimension.
            output_indices: A list of indices, corresponding to the outputs over
                which to compute the posterior (if the model is multi-output).
                Can be used to speed up computation if only a subset of the
                model's outputs are required for optimization. If omitted,
                computes the posterior over all model outputs.
            observation_noise: If True, add observation noise to the posterior.

        Returns:
            A `Posterior` object, representing a batch of `b` joint distributions
            over `q` points and `o` outputs each.
        """
        pass  # pragma: no cover

    def condition_on_observations(self, X: Tensor, Y: Tensor, **kwargs: Any) -> "Model":
        r"""Condition the model on new observations.

        Args:
            X: A `batch_shape x m x d`-dim Tensor, where `d` is the dimension of
                the feature space, `m` is the number of points per batch, and
                `batch_shape` is the batch shape (must be compatible with the
                batch shape of the model).
            Y: A `batch_shape' x m x (o)`-dim Tensor, where `o` is the number of
                model outputs, `m` is the number of points per batch, and
                `batch_shape'` is the batch shape of the observations.
                `batch_shape'` must be broadcastable to `batch_shape` using
                standard broadcasting semantics. If `Y` has fewer batch dimensions
                than `X`, it is assumed that the missing batch dimensions are
                the same for all `Y`.

        Returns:
            A `Model` object of the same type, representing the original model
            conditioned on the new observations `(X, Y)` (and possibly noise
            observations passed in via kwargs).
        """
        raise NotImplementedError

    def fantasize(
        self,
        X: Tensor,
        sampler: MCSampler,
        observation_noise: bool = True,
        **kwargs: Any,
    ) -> "Model":
        r"""Construct a fantasy model.

        Constructs a fantasy model in the following fashion:
        (1) compute the model posterior at `X` (including observation noise if
        `observation_noise=True`).
        (2) sample from this posterior (using `sampler`) to generate "fake"
        observations.
        (3) condition the model on the new fake observations.

        Args:
            X: A `batch_shape x m x d`-dim Tensor, where `d` is the dimension of
                the feature space, `m` is the number of points per batch, and
                `batch_shape` is the batch shape (must be compatible with the
                batch shape of the model).
            sampler: The sampler used for sampling from the posterior at `X`.
            observation_noise: If True, include observation noise.

        Returns:
            The constructed fantasy model.
        """
        post_X = self.posterior(X, observation_noise=observation_noise, **kwargs)
        Y_fantasized = sampler(post_X)  # num_fantasies x batch_shape x m x o
        return self.condition_on_observations(X=X, Y=Y_fantasized, **kwargs)
