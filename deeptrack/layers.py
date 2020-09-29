""" Standardized layers implemented in keras.
"""

import tensorflow
from tensorflow.keras import layers, activations
from tensorflow.keras.initializers import RandomNormal
from tensorflow_addons.layers import InstanceNormalization


def as_block(x):
    """Converts input to layer block"""
    if isinstance(x, str):
        if x in _string_to_block:
            return _string_to_block[x]
        else:
            raise ValueError(
                "Invalid blockname {0}, valid names are: ".format(x)
                + ", ".join(_string_to_block.keys())
            )
    if isinstance(x, layers.Layer) or not callable(x):
        raise TypeError("Layer block should be a function that returns a keras Layer.")
    else:
        return x


def _as_activation(x):
    if x is None:
        return layers.Layer()
    if isinstance(x, layers.Layer):
        return x
    else:
        return layers.Activation(x)


def _single_layer_call(x, layer, instance_norm, activation):
    y = layer(x)
    if instance_norm:
        if not isinstance(instance_norm, dict):
            instance_norm = {}

        y = InstanceNormalization(**instance_norm)(y)
    y = _as_activation(activation)(y)
    return y


def _instance_norm(x, filters):
    return x or (callable(x) and x(filters))


def ConvolutionalBlock(
    kernel_size=3,
    activation="relu",
    padding="same",
    strides=1,
    instance_norm=False,
    **kwargs
):
    """A single 2d convolutional layer.

    Accepts arguments of keras.layers.Conv2D.

    Parameters
    ----------
    kernel_size : int
        Size of the convolution kernel
    activation : str or activation function or layer
        Activation function of the layer. See keras docs for accepted strings.
    padding : str
        How to pad the input tensor. See keras docs for accepted strings.
    strides : int
        Step length of kernel
    instance_norm : bool
        Whether to add instance normalization (before activation).
    **kwargs
        Other keras.layers.Conv2D arguments
    """

    def Layer(filters, **kwargs_inner):
        kwargs_inner.update(kwargs)
        layer = layers.Conv2D(
            filters,
            kernel_size=kernel_size,
            padding=padding,
            strides=strides,
            **kwargs_inner
        )
        return lambda x: _single_layer_call(x, layer, instance_norm, activation)

    return Layer


def DenseBlock(activation="tanh", instance_norm=False, **kwargs):
    """A single dense layer.

    Accepts arguments of keras.layers.Dense.

    Parameters
    ----------
    activation : str or activation function or layer
        Activation function of the layer. See keras docs for accepted strings.
    instance_norm : bool
        Whether to add instance normalization (before activation).
    **kwargs
        Other keras.layers.Dense arguments
    """

    def Layer(filters, **kwargs_inner):
        kwargs_inner.update(kwargs)
        layer = layers.Dense(filters, **kwargs_inner)
        return lambda x: _single_layer_call(x, layer, instance_norm, activation)

    return Layer


def PoolingBlock(
    pool_size=(2, 2),
    activation=None,
    padding="same",
    strides=1,
    instance_norm=False,
    **kwargs
):
    """A single max pooling layer.

    Accepts arguments of keras.layers.MaxPool2D.

    Parameters
    ----------
    pool_size : int
        Size of the pooling kernel
    activation : str or activation function or layer
        Activation function of the layer. See keras docs for accepted strings.
    padding : str
        How to pad the input tensor. See keras docs for accepted strings.
    strides : int
        Step length of kernel
    instance_norm : bool
        Whether to add instance normalization (before activation).
    **kwargs
        Other keras.layers.MaxPool2D arguments
    """

    def Layer(filters=None, **kwargs_inner):
        kwargs_inner.update(kwargs)
        layer = layers.MaxPool2D(
            pool_size=pool_size, padding=padding, strides=strides, **kwargs_inner
        )
        return lambda x: _single_layer_call(x, layer, instance_norm, activation)

    return Layer


