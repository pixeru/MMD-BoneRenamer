import bpy
import threading
import time
from functools import lru_cache
from typing import Tuple, List, Dict
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty

try:
    from googletrans import Translator
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    print("GoogleTrans not available. Install using: pip install googletrans==3.1.0a0")

# Type definitions for better code clarity
BoneMapping = Tuple[str, ...]
BoneMappingList = List[BoneMapping]

# Bone name mappings for different formats
# Format order: [MMD English, XNALara, DAZ/Poser, Blender Rigify, Sims 2, Motion Builder, 3ds Max, Unknown, BEPu, MMD Japanese, MMD Japanese LR]
BONE_NAMES: BoneMappingList = [
    ("root", "root ground", "", "root", "auskel", "", "", "", "", "全ての親", "全ての親"), 
      
    ("neck", "head neck lower",  "neck", "neck", "neck", "Neck", "Neck", "Neck", "neck", "首", "首"),
    ("head", "head neck upper", "head", "head", "head", "Head", "Head", "Head", "head", "頭", "頭"),

    ("center", "root hips", "hip", 'hips', "root_rot", "Hips", "Hips", "Hip", "", "センター", "センター"),
    ("upper body 2", "spine upper", "chest", "chest", "spine2", "Spine2", "Chest3", "", 'chest', "上半身2", "上半身2"),
    ("upper body", "spine lower", "abdomen", "spine", "spine0", "chest", "Chest", "Chest1", 'spine', "上半身", "上半身"),
    ("lower body", "pelvis", "", "", "", "", "", "", 'hips', "下半身", "下半身"),

    ("shoulder_L", "arm left shoulder 1", "lCollar", "shoulder.L", "l_clavicle", "LeftShoulder", "LeftCollar", "Left Collar", 'shoulder.L', "左肩", "肩.L"),
    ("arm_L", "arm left shoulder 2", "lShldr", "upper_arm.L", "l_upperarm",  "LeftUpArm", "LeftShoulder", "Left Shoulder", 'uparm.L', "左腕", "腕.L"),
    ("elbow_L", "arm left elbow", "lForeArm", "forearm.L", "l_forearm", "LeftLowArm", "LeftElbow", "Left Forearm", 'loarm.L', "左ひじ", "ひじ.L"),
    ("wrist_L", "arm left wrist", "lHand", "hand.L", "l_hand", "LeftHand", "LeftWrist", "Left Hand", 'finger3-1.L',"左手首", "手首.L"),
    ("shoulder_R", "arm right shoulder 1", "rCollar", "shoulder.R", "r_clavicle", "RightShoulder", "RightCollar", "Right Collar", 'shoulder.R', "右肩", "肩.R"),
    ("arm_R", "arm right shoulder 2", "rShldr", "upper_arm.R", "r_upperarm", "RightUpArm", "RightShoulder", "Right Shoulder", 'uparm.R', "右腕", "腕.R"),
    ("elbow_R", "arm right elbow", "rForeArm", "forearm.R", "r_forearm", "RightLowArm", "RightElbow", "Right Forearm", 'loarm.R', "右ひじ", "ひじ.R"),
    ("wrist_R", "arm right wrist", "rHand", "hand.R", "r_hand", "RightHand", "RightWrist", "Right Hand", 'finger3-1.R',"右手首", "手首.R"),
    ("leg_L", "leg left thigh", "lThigh", "thigh.L", "l_thigh", "LeftUpLeg", "LeftHip", "Left Thigh", 'upleg.L', "左足", "足.L"),
    ("knee_L", "leg left knee", "lShin", "shin.L", "l_calf", "LeftLowLeg", "LeftKnee", "Left Shin", 'loleg.L', "左ひざ", "ひざ.L"),
    ("ankle_L", "leg left ankle", "lFoot", "foot.L", "l_foot", "LeftFoot", "LeftAnkle", "Left Foot", 'foot.L', "左足首", "足首.L"),
    ("leg_R", "leg right thigh", "rThigh", "thigh.R", "r_thigh", "RightUpLeg", "RightHip", "Right Thigh", 'upleg.R', "右足", "足.R"),
    ("knee_R", "leg right knee", "rShin", "shin.R", "r_calf", "RightLowLeg", "RightKnee", "Right Shin", 'loleg.R', "右ひざ", "ひざ.R"),
    ("ankle_R", "leg right ankle", "rFoot", "foot.R", "r_foot", "RightFoot", "RightAnkle", "Right Foot", 'foot.R', "右足首", "足首.R"),

    ("toe_L", "leg left toes", "lToe", "toe.L", "l_toe", 'LeftToeBase', "LeftToe", "Left Toe", 'toe1-1.L', "左つま先", "つま先.L"),
    ("toe_R", "leg right toes", "rToe", "toe.R", "r_toe", 'RightToeBase', "RightToe", 'toe1-1.R',"Right Toe", "右つま先", "つま先.R"),
    ("eye_L", "head eyeball left", "leftEye", "eye.L", "l_eye", "LeftEye", "LeftEye", "Left Eye", 'eye.L', "左目", "目.L"),
    ("eye_R", "head eyeball right", "rightEye", "eye.R", "r_eye", "RightEye", "RightEye", "Right Eye", 'eye.R', "右目", "目.R"),
]

