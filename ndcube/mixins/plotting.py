import numpy as np
import matplotlib.pyplot as plt

import astropy.units as u
from sunpy.visualization.imageanimator import ImageAnimatorWCS, LineAnimator
import sunpy.visualization.wcsaxes_compat as wcsaxes_compat

__all__ = ['NDCubePlotMixin']


class NDCubePlotMixin:
    """
    Add plotting functionality to a NDCube class.
    """

    def plot(self, axes=None, image_axes=None, unit_x_axis=None, unit_y_axis=None,
             axis_ranges=None, unit=None, **kwargs):
        """
        Plots an interactive visualization of this cube with a slider
        controlling the wavelength axis for data having dimensions greater than 2.
        Plots an x-y graph onto the current axes for 2D or 1D data.
        Keyword arguments are passed on to matplotlib.
        Parameters other than data and wcs are passed to ImageAnimatorWCS,
        which in turn passes them to imshow for data greater than 2D.

        Parameters
        ----------
        image_axes: `list`
            The two axes that make the image.
            Like [-1,-2] this implies cube instance -1 dimension
            will be x-axis and -2 dimension will be y-axis.

        axes: `astropy.visualization.wcsaxes.core.WCSAxes` or None:
            The axes to plot onto. If None the current axes will be used.

        unit_x_axis: `astropy.units.Unit`
            The unit of x axis for 2D plots.

        unit_y_axis: `astropy.units.Unit`
            The unit of y axis for 2D plots.

        unit: `astropy.unit.Unit`
            The data is changed to the unit given or the cube.unit if not given, for 1D plots.

        axis_ranges: list of physical coordinates for array or None
            If None array indices will be used for all axes.
            If a list it should contain one element for each axis of the numpy array.
            For the image axes a [min, max] pair should be specified which will be
            passed to :func:`matplotlib.pyplot.imshow` as extent.
            For the slider axes a [min, max] pair can be specified or an array the
            same length as the axis which will provide all values for that slider.
            If None is specified for an axis then the array indices will be used
            for that axis.

        """
        if not image_axes:
            image_axes = [-1, -2]
        try:
            plot_axis_index = int(image_axes)
        except TypeError:
            if len(image_axes) == 1:
                plot_axis_index = int(image_axes[0])
            else:
                plot_axis_index = None
        if isinstance(plot_axis_index, int) and self.data.ndim > 1:
            plot = self._animate_cube_1D(plot_axis_index=plot_axis_index,
                                         unit_x_axis=unit_x_axis, unit_y_axis=unit_y_axis,
                                         **kwargs)
        else:
            axis_data = ['x', 'x']
            axis_data[image_axes[1]] = 'y'
            if self.data.ndim >= 3:
                plot = self._plot_3D_cube(image_axes=image_axes, unit_x_axis=unit_x_axis,
                                          unit_y_axis=unit_y_axis, axis_ranges=axis_ranges,
                                          **kwargs)
            elif self.data.ndim == 2:
                plot = self._plot_2D_cube(axes=axes, image_axes=axis_data[::-1], **kwargs)

            elif self.data.ndim == 1:
                plot = self._plot_1D_cube(unit_x_axis=unit_x_axis, unit_y_axis=unit_y_axis, **kwargs)

        return plot

    def _plot_3D_cube(self, image_axes=None, unit_x_axis=None, unit_y_axis=None,
                      axis_ranges=None, **kwargs):
        """
        Plots an interactive visualization of this cube using sliders to move through axes
        plot using in the image.
        Parameters other than data and wcs are passed to ImageAnimatorWCS, which in turn
        passes them to imshow.

        Parameters
        ----------
        image_axes: `list`
            The two axes that make the image.
            Like [-1,-2] this implies cube instance -1 dimension
            will be x-axis and -2 dimension will be y-axis.

        unit_x_axis: `astropy.units.Unit`
            The unit of x axis.

        unit_y_axis: `astropy.units.Unit`
            The unit of y axis.

        axis_ranges: `list` of physical coordinates for array or None
            If None array indices will be used for all axes.
            If a list it should contain one element for each axis of the numpy array.
            For the image axes a [min, max] pair should be specified which will be
            passed to :func:`matplotlib.pyplot.imshow` as extent.
            For the slider axes a [min, max] pair can be specified or an array the
            same length as the axis which will provide all values for that slider.
            If None is specified for an axis then the array indices will be used
            for that axis.

        """
        if not image_axes:
            image_axes = [-1, -2]
        i = ImageAnimatorWCS(self.data, wcs=self.wcs, image_axes=image_axes,
                             unit_x_axis=unit_x_axis, unit_y_axis=unit_y_axis,
                             axis_ranges=axis_ranges, **kwargs)
        return i

    def _plot_2D_cube(self, axes=None, image_axes=None, **kwargs):
        """
        Plots a 2D image onto the current
        axes. Keyword arguments are passed on to matplotlib.

        Parameters
        ----------
        axes: `astropy.visualization.wcsaxes.core.WCSAxes` or `None`:
            The axes to plot onto. If None the current axes will be used.

        image_axes: `list`.
            The first axis in WCS object will become the first axis of image_axes and
            second axis in WCS object will become the second axis of image_axes.
            Default: ['x', 'y']

        """
        if not image_axes:
            image_axes = ['x', 'y']
        if axes is None:
            if self.wcs.naxis is not 2:
                missing_axis = self.missing_axis
                slice_list = []
                index = 0
                for i, bool_ in enumerate(missing_axis):
                    if not bool_:
                        slice_list.append(image_axes[index])
                        index += 1
                    else:
                        slice_list.append(1)
                if index is not 2:
                    raise ValueError("Dimensions of WCS and data don't match")
            axes = wcsaxes_compat.gca_wcs(self.wcs, slices=slice_list)
        plot = axes.imshow(self.data, **kwargs)
        return plot

    def _plot_1D_cube(self, unit_x_axis=None, unit_y_axis=None, **kwargs):
        """
        Plots a graph.
        Keyword arguments are passed on to matplotlib.

        Parameters
        ----------
        unit: `astropy.unit.Unit`
            The data is changed to the unit given or the cube.unit if not given.

        """
        index_not_one = []
        for i, _bool in enumerate(self.missing_axis):
            if not _bool:
                index_not_one.append(i)
        xdata = self.pixel_to_world(u.Quantity(np.arange(self.data.shape[0]), unit=u.pix))[0]
        if unit_x_axis is not None:
            xdata = xdata.to(unit_x_axis)
        if unit_y_axis is None:
            ydata = self.data
            unit_y_axis = self.unit
        else:
            if self.unit is None:
                raise TypeError("NDCube.unit is None.  Must be an astropy.units.unit or "
                                "valid unit string in order to set unit_y_axis.")
            else:
                ydata = (self.data * self.unit).to(unit_y_axis)
        plot = plt.plot(xdata, ydata,
                        xlabel="{0} [{1}]".format(self.world_axis_physical_types[0], unit_x_axis),
                        ylabel="Data [{0}]".format(unit_y_axis), **kwargs)
        return plot

    def _animate_cube_1D(self, plot_axis_index=-1, unit_x_axis=None, unit_y_axis=None, **kwargs):
        """Animates an axis of a cube as a line plot with sliders for other axes."""
        # Get real world axis values along axis to be plotted and enter into axes_ranges kwarg.
        xdata = self.axis_world_coords(plot_axis_index)
        # Change x data to desired units it set by user.
        if unit_x_axis:
            xdata = xdata.to(unit_x_axis)
        axis_ranges = [None] * self.data.ndim
        axis_ranges[plot_axis_index] = xdata.value
        if unit_y_axis:
            if self.unit is None:
                raise TypeError("NDCube.unit is None.  Must be an astropy.units.unit or "
                                "valid unit string in order to set unit_y_axis.")
            else:
                data = (self.data * self.unit).to(unit_y_axis)
        # Initiate line animator object.
        plot = LineAnimator(data.value, plot_axis_index=plot_axis_index, axis_ranges=axis_ranges,
                            xlabel="{0} [{1}]".format(
                                self.world_axis_physical_types[plot_axis_index], unit_x_axis),
                            ylabel="Data [{0}]".format(unit_y_axis), **kwargs)
        return plot
