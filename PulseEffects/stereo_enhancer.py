# -*- coding: utf-8 -*-

import logging
import os

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstInsertBin', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, GObject, Gst, GstInsertBin, Gtk

Gst.init(None)


class StereoEnhancer():

    def __init__(self):
        self.settings = None
        self.module_path = os.path.dirname(__file__)

        self.log = logging.getLogger('PulseEffects')
        self.use_workaround = False

        if Gst.ElementFactory.make(
                'calf-sourceforge-net-plugins-HaasEnhancer'):
            self.is_installed = True
        else:
            self.is_installed = False

            self.log.warn(
                'Stereo Enhancer plugin was not found. Disabling it!')

        self.build_bin()

    def on_filter_added(self, bin, element, success, user_data):
        pass

    def build_bin(self):
        self.input_gain = Gst.ElementFactory.make('volume', None)
        self.stereo_enhancer = Gst.ElementFactory.make(
            'calf-sourceforge-net-plugins-HaasEnhancer', None)

        self.input_level = Gst.ElementFactory.make('level', 'stereo_enhancer' +
                                                   '_input_level')
        self.out_level = Gst.ElementFactory.make('level', 'stereo_enhancer' +
                                                 '_output_level')

        self.bin = GstInsertBin.InsertBin.new('stereo_enhancer_bin')

        if self.is_installed:
            # booleans are inverted in GStreamer versions older than 1.12.5

            registry = Gst.Registry().get()
            self.use_workaround = not registry\
                .check_feature_version('pulsesrc', 1, 12, 5)

            if self.use_workaround:
                self.stereo_enhancer.set_property('bypass', True)
            else:
                self.stereo_enhancer.set_property('bypass', False)

            self.stereo_enhancer.set_property('level-in', 1.0)

            self.bin.append(self.input_gain, self.on_filter_added, None)
            self.bin.append(self.input_level, self.on_filter_added, None)
            self.bin.append(self.stereo_enhancer, self.on_filter_added, None)
            self.bin.append(self.out_level, self.on_filter_added, None)

    def post_messages(self, state):
        self.input_level.set_property('post-messages', state)
        self.out_level.set_property('post-messages', state)

    def init_ui(self):
        self.builder = Gtk.Builder.new_from_file(self.module_path +
                                                 '/ui/stereo_enhancer.glade')

        self.builder.connect_signals(self)

        self.ui_window = self.builder.get_object('window')
        self.ui_controls = self.builder.get_object('controls')
        self.ui_listbox_control = self.builder.get_object('listbox_control')

        self.ui_enable = self.builder.get_object('enable')
        self.ui_img_state = self.builder.get_object('img_state')

        self.ui_input_gain = self.builder.get_object('input_gain')
        self.ui_output_gain = self.builder.get_object('output_gain')

        self.ui_left_invert_phase = self.builder.get_object(
            'invert_left_phase')
        self.ui_left_balance = self.builder.get_object('left_balance')
        self.ui_left_delay = self.builder.get_object('left_delay')
        self.ui_left_gain = self.builder.get_object('left_gain')

        self.ui_right_invert_phase = self.builder.get_object(
            'invert_right_phase')
        self.ui_right_balance = self.builder.get_object('right_balance')
        self.ui_right_delay = self.builder.get_object('right_delay')
        self.ui_right_gain = self.builder.get_object('right_gain')

        self.ui_middle_invert_phase = self.builder.get_object(
            'invert_middle_phase')
        self.ui_middle_source = self.builder.get_object('middle_source')

        self.ui_side_gain = self.builder.get_object('side_gain')

        self.ui_input_level_left = self.builder.get_object('input_level_left')
        self.ui_input_level_right = self.builder.get_object(
            'input_level_right')
        self.ui_output_level_left = self.builder.get_object(
            'output_level_left')
        self.ui_output_level_right = self.builder.get_object(
            'output_level_right')

        self.ui_input_level_left_label = self.builder.get_object(
            'input_level_left_label')
        self.ui_input_level_right_label = self.builder.get_object(
            'input_level_right_label')
        self.ui_output_level_left_label = self.builder.get_object(
            'output_level_left_label')
        self.ui_output_level_right_label = self.builder.get_object(
            'output_level_right_label')

    def bind(self):
        # binding ui widgets to gsettings

        flag = Gio.SettingsBindFlags.DEFAULT

        self.settings.bind('state', self.ui_enable, 'active', flag)
        self.settings.bind('state', self.ui_img_state, 'visible', flag)
        self.settings.bind('state', self.ui_controls, 'sensitive',
                           Gio.SettingsBindFlags.GET)

        self.settings.bind('input-gain', self.ui_input_gain, 'value', flag)
        self.settings.bind('output-gain', self.ui_output_gain, 'value', flag)

        self.settings.bind('left-invert-phase', self.ui_left_invert_phase,
                           'active', flag)
        self.settings.bind('left-balance', self.ui_left_balance, 'value', flag)
        self.settings.bind('left-delay', self.ui_left_delay, 'value', flag)
        self.settings.bind('left-gain', self.ui_left_gain, 'value', flag)

        self.settings.bind('right-invert-phase', self.ui_right_invert_phase,
                           'active', flag)
        self.settings.bind('right-balance', self.ui_right_balance, 'value',
                           flag)
        self.settings.bind('right-delay', self.ui_right_delay, 'value', flag)
        self.settings.bind('right-gain', self.ui_right_gain, 'value', flag)

        self.settings.bind('middle-invert-phase', self.ui_middle_invert_phase,
                           'active', flag)
        self.settings.bind('middle-source', self.ui_middle_source, 'active',
                           flag)

        self.settings.bind('side-gain', self.ui_side_gain, 'value', flag)

        # binding ui widgets to gstreamer plugins

        flag = GObject.BindingFlags.BIDIRECTIONAL | \
            GObject.BindingFlags.SYNC_CREATE

        # There is a bug in gstreaner. Booleans are inverted. For example
        # we have to turn on bypass in order to effects to be applied

        boolean_flag = flag

        if self.use_workaround:
            boolean_flag = flag | GObject.BindingFlags.INVERT_BOOLEAN

        self.ui_left_invert_phase.bind_property('active', self.stereo_enhancer,
                                                's-phase1', boolean_flag)
        self.ui_left_balance.bind_property('value', self.stereo_enhancer,
                                           's-balance1', flag)
        self.ui_left_delay.bind_property('value', self.stereo_enhancer,
                                         's-delay1', flag)

        self.ui_right_invert_phase.bind_property('active',
                                                 self.stereo_enhancer,
                                                 's-phase2', boolean_flag)
        self.ui_right_balance.bind_property('value', self.stereo_enhancer,
                                            's-balance2', flag)
        self.ui_right_delay.bind_property('value', self.stereo_enhancer,
                                          's-delay2', flag)

        self.ui_middle_invert_phase.bind_property('active',
                                                  self.stereo_enhancer,
                                                  'm-phase', boolean_flag)
        self.ui_middle_source.bind_property('active', self.stereo_enhancer,
                                            'm-source', flag)

    def on_input_gain_value_changed(self, obj):
        value_db = obj.get_value()
        value_linear = 10**(value_db / 20.0)

        self.input_gain.set_property('volume', value_linear)

    def on_output_gain_value_changed(self, obj):
        value_db = obj.get_value()
        value_linear = 10**(value_db / 20.0)

        self.stereo_enhancer.set_property('level-out', value_linear)

    def on_left_gain_value_changed(self, obj):
        value_db = obj.get_value()
        value_linear = 10**(value_db / 20.0)

        self.stereo_enhancer.set_property('s-gain1', value_linear)

    def on_right_gain_value_changed(self, obj):
        value_db = obj.get_value()
        value_linear = 10**(value_db / 20.0)

        self.stereo_enhancer.set_property('s-gain2', value_linear)

    def on_side_gain_value_changed(self, obj):
        value_db = obj.get_value()
        value_linear = 10**(value_db / 20.0)

        self.stereo_enhancer.set_property('s-gain', value_linear)

    def ui_update_level(self, widgets, peak):
        left, right = peak[0], peak[1]

        widget_level_left = widgets[0]
        widget_level_right = widgets[1]
        widget_level_left_label = widgets[2]
        widget_level_right_label = widgets[3]

        if left >= -99:
            l_value = 10**(left / 10)
            widget_level_left.set_value(l_value)
            widget_level_left_label.set_text(str(round(left)))
        else:
            widget_level_left.set_value(0)
            widget_level_left_label.set_text('-99')

        if right >= -99:
            r_value = 10**(right / 10)
            widget_level_right.set_value(r_value)
            widget_level_right_label.set_text(str(round(right)))
        else:
            widget_level_right.set_value(0)
            widget_level_right_label.set_text('-99')

    def ui_update_input_level(self, peak):
        widgets = [self.ui_input_level_left, self.ui_input_level_right,
                   self.ui_input_level_left_label,
                   self.ui_input_level_right_label]

        self.ui_update_level(widgets, peak)

    def ui_update_output_level(self, peak):
        widgets = [self.ui_output_level_left, self.ui_output_level_right,
                   self.ui_output_level_left_label,
                   self.ui_output_level_right_label]

        self.ui_update_level(widgets, peak)

    def reset(self):
        self.settings.reset('state')
        self.settings.reset('input-gain')
        self.settings.reset('output-gain')
        self.settings.reset('left-invert-phase')
        self.settings.reset('left-balance')
        self.settings.reset('left-delay')
        self.settings.reset('left-gain')
        self.settings.reset('right-invert-phase')
        self.settings.reset('right-balance')
        self.settings.reset('right-delay')
        self.settings.reset('right-gain')
        self.settings.reset('middle-invert-phase')
        self.settings.reset('middle-source')
        self.settings.reset('side-gain')