FINGER_BONES: BoneMappingList = [
    ("thumb1_L", "arm left finger 1b", "lThumb2", "thumb.02.L", "l_thumb1", 'LeftHandThumb2', 'LeftFinger01', 'finger1-3.L', "左親指１", "親指１.L"),
    ("thumb2_L", "arm left finger 1c", "lThumb3", "thumb.03.L", "l_thumb2", 'LeftHandThumb3', 'LeftFinger02', 'finger1-4.L', "左親指２", "親指２.L"),
    ("fore1_L", "arm left finger 2a", "lIndex1", "f_index.01.L", "l_index0", 'LeftHandIndex1', 'LeftFinger1', 'finger2-2.L', "左人指１", "人指１.L"),
    ("fore2_L", "arm left finger 2b", "lIndex2", "f_index.02.L", "l_index1", 'LeftHandIndex2', 'LeftFinger11', 'finger2-3.L', "左人指２", "人指２.L"),
    ("fore3_L", "arm left finger 2c", "lIndex3", "f_index.03.L", "l_index2", 'LeftHandIndex3', 'LeftFinger12', 'finger2-4.L', "左人指３", "人指３.L"),
    ("middle1_L", "arm left finger 3a", "lMid1", "f_middle.01.L", "l_mid0", 'LeftHandMiddle1', 'LeftFinger2', 'finger3-2.L', "左中指１", "中指１.L"),
    ("middle2_L", "arm left finger 3b", "lMid2", "f_middle.02.L", "l_mid1", 'LeftHandMiddle2', 'LeftFinger21', 'finger3-3.L', "左中指２", "中指２.L"),
    ("middle3_L", "arm left finger 3c", "lMid3", "f_middle.03.L", "l_mid2", 'LeftHandMiddle3', 'LeftFinger22', 'finger3-4.L', "左中指３", "中指３.L"),
    ("third1_L", "arm left finger 4a", "lRing1", "f_ring.01.L", "l_ring0", 'LeftHandRing1', 'LeftFinger3', 'finger4-2.L', "左薬指１", "薬指１.L"),
    ("third2_L", "arm left finger 4b", "lRing2", "f_ring.02.L", "l_ring1", 'LeftHandRing2', 'LeftFinger31', 'finger4-3.L', "左薬指２", "薬指２.L"),
    ("third3_L", "arm left finger 4c", "lRing3", "f_ring.03.L", "l_ring2", 'LeftHandRing3', 'LeftFinger32', 'finger4-4.L', "左薬指３", "薬指３.L"),
    ("little1_L", "arm left finger 5a", "lPinky1", "f_pinky.01.L", "l_pinky0", 'LeftHandPinky1', 'LeftFinger4', 'finger5-2.L', "左小指１", "小指１.L"),
    ("little2_L", "arm left finger 5b", "lPinky2", "f_pinky.02.L", "l_pinky1", 'LeftHandPinky2', 'LeftFinger41', 'finger5-3.L', "左小指２", "小指２.L"),
    ("little3_L", "arm left finger 5c", "lPinky3", "f_pinky.03.L", "l_pinky2", 'LeftHandPinky3', 'LeftFinger42', 'finger5-4.L', "左小指３", "小指３.L"),
    ("thumb1_R", "arm right finger 1b", "rThumb2", "thumb.02.R", "r_thumb1", 'RightHandThumb2', 'RightFinger01', 'finger1-3.R', "右親指１", "親指１.R"),
    ("thumb2_R", "arm right finger 1c", "rThumb3", "thumb.03.R", "r_thumb2", 'RightHandThumb3', 'RightFinger02', 'finger1-4.R', "右親指２", "親指２.R"),
    ("fore1_R", "arm right finger 2a", "rIndex1", "f_index.01.R", "r_index0", 'RightHandIndex1', 'RightFinger1', 'finger2-2.R', "右人指１", "人指１.R"),
    ("fore2_R", "arm right finger 2b", "rIndex2", "f_index.02.R", "r_index1", 'RightHandIndex2', 'RightFinger11', 'finger2-3.R', "右人指２", "人指２.R"),
    ("fore3_R", "arm right finger 2c", "rIndex3", "f_index.03.R", "r_index2", 'RightHandIndex3', 'RightFinger12', 'finger2-4.R', "右人指３", "人指３.R"),
    ("middle1_R", "arm right finger 3a", "rMid1", "f_middle.01.R", "r_mid0", 'RightHandMiddle1', 'RightFinger2', 'finger3-2.R', "右中指１", "中指１.R"),
    ("middle2_R", "arm right finger 3b", "rMid2", "f_middle.02.R", "r_mid1", 'RightHandMiddle2', 'RightFinger21', 'finger3-3.R', "右中指２", "中指２.R"),
    ("middle3_R", "arm right finger 3c", "rMid3", "f_middle.03.R", "r_mid2", 'RightHandMiddle3', 'RightFinger22', 'finger3-4.R', "右中指３", "中指３.R"),
    ("third1_R", "arm right finger 4a", "rRing1", "f_ring.01.R", "r_ring0", 'RightHandRing1', 'RightFinger3', 'finger4-2.R', "右薬指１", "薬指１.R"),
    ("third2_R", "arm right finger 4b", "rRing2", "f_ring.02.R", "r_ring1", 'RightHandRing2', 'RightFinger31', 'finger4-3.R', "右薬指２", "薬指２.R"),
    ("third3_R", "arm right finger 4c", "rRing3", "f_ring.03.R", "r_ring2", 'RightHandRing3', 'RightFinger32', 'finger4-4.R', "右薬指３", "薬指３.R"),
    ("little1_R", "arm right finger 5a", "rPinky1", "f_pinky.01.R", "r_pinky0", 'RightHandPinky1', 'RightFinger4', 'finger5-2.R', "右小指１", "小指１.R"),
    ("little2_R", "arm right finger 5b", "rPinky2", "f_pinky.02.R", "r_pinky1", 'RightHandPinky2', 'RightFinger41', 'finger5-3.R', "右小指２", "小指２.R"),
    ("little3_R", "arm right finger 5c", "rPinky3", "f_pinky.03.R", "r_pinky2", 'RightHandPinky3', 'RightFinger42', 'finger5-4.R', "右小指３", "小指３.R"),
    ("thumb0_L", "arm left finger 1a", "lThumb1", "thumb.01.L", "l_thumb0", 'LeftHandThumb1', 'LeftFinger0', 'finger1-2.L', "左親指0", "親指0.L"),
    ("thumb0_R", "arm right finger 1a", "rThumb1", "thumb.01.R", "r_thumb0", 'RightHandThumb1', 'RightFinger0', 'finger1-2.R', "右親指0", "親指0.R"),
]

