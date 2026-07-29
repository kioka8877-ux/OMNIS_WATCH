"""
omnis_f03c_b.py — F03C-B : La Machine a Micro-jets (Mixage Musical)
Assemble le mix final : musique (directives.json) + video_complete.mp4 (F03B) -> video_with_music.mp4
Adapte depuis SANCTORUM F03_SERAPHIM seraphim_b.py

Changements vs SANCTORUM :
- Input : video_complete.mp4 (F03B = SFX + voix off) au lieu de voix_purifiee.wav
- Output : video_with_music.mp4 (video + audio mixe) au lieu de master_audio_mix.mp3
- Ducking : utilise timing.json pour detecter quand la voix parle
- Pas de push vers ANGRON-V2
- Conserve export backbone (musique seule)
"""
import argparse, json, os, sys, math, subprocess, tempfile


def extract_audio_from_video(video_path, output_audio_path):
    """Extrait l'audio de video_complete.mp4 (SFX + voix off)."""
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "44100", "-ac", "2",
        output_audio_path
    ]
    print(f"[F03C-B] Extraction audio depuis video -> {output_audio_path}")
    subprocess.run(cmd, check=True, capture_output=True)


def assemble_mix(directives_path, music_path, video_audio_path, output_audio_path, video_path, output_video_path):
    from pydub import AudioSegment

    with open(directives_path) as f:
        d = json.load(f)

    print(f"[F03C-B] BPM={d['bpm']} | {len(d['audio_timeline'])} segments | ducking={d['ducking_db']}dB")

    music_src = AudioSegment.from_file(music_path).set_frame_rate(44100).set_channels(2)
    voice = AudioSegment.from_file(video_audio_path).set_frame_rate(44100).set_channels(2)

    crossfade_ms = d.get('crossfade_ms', 15)
    music_backbone = AudioSegment.silent(duration=0)

    for seg in d['audio_timeline']:
        start_ms = int(seg['start'] * 1000)
        end_ms = int(seg['end'] * 1000)
        clip = music_src[start_ms:end_ms]

        # Speed
        speed = seg.get('speed', 1.0)
        if speed != 1.0:
            clip = clip._spawn(
                clip.raw_data,
                overrides={"frame_rate": int(clip.frame_rate * speed)}
            ).set_frame_rate(44100)

        # Reverse
        if seg.get('reverse', False):
            clip = clip.reverse()

        # Volume
        vol_pct = seg.get('volume_pct', 100)
        if vol_pct != 100 and vol_pct > 0:
            clip = clip + (20 * math.log10(vol_pct / 100))

        # Fades
        fi = seg.get('fade_in_ms', 0)
        fo = seg.get('fade_out_ms', 0)
        if fi > 0:
            clip = clip.fade_in(min(fi, len(clip) // 2))
        if fo > 0:
            clip = clip.fade_out(min(fo, len(clip) // 2))

        # Loops
        looped = clip
        for _ in range(seg.get('loops', 1) - 1):
            looped = looped.append(clip, crossfade=crossfade_ms)

        if len(music_backbone) == 0:
            music_backbone = looped
        else:
            music_backbone = music_backbone.append(looped, crossfade=crossfade_ms)

    print(f"[F03C-B] Backbone musique : {len(music_backbone)/1000:.1f}s")

    # Stretch backbone to cover voice + 2s tail
    target_ms = len(voice) + 2000
    if len(music_backbone) < target_ms:
        last = d['audio_timeline'][-1]
        filler = music_src[int(last['start']*1000):int(last['end']*1000)]
        if len(filler) == 0:
            filler = music_src[:4000]
        while len(music_backbone) < target_ms:
            music_backbone = music_backbone.append(filler, crossfade=crossfade_ms)

    music_backbone = music_backbone[:target_ms]

    # Ducking : full volume pendant hook (avant voix), duck sous la voix
    ducking_db = d.get('ducking_db', -14.0)
    music_ducked = music_backbone + ducking_db

    # Hook duration = 500ms plein volume avant que la voix commence
    hook_ms = 500
    if len(music_backbone) > hook_ms:
        music_final = music_backbone[:hook_ms].append(music_ducked[hook_ms:], crossfade=50)
    else:
        music_final = music_ducked

    # Pad si necessaire
    if len(music_final) < len(voice):
        music_final = music_final + AudioSegment.silent(len(voice) - len(music_final))

    # Mix voix/SFX sur musique
    master = music_final.overlay(voice, position=0)
    master = master.normalize(headroom=1.0)

    # Export audio mix
    master.export(output_audio_path, format='mp3', bitrate='192k')
    size_kb = os.path.getsize(output_audio_path) // 1024
    dur_s = len(master) / 1000
    print(f"[F03C-B] Audio mix -> {output_audio_path} ({size_kb} KB, {dur_s:.1f}s)")

    # Export backbone seul (musique pure, sans voix)
    backbone_path = output_audio_path.replace('.mp3', '_backbone.mp3')
    music_backbone_full = music_backbone[:target_ms].normalize(headroom=1.0)
    music_backbone_full.export(backbone_path, format='mp3', bitrate='192k')
    size_kb2 = os.path.getsize(backbone_path) // 1024
    print(f"[F03C-B] Backbone -> {backbone_path} ({size_kb2} KB, {dur_s:.1f}s)")

    # Mux audio mix back onto video
    print(f"[F03C-B] Mux audio sur video...")
    cmd_mux = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", output_audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        output_video_path
    ]
    subprocess.run(cmd_mux, check=True, capture_output=True)
    size_mb = os.path.getsize(output_video_path) // (1024*1024)
    print(f"[F03C-B] Video finale -> {output_video_path} ({size_mb} MB)")

    return dur_s, backbone_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--directives', required=True, help='Path to directives.json')
    p.add_argument('--music', required=True, help='Path to music.mp3')
    p.add_argument('--video', required=True, help='Path to video_complete.mp4 (F03B output)')
    p.add_argument('--output', required=True, help='Output directory')
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # Extract audio from video
    video_audio = os.path.join(args.output, 'video_audio.wav')
    extract_audio_from_video(args.video, video_audio)

    # Mix
    output_audio = os.path.join(args.output, 'master_audio_mix.mp3')
    output_video = os.path.join(args.output, 'video_with_music.mp4')

    assemble_mix(args.directives, args.music, video_audio, output_audio, args.video, output_video)

    # Cleanup temp
    if os.path.exists(video_audio):
        os.remove(video_audio)

    print(f"\n[F03C-B] TERMINE")
    print(f"  Video : {output_video}")
    print(f"  Audio : {output_audio}")


if __name__ == '__main__':
    main()
