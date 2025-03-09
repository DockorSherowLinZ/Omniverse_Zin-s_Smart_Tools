import omni.ext
import omni.ui as ui
import omni.kit.commands

from pxr import Usd, Sdf, Gf, Tf, UsdGeom, UsdPhysics, UsdShade
from omni.ui import color as cl

def some_public_function(x: int):
    print("[SmartMeasure] some_public_function was called with x: ", x)
    return x ** x

class SmartmeasureExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[SmartMeasure] SmartMeasure startup")

        self._window = ui.Window("Smart Measure", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                self._label = ui.Label("Press Add Button to measure a object.")

                def read_object_size():
                    selection = omni.usd.get_context().get_selection().get_selected_prim_paths()
                    if selection:
                        path = selection[0]
                        stage = omni.usd.get_context().get_stage()
                        prim = stage.GetPrimAtPath(path)

                        if prim:
                            geom = UsdGeom.Gprim(prim)
                            purposes = [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy, UsdGeom.Tokens.guide]
                            bounds = geom.ComputeLocalBound(Usd.TimeCode.Default(), purposes[0], purposes[1], purposes[2], purposes[3])
                            size = bounds.GetRange().GetSize()

                            # 將尺寸轉換為公分
                            size_cm = [dimension for dimension in size]
                            self._label.text = f"Size: Length={size_cm[0]:.2f} cm, Width={size_cm[1]:.2f} cm, Height={size_cm[2]:.2f} cm"
                        else:
                            self._label.text = "Can't find a object"
                    else:
                        self._label.text = "Select a object"

                def on_add():
                    read_object_size()

                def on_reset():
                    self._count = 0
                    self._label.text = "Select an object"

                on_reset()

                with ui.VStack():
                    ui.Button("Measure", clicked_fn=on_add)
                    ui.Button("Reset", clicked_fn=on_reset)

    def on_shutdown(self):
        print("[SmartMeasure] SmartMeasure shutdown")