JP_TO_EN_MAPPING = [
    ("全ての親", "ParentNode"),
    ("操作中心", "ControlNode"),
    ("センター", "Center"),
    ("ｾﾝﾀｰ", "Center"),
    ("グループ", "Group"),
    ("グルーブ", "Groove"),
    ("キャンセル", "Cancel"),
    ("上半身", "UpperBody"),
    ("下半身", "LowerBody"),
    ("手首", "Wrist"),
    ("足首", "Ankle"),
    ("首", "Neck"),
    ("頭", "Head"),
    ("顔", "Face"),
    ("下顎", "Chin"),
    ("下あご", "Chin"),
    ("あご", "Jaw"),
    ("顎", "Jaw"),
    ("両目", "Eyes"),
    ("目", "Eye"),
    ("眉", "Eyebrow"),
    ("舌", "Tongue"),
    ("涙", "Tears"),
    ("泣き", "Cry"),
    ("歯", "Teeth"),
    ("照れ", "Blush"),
    ("青ざめ", "Pale"),
    ("ガーン", "Gloom"),
    ("汗", "Sweat"),
    ("怒", "Anger"),
    ("感情", "Emotion"),
    ("符", "Marks"),
    ("暗い", "Dark"),
    ("腰", "Waist"),
    ("髪", "Hair"),
    ("三つ編み", "Braid"),
    ("胸", "Breast"),
    ("乳", "Boob"),
    ("おっぱい", "Tits"),
    ("筋", "Muscle"),
    ("腹", "Belly"),
    ("鎖骨", "Clavicle"),
    ("肩", "Shoulder"),
    ("腕", "Arm"),
    ("うで", "Arm"),
    ("ひじ", "Elbow"),
    ("肘", "Elbow"),
    ("手", "Hand"),
    ("親指", "Thumb"),
    ("人指", "IndexFinger"),
    ("人差指", "IndexFinger"),
    ("中指", "MiddleFinger"),
    ("薬指", "RingFinger"),
    ("小指", "LittleFinger"),
    ("足", "Leg"),
    ("ひざ", "Knee"),
    ("つま", "Toe"),
    ("袖", "Sleeve"),
    ("新規", "New"),
    ("ボーン", "Bone"),
    ("捩", "Twist"),
    ("回転", "Rotation"),
    ("軸", "Axis"),
    ("ﾈｸﾀｲ", "Necktie"),
    ("ネクタイ", "Necktie"),
    ("ヘッドセット", "Headset"),
    ("飾り", "Accessory"),
    ("リボン", "Ribbon"),
    ("襟", "Collar"),
    ("紐", "String"),
    ("コード", "Cord"),
    ("イヤリング", "Earring"),
    ("メガネ", "Eyeglasses"),
    ("眼鏡", "Glasses"),
    ("帽子", "Hat"),
    ("ｽｶｰﾄ", "Skirt"),
    ("スカート", "Skirt"),
    ("パンツ", "Pantsu"),
    ("シャツ", "Shirt"),
    ("フリル", "Frill"),
    ("マフラー", "Muffler"),
    ("ﾏﾌﾗｰ", "Muffler"),
    ("服", "Clothes"),
    ("ブーツ", "Boots"),
    ("ねこみみ", "CatEars"),
    ("ジップ", "Zip"),
    ("ｼﾞｯﾌﾟ", "Zip"),
    ("ダミー", "Dummy"),
    ("ﾀﾞﾐｰ", "Dummy"),
    ("基", "Category"),
    ("あほ毛", "Antenna"),
    ("アホ毛", "Antenna"),
    ("モミアゲ", "Sideburn"),
    ("もみあげ", "Sideburn"),
    ("ツインテ", "Twintail"),
    ("おさげ", "Pigtail"),
    ("ひらひら", "Flutter"),
    ("調整", "Adjustment"),
    ("補助", "Aux"),
    ("右", "Right"),
    ("左", "Left"),
    ("前", "Front"),
    ("後ろ", "Behind"),
    ("後", "Back"),
    ("横", "Side"),
    ("中", "Middle"),
    ("上", "Upper"),
    ("下", "Lower"),
    ("親", "Parent"),
    ("先", "Tip"),
    ("パーツ", "Part"),
    ("光", "Light"),
    ("戻", "Return"),
    ("羽", "Wing"),
    ("根", "Base"),  # ideally 'Root' but to avoid confusion
    ("毛", "Strand"),
    ("尾", "Tail"),
    ("尻", "Butt"),
]

