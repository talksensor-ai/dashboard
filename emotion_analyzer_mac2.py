import os
import glob
import tempfile
import warnings
import soundfile as sf
import torchaudio

warnings.filterwarnings("ignore")

os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"

_emo_model = None

def _get_emo_model():
    global _emo_model
    if _emo_model is None:
        import gigaam
        import torch
        device = "cpu"
        print(f"[EMO] Загрузка GigaAM-Emo (устройство: {device})...")
        _emo_model = gigaam.load_model("emo", device=device)
        print("[EMO] GigaAM-Emo загружена!")
    return _emo_model

def get_emotion_score(global_start, global_end, date_folder, root_path="/Users/ai/talk"):
    target_dir = root_path
    
    # Looking for .ogg files in the directory
    ogg_files = glob.glob(os.path.join(target_dir, f"{date_folder}_*.ogg"))
    if not ogg_files:
        ogg_files = glob.glob(os.path.join(target_dir, "*.ogg"))
        
    if not ogg_files:
        print(f"[EMO] Не найдено .ogg файлов в {target_dir}")
        return {"error": "no audio files"}, None

    file_shifts = []
    for f in ogg_files:
        basename = os.path.basename(f)
        clean_name = basename
        if '_' in basename:
            clean_name = basename.split('_', 1)[1]
            
        parts = clean_name.split('-')
        try:
            h = int(parts[0])
            m = int(parts[1])
            shift_s = h * 3600 + m * 60
            file_shifts.append((shift_s, f))
        except:
            continue
            
    file_shifts.sort(key=lambda x: x[0])
    
    if not file_shifts:
        file_shifts = [(0, ogg_files[0])]

    # Normalize shifts so the first file is at t=0
    base_shift = file_shifts[0][0]
    normalized_shifts = [(s - base_shift, f) for s, f in file_shifts]

    target_file = None
    local_start = global_start
    local_end = global_end
    
    for i in range(len(normalized_shifts)-1, -1, -1):
        shift, fpath = normalized_shifts[i]
        if global_start >= shift:
            target_file = fpath
            local_start = global_start - shift
            local_end = global_end - shift
            break
            
    if not target_file:
        target_file = normalized_shifts[0][1]
        local_start = max(0, global_start)
        local_end = max(1, global_end)
        
    print(f"[EMO] Глобальный {global_start}-{global_end} -> Локальный {local_start}-{local_end} в {os.path.basename(target_file)}")
    
    try:
        waveform, sr = torchaudio.load(target_file)
        start_idx = int(local_start * sr)
        end_idx = int(local_end * sr)
        
        start_idx = max(0, min(start_idx, waveform.shape[1] - 1))
        end_idx = max(start_idx + 1, min(end_idx, waveform.shape[1]))
        
        audio_chunk = waveform[:, start_idx:end_idx]
        
        fd, tmp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        sf.write(tmp_path, audio_chunk[0].numpy(), sr)
        
        try:
            import torch
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception:
            pass

        model = _get_emo_model()
        probs = model.get_probs(tmp_path)
        
        return probs, tmp_path

    except Exception as e:
        print(f"[EMO] Ошибка: {e}")
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            return {"error": str(e)}, tmp_path
        return {"error": str(e)}, None

def analyze_emotion_and_tag(global_start, global_end, date_folder, root_path):
    probs, audio_path = get_emotion_score(global_start, global_end, date_folder, root_path)
    if not probs or "error" in probs:
        return "[ЭМОЦИИ: ОШИБКА]", False, audio_path
        
    angry = probs.get("angry", 0)
    tag_text = f"[ЭМОЦИИ: angry={angry:.2f}, neutral={probs.get('neutral',0):.2f}, positive={probs.get('positive',0):.2f}, sad={probs.get('sad',0):.2f}]"
    is_conflict = angry > 0.35
    
    if is_conflict:
        tag_text += " [КОНФЛИКТ]"
        
    return tag_text, is_conflict, audio_path
