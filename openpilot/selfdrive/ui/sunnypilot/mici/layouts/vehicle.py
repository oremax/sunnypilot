"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import json
import os

from openpilot.common.basedir import BASEDIR
from openpilot.selfdrive.ui.mici.widgets.button import BigButton
from openpilot.selfdrive.ui.mici.widgets.dialog import BigDialog
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.lib.multilang import tr
from openpilot.system.ui.widgets.label import UnifiedLabel
from openpilot.system.ui.widgets.scroller import NavScroller

CAR_LIST_JSON_OUT = os.path.join(BASEDIR, "openpilot", "sunnypilot", "selfdrive", "car", "car_list.json")


def _load_platforms():
  with open(CAR_LIST_JSON_OUT) as car_list_json:
    return json.load(car_list_json)


class VehicleLayoutMici(NavScroller):
  def __init__(self):
    super().__init__()
    self._platforms = _load_platforms()

    self._current_btn = BigButton(tr("vehicle"), "")
    self._current_btn.set_click_callback(self._open_make_list)

    self._auto_btn = BigButton(tr("automatic fingerprint"), "")
    self._auto_btn.set_click_callback(self._clear_selection)

    self._hint = UnifiedLabel(tr("Select vehicle to force fingerprint manually."), 32, max_width=640)

    self._scroller.add_widgets([self._current_btn, self._auto_btn, self._hint])
    self._refresh()

  def _refresh(self):
    if bundle := ui_state.params.get("CarPlatformBundle"):
      self._current_btn.set_value(bundle.get("name", ""))
      self._auto_btn.set_visible(True)
    elif ui_state.CP is not None and ui_state.CP.carFingerprint != "MOCK":
      self._current_btn.set_value(ui_state.CP.carFingerprint)
      self._auto_btn.set_visible(False)
    else:
      self._current_btn.set_value(tr("unrecognized"))
      self._auto_btn.set_visible(False)

  def _update_state(self):
    super()._update_state()
    self._refresh()

  def _clear_selection(self):
    ui_state.params.remove("CarPlatformBundle")
    self._refresh()

  def _open_make_list(self):
    gui_app.push_widget(VehicleMakeListMici(self._platforms, self._on_selected))

  def _on_selected(self, name):
    if data := self._platforms.get(name):
      ui_state.params.put("CarPlatformBundle", {**data, "name": name})
    self._refresh()
    msg = tr("This setting will take effect immediately.") if ui_state.is_offroad() else \
      tr("This setting will take effect once the device enters offroad state.")
    gui_app.push_widget(BigDialog(tr("vehicle selected"), msg))


class VehicleMakeListMici(NavScroller):
  def __init__(self, platforms, on_selected):
    super().__init__()
    self._platforms = platforms
    self._on_selected = on_selected

    buttons = []
    for make in sorted({p.get("make") for p in platforms.values() if p.get("make")}):
      btn = BigButton(make, "")
      btn.set_click_callback(lambda m=make: self._open_models(m))
      buttons.append(btn)
    self._scroller.add_widgets(buttons)

  def _open_models(self, make):
    gui_app.push_widget(VehicleModelListMici(self._platforms, make, self._on_selected))


class VehicleModelListMici(NavScroller):
  def __init__(self, platforms, make, on_selected):
    super().__init__()
    self._on_selected = on_selected

    buttons = []
    for name in sorted(n for n, d in platforms.items() if d.get("make") == make):
      btn = BigButton(name, "")
      btn.set_click_callback(lambda n=name: self._select(n))
      buttons.append(btn)
    self._scroller.add_widgets(buttons)

  def _select(self, name):
    gui_app.pop_widget()
    gui_app.pop_widget()
    self._on_selected(name)
