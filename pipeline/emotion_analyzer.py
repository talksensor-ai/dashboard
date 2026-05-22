import os
import glob
import tempfile
import warnings
import soundfile as sf
import torchaudio

warnings.filterwarnings("ignore")

# Добавляем Homebrew bin в PATH чтобы ffmpeg находился
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"

# Кэш модели GigaAM-Emo (загружается один раз)
_emo_model = None

def _get_emo_model():
    global _emo_model
    if _emo_model is None:
        import gigaam
        import torch
        device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[EMO] Загрузка GigaAM-Emo (устройство: {device})...")
        _emo_model = gigaam.load_model("emo", device=device)
        print("[EMO] GigaAM-Emo загружена!")
    return _emo_model


def get_emotion_score(global_start, global_end, date_folder, root_path="/root/talk/test_compare"):
    """
    Finds the right audio snippet for the global timestamps and gets its emotion probabilities.
    
    global_start: e.g. 52250 (seconds from midnight)
    global_end: e.g. 52270
    date_folder: "2026-04-27"
    root_path: path where the .ogg files are stored locally
    """

    import gigaam
    
    # 1. Find all local .ogg files for this date
    # In reality, they are named e.g., "19-00-27-04-2026.ogg"
    # But daily_cache_worker assumes format 'HH-MM-SS.ogg' or '19-00-27-04-2026.ogg'
    # We'll just look for files in root_path/date_folder or root_path
    
    # For testing on a single file:
    # If the user only gave us 1 file, let's just use it directly.
    # We will build a robust mapping based on the files present.
    
    target_dir = os.path.join(root_path, date_folder)
    if not os.path.exists(target_dir):
        # Fallback to root_path
        target_dir = root_path

    ogg_files = glob.glob(os.path.join(target_dir, "*.ogg"))
    
    if not ogg_files:
        print(f"[EMO] Не найдено .ogg файлов в {target_dir}")
        return {"error": "no audio files"}

    # Calculate shift for each file
    file_shifts = []
    for f in ogg_files:
        basename = os.path.basename(f)
        # Strip date prefix if present (e.g. 2026-04-25_09-00...)
        clean_name = basename
        if '_' in basename:
            clean_name = basename.split('_', 1)[1]
            
        parts = clean_name.split('-')
        try:
            h = int(parts[0])
            m = int(parts[1])
            # In the format HH-MM-DD-MM-YYYY, there are no seconds.
            shift_s = h * 3600 + m * 60
            file_shifts.append((shift_s, f))
        except:
            continue
            
    file_shifts.sort(key=lambda x: x[0])
    
    if not file_shifts:
        # If parsing failed, just use the first file and assume 0 shift
        file_shifts = [(0, ogg_files[0])]
    else:
        # Normalize shifts relative to the first file of the day
        first_file_shift = file_shifts[0][0]
        file_shifts = [(shift - first_file_shift, fpath) for shift, fpath in file_shifts]

    # Find the right file
    target_file = None
    local_start = global_start
    local_end = global_end
    
    for i in range(len(file_shifts)-1, -1, -1):
        shift, fpath = file_shifts[i]
        if global_start >= shift:
            target_file = fpath
            local_start = global_start - shift
            local_end = global_end - shift
            break
            
    if not target_file:
        target_file = file_shifts[0][1]
        local_start = max(0, global_start - file_shifts[0][0])
        local_end = max(1, global_end - file_shifts[0][0])
        
    print(f"[EMO] Глобальный {global_start}-{global_end} -> Локальный {local_start}-{local_end} в {os.path.basename(target_file)}")
    
    try:
        waveform, sr = torchaudio.load(target_file)
        if sr != 16000:
            waveform = torchaudio.functional.resample(waveform, sr, 16000)
            sr = 16000
            
        duration = local_end - local_start
        chunk_size = 30.0
        
        if duration <= chunk_size:
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
        else:
            # Chunk the audio into 30-second segments
            chunks = []
            t = local_start
            while t < local_end:
                chunks.append((t, min(t + chunk_size, local_end)))
                t += chunk_size
                
            all_probs = []
            last_tmp_path = None
            
            for chunk_start, chunk_end in chunks:
                chunk_start_idx = int(chunk_start * sr)
                chunk_end_idx = int(chunk_end * sr)
                
                chunk_start_idx = max(0, min(chunk_start_idx, waveform.shape[1] - 1))
                chunk_end_idx = max(chunk_start_idx + 1, min(chunk_end_idx, waveform.shape[1]))
                
                audio_chunk = waveform[:, chunk_start_idx:chunk_end_idx]
                
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
                all_probs.append(probs)
                
                if last_tmp_path and os.path.exists(last_tmp_path):
                    try:
                        os.remove(last_tmp_path)
                    except Exception:
                        pass
                last_tmp_path = tmp_path
                
            combined_probs = {"angry": 0.0, "neutral": 0.0, "positive": 0.0, "sad": 0.0}
            if all_probs:
                combined_probs["angry"] = max(p.get("angry", 0.0) for p in all_probs)
                combined_probs["sad"] = max(p.get("sad", 0.0) for p in all_probs)
                combined_probs["neutral"] = sum(p.get("neutral", 0.0) for p in all_probs) / len(all_probs)
                combined_probs["positive"] = sum(p.get("positive", 0.0) for p in all_probs) / len(all_probs)
                
            return combined_probs, last_tmp_path


        
    except Exception as e:
        print(f"[EMO] Ошибка: {e}")
        return {"error": str(e)}, None

def analyze_emotion_and_tag(global_start, global_end, date_folder, root_path):
    probs, audio_path = get_emotion_score(global_start, global_end, date_folder, root_path)
    if "error" in probs:
        return "[ЭМОЦИИ: ОШИБКА]", False, None
        
    angry = probs.get("angry", 0)
    tag_text = f"[ЭМОЦИИ: angry={angry:.2f}, neutral={probs.get('neutral',0):.2f}, positive={probs.get('positive',0):.2f}, sad={probs.get('sad',0):.2f}]"
    is_conflict = angry > 0.35
    
    if is_conflict:
        tag_text += " [КОНФЛИКТ]"
        
    return tag_text, is_conflict, audio_path