def DeconvolutionalBlock(
    kernel_size=(2, 2),
    activation=None,
    padding="same",
    strides=1,
    instance_norm=False,
    **kwargs
):
    """A single 2d deconvolutional layer.

    Accepts arguments of keras.layers.Conv2DTranspose.

    Parameters
    ----------
    kernel_size : int
        Size of the kernel
    activation : str or activation function or layer
        Activation function of the layer. See keras docs for accepted strings.
    padding : str
        How to pad the input tensor. See keras docs for accepted strings.
    strides : int
        Step length of kernel
    instance_norm : bool
        Whether to add instance normalization (before activation).
    **kwargs
        Other keras.layers.Conv2DTranspose arguments
    """

    def Layer(filters, **kwargs_inner):
        kwargs_inner.update(kwargs)
        layer = layers.Conv2DTranspose(
            filters,
            kernel_size=kernel_size,
            padding=padding,
            strides=strides,
            **kwargs_inner
        )
        return lambda x: _single_layer_call(x, layer, instance_norm, activation)

    return Layer


def StaticUpsampleBlock(
    size=(2, 2),
    activation=None,
    interpolation="bilinear",
    instance_norm=False,
    **kwargs
):
    """A single no-trainable 2d deconvolutional layer.

    Accepts arguments of keras.layers.UpSampling2D.

    Parameters
    ----------
    size : int
        Size of the kernel
    activation : str or activation function or layer
        Activation function of the layer. See keras docs for accepted strings.
    interpolation
        Interpolation type. Either "bilinear" or "nearest".
    instance_norm : bool
        Whether to add instance normalization (before activation).
    **kwargs
        Other keras.layers.Conv2DTranspose arguments
    """

    def Layer(filters=None, **kwargs_inner):
        kwargs_inner.update(kwargs)
        layer = layers.UpSampling2D(
            size=size, interpolation=interpolation, **kwargs_inner
        )
        return lambda x: _single_layer_call(x, layer, instance_norm, activation)

    return Layer


def ResidualBlock(
    kernel_size=(3, 3), activation="relu", strides=1, instance_norm=True, **kwargs
):
    """A 2d residual layer with two convolutional steps.

    Accepts arguments of keras.layers.Conv2D.

    Parameters
    ----------
    kernel_size : int
        Size of the kernel
    activation : str or activation function or layer
        Activation function of the layer. See keras docs for accepted strings.
    strides : int
        Step length of kernel
    instance_norm : bool
        Whether to add instance normalization (before activation).
    **kwargs
        Other keras.layers.Conv2D arguments
    """

    def Layer(filters, **kwargs_inner):
        kwargs_inner.update(kwargs)
        identity = layers.Conv2D(filters, kernel_size=(1, 1))

        conv = layers.Conv2D(
            filters,
            kernel_size=kernel_size,
            strides=strides,
            padding="same",
        )

        conv2 = layers.Conv2D(
            filters, kernel_size=kernel_size, strides=1, padding="same"
        )

        def call(x):
            y = _single_layer_call(x, conv, instance_norm, activation)
            y = _single_layer_call(y, conv2, instance_norm, activation)
            y = layers.Add()([identity(x), y])
            return y

        return call

    return Layer


def Identity(activation=None, instance_norm=False, **kwargs):
    """Identity layer that returns the input tensor.

    Can optionally perform instance normalization or some activation function.

    Accepts arguments of keras.layers.Layer.

    Parameters
    ----------

    activation : str or activation function or layer
        Activation function of the layer. See keras docs for accepted strings.
    instance_norm : bool
        Whether to add instance normalization (before activation).
    **kwargs
        Other keras.layers.Layer arguments
    """

    def Layer(filters, **kwargs_inner):
        layer = layers.Layer(**kwargs_inner)
        return lambda x: _single_layer_call(x, layer, instance_norm, activation)

    return Layer


_string_to_block = {
    "conv": ConvolutionalBlock(),
    "convolutional": ConvolutionalBlock(),
    "dense": DenseBlock(),
    "pool": PoolingBlock(),
    "pooling": PoolingBlock(),
    "upsample": DeconvolutionalBlock(),
    "deconv": DeconvolutionalBlock(),
    "deconvolutional": DeconvolutionalBlock(),
    "none": Identity(),
    "identity": Identity(),
}