# Supported bone mapping formats
BONE_MAPS = [
    ('mmd_english', 'MMD English', 'MikuMikuDance English bone names'),
    ('xna_lara', 'XNALara', 'XNALara bone names'),
    ('daz_poser', 'DAZ/Poser', 'DAZ Studio and Poser bone names'),
    ('blender_rigify', 'Rigify', 'Blender Rigify bone names'),
    ('sims_2', 'Sims 2', 'The Sims 2 bone names'),
    ('motion_builder', 'Motion Builder', 'Motion Builder bone names'),
    ('3ds_max', '3ds Max', '3ds Max bone names'),
    ('type_x', 'Type X', 'Type X bone names'),
    ('bepu', 'BEPu', 'BEPu bone names'),
    ('mmd_japanese', 'MMD Japanese', 'MikuMikuDance Japanese bone names'),
    ('mmd_japaneseLR', 'MMD Japanese L/R', 'MikuMikuDance Japanese bone names with L/R suffixes'),
    ('unknown', 'Unknown', 'Unknown bone format')
]

def show_message(message: str, title: str = "Message", icon: str = 'INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

JP_BONE_MAPPING = {
    # Basic body parts
    "全ての親": "root",
    "センター": "center",
    "グルーブ": "groove",
    "親": "parent",
    "腰": "waist",
    "上半身": "upper body",
    "下半身": "lower body",
    "首": "neck",
    "頭": "head",
    "目": "eye",
    "両目": "eyes",
    "顔": "face",
    "あご": "jaw",
    "顎": "jaw",
    "舌": "tongue",
    "歯": "teeth",
    "髪": "hair",
    "胸": "chest",
    
    # Arms and hands
    "肩": "shoulder",
    "腕": "arm",
    "ひじ": "elbow",
    "手首": "wrist",
    "手": "hand",
    "親指": "thumb",
    "人指": "fore",
    "中指": "middle",
    "薬指": "third",
    "小指": "little",
    
    # Legs and feet
    "足": "leg",
    "ひざ": "knee",
    "足首": "ankle",
    "つま先": "toe",
    
    # Clothing and accessories
    "スカート": "skirt",
    "パンツ": "pants",
    "リボン": "ribbon",
    "紐": "string",
    "服": "clothes",
    "襟": "collar",
    "袖": "sleeve",
    
    # Hair parts
    "前髪": "front hair",
    "後髪": "back hair",
    "横髪": "side hair",
    "もみあげ": "sideburn",
    "アホ毛": "ahoge",
    
    # Directional terms
    "右": "right",
    "左": "left",
    "前": "front",
    "後ろ": "back",
    "中": "middle",
    "上": "upper",
    "下": "lower",
    "先": "tip",
    
    # Additional terms
    "補助": "auxiliary",
    "調整": "adjustment",
    "基": "base",
    "戻": "return",
    "操作": "control",
    "軸": "axis",
    "捩": "twist",
    "回転": "rotation",
    "ダミー": "dummy",
    "パーツ": "parts",
    
    # MMD specific
    "ＩＫ": "IK",
    "エクステ": "extension",
}

class TranslationCache:
    """Thread-safe translation cache"""
    def __init__(self):
        self._cache = {}
        self._lock = threading.Lock()
    
    def get(self, key):
        with self._lock:
            return self._cache.get(key)
    
    def set(self, key, value):
        with self._lock:
            self._cache[key] = value

# Global translation cache
translation_cache = TranslationCache()

class AsyncTranslator:
    """Handles asynchronous translation requests"""
    def __init__(self):
        self.translator = Translator()
        self.timeout = 2.0  # Translation timeout in seconds
        
    @lru_cache(maxsize=1000)
    def translate_text(self, text: str, src='ja', dest='en') -> str:
        """Translate text with caching and timeout"""
        try:
            # Check cache first
            cached = translation_cache.get(text)
            if cached:
                return cached
            
            # Attempt translation
            translation = self.translator.translate(text, src=src, dest=dest)
            result = translation.text.lower()  # Convert to lowercase for consistency
            
            # Cache the result
            translation_cache.set(text, result)
            
            return result
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return None

class BoneRenamerProperties(PropertyGroup):
    source_object: StringProperty(
        name="Source Object",
        description="Armature to rename bones from",
        default=""
    )
    source_format: EnumProperty(
        items=BONE_MAPS,
        name="Source Format",
        description="Current bone naming format",
        default='mmd_japanese'
    )
    target_format: EnumProperty(
        items=BONE_MAPS,
        name="Target Format",
        description="Desired bone naming format",
        default='mmd_english'
    )
    include_fingers: BoolProperty(
        name="Include Fingers",
        description="Also rename finger bones",
        default=True
    )
    use_online_translation: BoolProperty(
        name="Use Online Translation",
        description="Use Google Translate for unknown Japanese terms (requires internet)",
        default=True
    )
    translation_timeout: FloatProperty(
        name="Translation Timeout",
        description="Seconds to wait for online translation before falling back to static dictionary",
        default=2.0,
        min=0.1,
        max=10.0
    )

def clean_bone_name(name: str) -> str:
    """Clean up bone names to be more Blender-friendly"""
    # Remove illegal characters and spaces
    cleaned = "".join(c for c in name if c.isalnum() or c in "._-")
    # Ensure name starts with a letter
    if cleaned and not cleaned[0].isalpha():
        cleaned = "bone_" + cleaned
    return cleaned

def extract_lr_suffix(name: str) -> Tuple[str, str]:
    """Extract left/right suffix from bone name"""
    for suffix in ['.L', '.R', '_L', '_R', '.l', '.r', '_l', '_r']:
        if name.endswith(suffix):
            return name[:-len(suffix)], suffix
    return name, ""

class ARMATURE_OT_rename_bones(Operator):
    bl_idname = "armature.rename_bones"
    bl_label = "Rename Bones"
    bl_description = "Rename bones from source format to target format"
    
    def execute(self, context):
        props = context.scene.bone_renamer
        
        # Get the armature
        armature = bpy.data.objects.get(props.source_object)
        if not armature:
            self.report({'ERROR'}, "Please select a valid armature!")
            return {'CANCELLED'}
        
        if props.source_format == 'mmd_japanese' and props.target_format == 'mmd_english':
            # Use the Japanese to English translation
            bpy.ops.armature.translate_jp_bones()
            return {'FINISHED'}
        
        # Otherwise use the original bone mapping logic
        try:
            renamed_count = self.rename_bones(
                armature, 
                props.source_format, 
                props.target_format, 
                props.include_fingers
            )
            self.report({'INFO'}, f"Successfully renamed {renamed_count} bones")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
    
    def rename_bones(self, armature, source_format: str, target_format: str, include_fingers: bool) -> int:
        # Find the indices in the original format lists
        format_mapping = {
            'mmd_english': 0,
            'xna_lara': 1,
            'daz_poser': 2,
            'blender_rigify': 3,
            'sims_2': 4,
            'motion_builder': 5,
            '3ds_max': 6,
            'type_x': 7,
            'bepu': 8,
            'mmd_japanese': 9,
            'mmd_japaneseLR': 10,
            'unknown': 11
        }
        
        source_idx = format_mapping[source_format]
        target_idx = format_mapping[target_format]
        
        bones = armature.data.bones
        renamed_count = 0
        
        # Perform the renaming
        mappings = [(BONE_NAMES, False), (FINGER_BONES, True)]
        for mapping_list, is_finger in mappings:
            if is_finger and not include_fingers:
                continue
                
            for mapping in mapping_list:
                source_name = mapping[source_idx]
                target_name = mapping[target_idx]
                
                if source_name and target_name and source_name in bones:
                    bones[source_name].name = target_name
                    renamed_count += 1
                    
        return renamed_count

class PICK_OT_armature(Operator):
    bl_idname = "armature.pick_source"
    bl_label = "Pick Armature"
    bl_description = "Pick the armature from the 3D viewport"
    
    def execute(self, context):
        if not context.active_object:
            show_message("No active object selected!", "Error", 'ERROR')
            return {'CANCELLED'}
            
        if context.active_object.type != 'ARMATURE':
            show_message("Selected object is not an armature!", "Error", 'ERROR')
            return {'CANCELLED'}
            
        context.scene.bone_renamer.source_object = context.active_object.name
        show_message(f"Selected armature: {context.active_object.name}", "Success", 'INFO')
        return {'FINISHED'}

class ARMATURE_OT_toggle_names(Operator):
    bl_idname = "armature.toggle_names"
    bl_label = "Toggle Names Display"
    bl_description = "Toggle visibility of bone names in viewport"
    
    def execute(self, context):
        show_names = None  # To track the first armature's state
        toggled_count = 0
        
        for obj in context.scene.objects:
            if obj.type == 'ARMATURE':
                if show_names is None:
                    # Use first armature's state to determine what to do
                    show_names = not obj.data.show_names
                
                obj.data.show_names = show_names
                toggled_count += 1
        
        if toggled_count > 0:
            state = "on" if show_names else "off"
            show_message(f"Turned bone names display {state} for {toggled_count} armatures", "Success", 'INFO')
        else:
            show_message("No armatures found in scene", "Info", 'INFO')
            
        return {'FINISHED'}

def translate_japanese_name(bone_name: str, use_online: bool = True, timeout: float = 2.0) -> str:
    """
    Translate Japanese bone name to English using multiple methods
    
    Args:
        bone_name (str): The bone name to translate
        use_online (bool): Whether to attempt online translation
        timeout (float): Maximum time to wait for online translation
        
    Returns:
        str: The translated bone name
    """
    base_name, suffix = extract_lr_suffix(bone_name)
    translated_name = base_name
    
    # Try online translation first if enabled
    if use_online and GOOGLE_TRANSLATE_AVAILABLE:
        try:
            translator = AsyncTranslator()
            translator.timeout = timeout
            online_translation = translator.translate_text(base_name)
            if online_translation:
                translated_name = online_translation
        except Exception as e:
            print(f"Online translation failed: {str(e)}")
    
    # Fallback to static dictionary if needed
    if translated_name == base_name:
        for jp, en in sorted(JP_BONE_MAPPING.items(), key=lambda x: len(x[0]), reverse=True):
            if jp in translated_name:
                translated_name = translated_name.replace(jp, en)
    
    # Clean up the translation
    translated_name = clean_bone_name(translated_name)
    
    # Reattach suffix if it existed
    if suffix:
        translated_name += suffix
    
    return translated_name

class ARMATURE_OT_translate_jp_bones(Operator):
    bl_idname = "armature.translate_jp_bones"
    bl_label = "Translate Japanese Names"
    bl_description = "Translate Japanese bone names to English"
    
    def execute(self, context):
        props = context.scene.bone_renamer
        
        # Get the armature
        armature = bpy.data.objects.get(props.source_object)
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select a valid armature!")
            return {'CANCELLED'}
        
        # Ensure we're in object mode
        if context.active_object and context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        # Perform the translation
        bones = armature.data.bones
        translated_count = 0
        skipped_count = 0
        online_count = 0
        fallback_count = 0
        
        # Create a list of bones to rename
        bones_to_rename = []
        for bone in bones:
            try:
                # Try online translation first if enabled
                new_name = translate_japanese_name(
                    bone.name,
                    use_online=props.use_online_translation,
                    timeout=props.translation_timeout
                )
                
                if new_name != bone.name:
                    bones_to_rename.append((bone, new_name))
                    if new_name != clean_bone_name(bone.name):  # If actual translation occurred
                        if props.use_online_translation and GOOGLE_TRANSLATE_AVAILABLE:
                            online_count += 1
                        else:
                            fallback_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                self.report({'WARNING'}, f"Failed to process {bone.name}: {str(e)}")
                skipped_count += 1
        
        # Perform the renaming
        for bone, new_name in bones_to_rename:
            try:
                bone.name = new_name
                translated_count += 1
            except Exception as e:
                self.report({'WARNING'}, f"Failed to rename {bone.name}: {str(e)}")
                skipped_count += 1
        
        # Create detailed success message
        if translated_count > 0:
            message = f"Successfully renamed {translated_count} bones:\n"
            if props.use_online_translation and GOOGLE_TRANSLATE_AVAILABLE:
                message += f"• {online_count} bones translated online\n"
                message += f"• {fallback_count} bones translated using dictionary"
            else:
                message += f"• {fallback_count} bones translated using dictionary"
            
            if skipped_count > 0:
                message += f"\n• {skipped_count} bones skipped (non-Japanese or errors)"
                
            self.report({'INFO'}, message)
            show_message(message, "Translation Complete", 'INFO')
        else:
            message = "No Japanese bone names found to translate"
            if skipped_count > 0:
                message += f"\n{skipped_count} bones were analyzed but didn't need translation"
            self.report({'INFO'}, message)
            show_message(message, "Translation Complete", 'INFO')
            
        return {'FINISHED'}

class VIEW3D_PT_bone_renamer(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'
    bl_label = "Bone Renamer"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.bone_renamer
        
        # Armature selection
        box = layout.box()
        box.label(text="Armature:")
        row = box.row(align=True)
        row.prop(props, "source_object", text="")
        row.operator("armature.pick_source", text="", icon='EYEDROPPER')
        
        # Translation options
        box = layout.box()
        box.label(text="Translation Options:")
        box.prop(props, "use_online_translation")
        if props.use_online_translation:
            box.prop(props, "translation_timeout")
        
        # Format selection
        box = layout.box()
        box.label(text="Formats:")
        box.prop(props, "source_format", text="From")
        box.prop(props, "target_format", text="To")
        
        # Options
        box = layout.box()
        box.label(text="Options:")
        box.prop(props, "include_fingers")
        
        # Action buttons
        col = layout.column(align=True)
        col.operator("armature.rename_bones", icon='OUTLINER_OB_ARMATURE')
        col.operator("armature.translate_jp_bones", icon='FILE_REFRESH')

classes = (
    BoneRenamerProperties,
    ARMATURE_OT_rename_bones,
    PICK_OT_armature,
    ARMATURE_OT_toggle_names,
    ARMATURE_OT_translate_jp_bones,
    VIEW3D_PT_bone_renamer
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.bone_renamer = bpy.props.PointerProperty(type=BoneRenamerProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.bone_renamer

if __name__ == "__main__":
    register()