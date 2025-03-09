import omni.ext
import omni.ui as ui
import omni.kit.commands

from pxr import Usd, Sdf, Gf, Tf, UsdGeom, UsdPhysics, UsdShade
from omni.ui import color as cl

#stage = omni.usd.get_context().get_stage()

def some_public_function(x: int):
    print("[SmartReference] some_public_function was called with x: ", x)
    return x ** x

class SmartreferenceExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        print("[SmartReference] SmartReference startup")

        self._window = ui.Window("Reference Assets", width=350, height=400)
        self.stage = omni.usd.get_context().get_stage()
               
        with self._window.frame:
            field_input = {
                'background_color': cl(30),
                'color': cl(160),
                'font_size': 14,                    
                'padding': 4,
                'margin': 4,
                'border_radius': 4.0,
                }
            field_label = {
                'color': cl(255),
                'font_size': 14,                    
                'padding': 4,
                'margin': 4,
                }
            field_title = {
                'color': cl(255),
                'font_size': 14,                    
                'padding': 4,
                'margin': 4,
                }
            field_context = {
                'color': cl(118,185,0),
                'font_size': 14,                    
                'padding': 4,
                'margin': 4,
                }
            field_line = {
                'color': cl(110),               
                'margin': 4,
            }
            
            with ui.VStack(height=18):
                with ui.HStack(width=200):
                    ui.Label("Start index:", name="text",style=field_label)
                    start_index_field = ui.StringField(style=field_input)
                with ui.HStack(width=200):
                    ui.Label("End index:", name="text",style=field_label)
                    end_index_field = ui.StringField(style=field_input)
                with ui.HStack(width=200):
                    ui.Label("Digits count:", name="text",style=field_label)
                    width_field = ui.StringField(style=field_input)  # 新增的寬度輸入欄位
                
                ui.Line(name='default',style=field_line)

                ui.Label("Prim Path:", name="text",style=field_title)
                prim_path_template_field = ui.StringField(style=field_input)
                ui.Label("Asset URL:", name="text",style=field_title)
                asset_url_field = ui.StringField(style=field_input)

                def on_click():
                    start_index = int(start_index_field.model.get_value_as_string())
                    end_index = int(end_index_field.model.get_value_as_string())
                    width = int(width_field.model.get_value_as_string())  # 獲取使用者輸入的寬度
                    asset_name = prim_path_template_field.model.get_value_as_string()
                    asset_path = asset_url_field.model.get_value_as_string()

                    def generate_path(i, width):  # 設定物件的 Prim 路徑
                        return f'{asset_name}{i:0{width}d}'

                    for i in range(start_index, end_index + 1):  # 設定物件的 URL
                        path_str = generate_path(i, width)
                        path = Sdf.Path(path_str)
                        prim = self.stage.GetPrimAtPath(path)

                        if prim.IsValid():  # 遍歷所有指定的路徑，檢查每個路徑上的 prim 是否有效
                            prim.GetReferences().AddReference(asset_path)
                        else:
                            print(f"Invalid prim at path: {path}")
                
                with ui.HStack():                    
                    start_index_field.model.set_value("ex:001")
                    end_index_field.model.set_value("ex:003")
                    width_field.model.set_value("ex:3")  # 設置寬度輸入欄位的初始值
                with ui.VStack():
                    prim_path_template_field.model.set_value("/World/Example")
                    asset_url_field.model.set_value("omniverse://localhost/Projects/Example.usd")
                with ui.VStack():
                    ui.Button("Confirm", clicked_fn=on_click, alignment=ui.Alignment.CENTER, height=40, width=150)
                    ui.Label("When referencing objects, first set the start index, end index,and the number of digits count.\n Then, set the path and URL of the reference object.", name="text",word_wrap=True,style=field_context)
             
    def on_shutdown(self):
        print("[SmartReference] SmartReference shutdown")

