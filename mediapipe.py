import bpy

from bpy.types import Panel, Operator, PropertyGroup, FloatProperty, PointerProperty
from bpy.utils import register_class, unregister_class
from bpy_extras.io_utils import ImportHelper


try:
    import cv2
    import mediapipe as mp
except Exception as e:
    # bpy.ops.message.messagebox('INVOKE_DEFAULT', 'Installing additional libraries, this may take a moment...')
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    install()
    import cv2
    import mediapipe as mp

body_names = [
"00 nose",
"01 left eye (inner)",
"02 left eye",
"03 left eye (outer)",
"04 right eye (inner)",
"05 right eye",
"06 right eye (outer)",
"07 left ear",
"08 right ear",
"09 mouth (left)",
"10 mouth (right)",
"11 left shoulder",
"12 right shoulder",
]


def install():
    #Install MediaPipe and dependencies 
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "ensurepip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mediapipe"])


def body_setup():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)

    scene_objects = [n for n in bpy.context.scene.objects.keys()]
    bpy.ops.object.add(radius=1.0, type='EMPTY')
    pose = bpy.context.active_object
    pose.name = "Pose"

    bpy.ops.object.add(radius=1.0, type='EMPTY')
    body = bpy.context.active_object
    body.name = "Body"
    body.parent = pose

    for k in range(13):
        bpy.ops.mesh.primitive_cube_add()
        box = bpy.context.active_object
        box.name = body_names[k]
        box.scale = (0.01, 0.01, 0.01)
        box.parent = body

    body = bpy.context.scene.objects["Body"]
    return body


def run_body():
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose

    body = body_setup()

    cap = cv2.VideoCapture(0)

    with mp_pose.Pose(smooth_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        for n in range(9000):
            success, image = cap.read()
            if not success: continue

            # image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            image.flags.writeable = False
            results = pose.process(image)

            if results.pose_landmarks:
                bns = [b for b in results.pose_landmarks.landmark]
                scale = 2
                bones = sorted(body.children, key=lambda b: b.name)

                for k in range(13):
                    bones[k].location.y = (bns[k].z)*0.5
                    bones[k].location.x = (0.5-bns[k].x)*scale
                    bones[k].location.z = (0.5-bns[k].y)*scale
                    bones[k].keyframe_insert(data_path="location", frame=n)

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            image = cv2.flip(image, 1)

            cv2.imshow('MediaPipe Pose', image)
            if cv2.waitKey(1) & 0xFF == 27:
                break

            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            bpy.context.scene.frame_set(n)

        cap.release()
        cv2.destroyAllWindows()



class RunOperator(bpy.types.Operator):
    #Tooltip
    bl_idname = "object.run_body_operator"
    bl_label = "Run Body Operator"

    def execute(self, context):
        run_body()
        return {'FINISHED'}



class MediaPipePanel(bpy.types.Panel):
    bl_label = "MediaPipe"
    bl_category = "MediaPipe"
    bl_idname = "MediaPipe"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "MediPipe v2"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        row = layout.row()

        row = layout.row()
        row.label(text="Run Motion Capture")

        row = layout.row()
        row.operator(RunOperator.bl_idname, text="Camera")

        row = layout.row()
        row.label(text="(Press escape to stop)")


_classes = [
    MediaPipePanel,
    RunOperator,
]


def register():
    for c in _classes: register_class(c)


def unregister():
    for c in _classes: unregister_class(c)

if __name__ == "__main__":
    register()
