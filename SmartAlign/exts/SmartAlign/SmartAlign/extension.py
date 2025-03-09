import omni.ext
import omni.ui as ui
import omni.kit.commands

from pxr import Usd, Sdf, Gf, Tf, UsdGeom, UsdPhysics, UsdShade
from omni.ui import color as cl

# Function to align objects on a specific axis
def align_objects(stage, object_a_path, object_b_path, align_axis):
    # Get A and B objects' UsdPrim
    object_a = stage.GetPrimAtPath(object_a_path)
    object_b = stage.GetPrimAtPath(object_b_path)
    
    if not object_a or not object_b:
        print("Cannot find specified objects")
        return
    
    # Get B object's transformation
    transform_b = UsdGeom.Xformable(object_b).GetLocalTransformation()
    
    # Get A object's transformation
    transform_a = UsdGeom.Xformable(object_a).GetLocalTransformation()
    
    # Align on the specified axis
    match align_axis:
        case 'X':
            transform_a.SetTranslateOnly(Gf.Vec3d(transform_b.ExtractTranslation()[0], transform_a.ExtractTranslation()[1], transform_a.ExtractTranslation()[2]))
        case 'Y':
            transform_a.SetTranslateOnly(Gf.Vec3d(transform_a.ExtractTranslation()[0], transform_b.ExtractTranslation()[1], transform_a.ExtractTranslation()[2]))
        case 'Z':
            transform_a.SetTranslateOnly(Gf.Vec3d(transform_a.ExtractTranslation()[0], transform_a.ExtractTranslation()[1], transform_b.ExtractTranslation()[2]))
    
    # Set A object's transformation
    UsdGeom.Xformable(object_a).SetLocalTransformation(transform_a)

class SmartAlignExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[SmartAlign] SmartAlign startup")

        self._selected_object_a = None
        self._align_axis = 'X'  # Default to align on X axis

        self._window = ui.Window("Smart Align", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                ui.Label("Select Object A and click Align")
                self.message_label = ui.Label("")

                def on_align_click():
                    # Execute alignment
                    if not self._selected_object_a:
                        self.message_label.text = "Please select Object A first"
                        return
                    
                    stage = omni.usd.get_context().get_stage()
                    object_b_path = "/World/ObjectB"  # Here you can set a fixed B object path or let the user input
                    
                    try:
                        print(f"Aligning {self._selected_object_a} to {object_b_path} on {self._align_axis} axis")
                        align_objects(stage, self._selected_object_a, object_b_path, self._align_axis)
                        self.message_label.text = "Objects aligned successfully"
                    except Exception as e:
                        self.message_label.text = f"Error: {str(e)}"
                        print(f"Error: {str(e)}")

                ui.Button("Align", clicked_fn=on_align_click)

                ui.Label("Object A Path")
                self.object_a_path_model = ui.SimpleStringModel("/World/ObjectA")
                self.object_a_path_field = ui.StringField(model=self.object_a_path_model)

                def on_select_a():
                    self._selected_object_a = self.object_a_path_model.as_string
                    self.message_label.text = f"Selected Object A: {self._selected_object_a}"
                    print(f"Selected Object A: {self._selected_object_a}")

                ui.Button("Select A", clicked_fn=on_select_a)

                ui.Label("Select Axis to Align")
                self.axis_combo_model = ui.SimpleStringModel("X")
                axis_combo = ui.ComboBox(0, model=self.axis_combo_model, items=["X", "Y", "Z"], on_current_index_changed_fn=self._set_align_axis)
                print("ComboBox created")

    def _set_align_axis(self, combo):
        self._align_axis = combo.model.as_string
        print(f"Axis set to: {self._align_axis}")

    def on_shutdown(self):
        print("[SmartAlign] SmartAlign shutdown")
