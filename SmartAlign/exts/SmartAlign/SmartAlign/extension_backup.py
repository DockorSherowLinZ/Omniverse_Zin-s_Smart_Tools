import omni.ext
import omni.usd
import omni.ui as ui
from pxr import Usd, UsdGeom, Gf

class SmartAlignExtension(omni.ext.IExt):
    # Extension startup: create UI
    def on_startup(self, ext_id):
        print("[SmartAlign] Startup")
        # Create a floating window for the SmartAlign UI
        
        self._window = ui.Window("SmartAlign", width=250, height=250)
        # Build the UI with a vertical layout of buttons
        with self._window.frame:
            with ui.VStack():
                ui.Button("Left Align", clicked_fn=self._on_left_align)
                ui.Button("Right Align", clicked_fn=self._on_right_align)
                ui.Button("Center Align (H)", clicked_fn=self._on_center_align)
                ui.Button("Top Align", clicked_fn=self._on_top_align)
                ui.Button("Bottom Align", clicked_fn=self._on_bottom_align)

    def on_shutdown(self):
        print("[SmartAlign] Shutdown")
        # Destroy the UI window if it exists
        if hasattr(self, "_window") and self._window:
            self._window.destroy()
            self._window = None

    def _get_selected_prims(self):
        """Helper to get currently selected prim paths."""
        ctx = omni.usd.get_context()
        selection = ctx.get_selection().get_selected_prim_paths()
        return selection

    def _align_prims(self, mode):
        """Core alignment logic: compute target and move prims based on mode."""
        paths = self._get_selected_prims()
        if not paths or len(paths) < 2:
            # Nothing to align if fewer than 2 prims selected
            return

        stage = omni.usd.get_context().get_stage()
        # Determine vertical axis index (1 for Y-up, 2 for Z-up)
        up_axis = UsdGeom.GetStageUpAxis(stage)
        vert_index = 1 if up_axis.upper() == "Y" else 2

        # Compute global target coordinate based on mode
        global_min_x = float("inf")
        global_max_x = float("-inf")
        global_min_vert = float("inf")
        global_max_vert = float("-inf")
        # Store per-prim values for second pass
        prim_bounds = {}

        for path in paths:
            # Compute world bounding box for this prim
            (min_pt, max_pt) = omni.usd.get_context().compute_path_world_bounding_box(path)
            # min_pt and max_pt are sequences of 3 floats (x,y,z)
            min_x, min_y, min_z = min_pt[0], min_pt[1], min_pt[2]
            max_x, max_y, max_z = max_pt[0], max_pt[1], max_pt[2]
            # Track global extrema
            if min_x < global_min_x: 
                global_min_x = min_x
            if max_x > global_max_x: 
                global_max_x = max_x
            # Vertical axis (Y or Z depending on stage up-axis)
            min_vert = min_pt[vert_index]
            max_vert = max_pt[vert_index]
            if min_vert < global_min_vert:
                global_min_vert = min_vert
            if max_vert > global_max_vert:
                global_max_vert = max_vert
            # Store values for use when moving this prim
            prim_bounds[path] = {
                "min_x": min_x, "max_x": max_x,
                "min_vert": min_vert, "max_vert": max_vert
            }

        # Determine target coordinate for alignment
        if mode == "left":
            target_x = global_min_x
        elif mode == "right":
            target_x = global_max_x
        elif mode == "center":
            target_x = 0.5 * (global_min_x + global_max_x)
        elif mode == "top":
            target_vert = global_max_vert
        elif mode == "bottom":
            target_vert = global_min_vert

        # Move each prim to align
        for path in paths:
            prim = stage.GetPrimAtPath(path)
            if not prim.IsValid():
                continue
            parent = prim.GetParent()
            # Compute parent world transform (or identity if no parent or parent is pseudo-root)
            parent_world_mtx = Gf.Matrix4d(1.0)  # identity by default
            if parent.IsValid() and not parent.IsPseudoRoot():
                parent_world = omni.usd.get_context().compute_path_world_transform(parent.GetPath().pathString)
                parent_world_mtx = Gf.Matrix4d(*parent_world)
            parent_inv_mtx = parent_world_mtx.GetInverse()

            # Calculate the offset in world space for this prim
            offset_world = Gf.Vec3d(0, 0, 0)
            if mode in ("left", "right", "center"):
                # horizontal alignment (X axis)
                current_center_x = 0.5 * (prim_bounds[path]["min_x"] + prim_bounds[path]["max_x"])
                if mode == "left":
                    # Align left edge
                    offset_x = target_x - prim_bounds[path]["min_x"]
                elif mode == "right":
                    # Align right edge
                    offset_x = target_x - prim_bounds[path]["max_x"]
                elif mode == "center":
                    # Align centers horizontally
                    offset_x = target_x - current_center_x
                offset_world = Gf.Vec3d(offset_x, 0, 0)
            else:
                # vertical alignment (Y or Z axis)
                if mode == "top":
                    offset_val = target_vert - prim_bounds[path]["max_vert"]
                elif mode == "bottom":
                    offset_val = target_vert - prim_bounds[path]["min_vert"]
                # Apply offset along the vertical axis
                if vert_index == 1:
                    # Y-up stage
                    offset_world = Gf.Vec3d(0, offset_val, 0)
                else:
                    # Z-up stage
                    offset_world = Gf.Vec3d(0, 0, offset_val)

            # Convert world offset to local space (account for parent transform)
            # Treat offset as a vector (w=0) for transformation
            offset_vec4 = Gf.Vec4d(offset_world[0], offset_world[1], offset_world[2], 0.0)
            local_offset_vec4 = offset_vec4 * parent_inv_mtx
            local_offset = Gf.Vec3d(local_offset_vec4[0], local_offset_vec4[1], local_offset_vec4[2])

            # Get current local translation of the prim
            # Compute prim's current local transform matrix:
            prim_world = omni.usd.get_context().compute_path_world_transform(path)
            prim_world_mtx = Gf.Matrix4d(*prim_world)
            local_mtx = parent_inv_mtx * prim_world_mtx
            # Extract translation components
            old_local_translate = Gf.Vec3d(local_mtx[3][0], local_mtx[3][1], local_mtx[3][2])
            # Compute new local translation
            new_local_translate = old_local_translate + local_offset

            # Execute the transform command to move the prim
            omni.kit.commands.execute(
                "TransformPrimSRTCommand",
                path=path,
                new_translation=new_local_translate,
                old_translation=old_local_translate
            )

    # Define one method per alignment mode that calls _align_prims with the mode
    def _on_left_align(self):
        self._align_prims(mode="left")
    def _on_right_align(self):
        self._align_prims(mode="right")
    def _on_center_align(self):
        self._align_prims(mode="center")
    def _on_top_align(self):
        self._align_prims(mode="top")
    def _on_bottom_align(self):
        self._align_prims(mode="bottom")