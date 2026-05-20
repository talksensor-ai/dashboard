import os
import time
import datetime
import re
import yadisk
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Добавляем путь к Homebrew bin для Mac
os.environ["PATH"] = os.environ.get("PATH", "") + ":/opt/homebrew/bin"

# HF_TOKEN для pyannote VAD внутри GigaAM longform
os.environ["HF_TOKEN"] = os.environ.get("HF_TOKEN", "")

# --- Кэш модели (загружается один раз на весь процесс) ---
_gigaam_model = None
_gigaam_device = None

def _get_model():
    """Возвращает уже загруженную модель GigaAM или загружает её первый раз."""
    global _gigaam_model, _gigaam_device
    if _gigaam_model is None:
        import gigaam
        import torch
        _gigaam_device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        print(f"\n--- Загрузка GigaAM v3_e2e_rnnt (устройство: {_gigaam_device}) ---")
        _gigaam_model = gigaam.load_model("v3_e2e_rnnt", device=_gigaam_device)
        print("Модель загружена!")
    return _gigaam_model

def run_gigaam(audio_path, output_txt="audit_dialogues.txt"):
    """Транскрипция через GigaAM v3 (RNNT) с word-level timestamps.
    Модель кэшируется в памяти и НЕ перезагружается между файлами.
    Настройки нарезки: чанк 30с, шаг 24с (6с перекрытие) → ~150 вызовов на час аудио.
    """
    if not os.path.exists(audio_path):
        print(f"Файл {audio_path} не найден.")
        return

    import torchaudio
    import tempfile
    import soundfile as sf
    import numpy as np

    model = _get_model()

    start_time = time.time()
    print(f"\n--- Транскрипция: {audio_path} ---")
    
    # Загружаем аудио
    waveform, sr = torchaudio.load(audio_path)
    if sr != 16000:
        waveform = torchaudio.functional.resample(waveform, sr, 16000)
        sr = 16000
    
    audio_np = waveform[0].numpy()
    total_duration = len(audio_np) / sr
    
    # Настройки нарезки: чанк 30с, шаг 24с (6с перекрытие)
    # Было: 24с/18с → ~200 вызовов на час. Стало: 30с/24с → ~150 вызовов (-25%)
    chunk_len_sec = 30.0
    step_sec = 24.0

    all_words = []

    n_chunks = int(total_duration / step_sec) + 1
    print(f"Длительность: {total_duration:.0f}с | Чанк: {chunk_len_sec}с | Шаг: {step_sec}с | Чанков: ~{n_chunks}")
    
    # Временный файл для чанков
    fd, tmp_path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    
    try:
        current_step = 0.0
        while current_step < total_duration:
            chunk_start = current_step
            chunk_end = min(chunk_start + chunk_len_sec, total_duration)
            
            # Core window for deduplication
            core_start = chunk_start
            core_end = min(chunk_start + step_sec, total_duration)
            
            s_idx = int(chunk_start * sr)
            e_idx = int(chunk_end * sr)
            chunk = audio_np[s_idx:e_idx]
            
            sf.write(tmp_path, chunk, sr)
            
            try:
                result = model.transcribe(tmp_path, word_timestamps=True)
                if result.words:
                    for w in result.words:
                        abs_start = chunk_start + w.start
                        abs_end = chunk_start + w.end
                        midpoint = (abs_start + abs_end) / 2.0
                        
                        # Keep word only if its midpoint is within the core window
                        if core_start <= midpoint < core_end:
                            all_words.append((abs_start, abs_end, w.text))
            except Exception as e:
                import traceback
                print(f"Ошибка при транскрипции чанка {chunk_start}-{chunk_end}: {e}")
                traceback.print_exc()
                
            current_step += step_sec
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Сортируем слова по времени
    all_words.sort(key=lambda x: x[0])

    # Нарезаем по фразам (по знакам препинания или паузам > 2 сек)
    lines = []
    current_words = []
    current_start = None
    last_word_end = None

    for w_start, w_end, w_text in all_words:
        if current_start is None:
            current_start = w_start
            
        # Если пауза между словами > 2 секунд, разбиваем фразу
        if last_word_end is not None and (w_start - last_word_end) > 2.0:
            lines.append((current_start, last_word_end, " ".join(current_words)))
            current_words = [w_text]
            current_start = w_start
        else:
            current_words.append(w_text)
            
        last_word_end = w_end
        
        is_sentence_end = w_text.rstrip().endswith(('.', '?', '!'))
        if is_sentence_end:
            lines.append((current_start, last_word_end, " ".join(current_words)))
            current_words = []
            current_start = None
            last_word_end = None

    if current_words:
        lines.append((current_start, last_word_end, " ".join(current_words)))

    # Записываем результат
    full_text_blocks = []
    with open(output_txt, 'w', encoding='utf-8') as f_out:
        f_out.write(f"Анализ файла: {audio_path} (GigaAM Слепая нарезка)\n")
        f_out.write("=" * 40 + "\n\n")

        print("\n=== ВЫВОД ТЕКСТА ===")
        for line_start, line_end, text in lines:
            if text.strip():
                s = int(line_start)
                e = int(line_end) + 1
                line = f"[{s} - {e}] {text}"
                print(line)
                full_text_blocks.append(line)
                f_out.write(line + "\n")
                f_out.flush()

    exec_time = time.time() - start_time
    print(f"\n[+] Транскрипция завершена за {exec_time:.1f} сек! ({len(lines)} строк)")
    print(f"[+] Сырой текст сохранен в: {output_txt}")
    return "\n".join(full_text_blocks)


