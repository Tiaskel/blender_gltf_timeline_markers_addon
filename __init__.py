import bpy
import io_scene_gltf2.io.com.gltf2_io
from io_scene_gltf2.blender.exp.cameras import gather_camera
from io_scene_gltf2.blender.exp.gather import gather_gltf2

bl_info = {
    "name": "Timeline markers Extension",
    "extension_name": "WEBGI_animation_markers",
    "category": "GLTF Exporter",
    "version": (1, 0, 1),
    "blender": (4, 4, 0),
    'location': 'File > Export > glTF 2.0',
    'description': 'Extension to export timeline markers and cameras in gltf.',
    'tracker_url': '',
    'isDraft': False,
    'developer': "Palash Bansal",
    'url': 'https://repalash.com',
}

extension_is_required = False

class TimelineMarkersExtensionProperties(bpy.types.PropertyGroup):
    __annotations__ = {
        "enabled": bpy.props.BoolProperty(
            name=bl_info["name"],
            description='Include this extension in the exported glTF file.',
            default=True
        ),
        "extension_name": bpy.props.StringProperty(
            name="Extension",
            description='GLTF extension name.',
            default=bl_info["extension_name"]
        ),
    }

class GLTF_PT_TimelineMarkersExtensionPanel(bpy.types.Panel):
    bl_idname = "GLTF_PT_timeline_markers_extension"
    bl_label = "Export Timeline Markers"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "EXPORT_SCENE_OT_gltf"

    def draw_header(self, context):
        props = context.scene.TimelineMarkersExtensionProperties
        self.layout.prop(props, 'enabled')

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        props = context.scene.TimelineMarkersExtensionProperties
        layout.active = props.enabled
        box = layout.box()
        box.label(text=props.extension_name)
        layout.prop(props, 'extension_name', text="GLTF extension name")

class glTF2ExportUserExtension:
    def __init__(self):
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        self.properties = bpy.context.scene.TimelineMarkersExtensionProperties
        self.cameras = {}

    def gather_camera_hook(self, gltf2_camera, blender_camera, export_settings):
        self.cameras[blender_camera.name] = gltf2_camera
        if blender_camera.sensor_fit == 'AUTO':
            if gltf2_camera.extras is None:
                gltf2_camera.extras = {}
            gltf2_camera.extras['autoAspect'] = True

    def gather_scene_hook(self, gltf2_scene, blender_scene, export_settings):
        markers = blender_scene.timeline_markers
        extMarkers = []
        fps = blender_scene.render.fps
        for marker in markers:
            markerData = {
                'name': marker.name,
                'frame': marker.frame,
                'time': marker.frame / fps
            }
            if marker.camera is not None:
                camIndex = self.cameras.get(marker.camera.data.name)
                if camIndex is not None:
                    markerData['camera'] = camIndex
            extMarkers.append(markerData)

        self.cameras.clear()

        if not gltf2_scene.extensions:
            gltf2_scene.extensions = {}
        gltf2_scene.extensions[self.properties.extension_name] = self.Extension(
            name=self.properties.extension_name,
            extension={'markers': extMarkers},
            required=extension_is_required
        )

def register():
    import addon_utils
    if not addon_utils.check("io_scene_gltf2")[1]:
        addon_utils.enable("io_scene_gltf2")

    bpy.utils.register_class(TimelineMarkersExtensionProperties)
    bpy.utils.register_class(GLTF_PT_TimelineMarkersExtensionPanel)
    bpy.types.Scene.TimelineMarkersExtensionProperties = bpy.props.PointerProperty(type=TimelineMarkersExtensionProperties)

def unregister():
    bpy.utils.unregister_class(GLTF_PT_TimelineMarkersExtensionPanel)
    bpy.utils.unregister_class(TimelineMarkersExtensionProperties)
    del bpy.types.Scene.TimelineMarkersExtensionProperties
