from pydub import AudioSegment


def convert_audio_format(input_path: str, output_path: str, output_format: str):
    """
    Convert an audio file to another format.

    Args:
        input_path (str): Path to the input audio file.
        output_path (str): Path to the output audio file.
        output_format (str): Desired output format (e.g., 'mp3', 'wav').
    """
    # Supported audio encoding options (used with FFmpeg):
    # - pcm_s16le: Signed 16-bit PCM
    # - pcm_u8: Unsigned 8-bit PCM
    # - pcm_s24le: Signed 24-bit PCM
    # - pcm_s32le: Signed 32-bit PCM
    # - aac: Advanced Audio Codec
    # - mp3: MPEG Layer 3
    # - vorbis: Vorbis (used in ogg)
    # - flac: Free Lossless Audio Codec
    # - opus: Opus Codec
    # - alac: Apple Lossless Audio Codec
    # - wav: Waveform Audio File Format
    # - ac3: Dolby Digital Audio Codec
    # - eac3: Enhanced AC-3
    # - dts: Digital Theater Systems Codec
    # - amr_nb: Adaptive Multi-Rate (Narrowband)
    # - amr_wb: Adaptive Multi-Rate (Wideband)
    # - wma: Windows Media Audio
    # - gsm: GSM Full Rate (GSM 06.10 codec)

    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format=output_format)
    print(f"Audio file converted to {output_format} format and saved at {output_path}")


def edit_audio_properties(input_path: str, output_path: str, volume_change_db: float = 0, bitrate: str = None,
                          sample_rate: int = None, encoding: str = None):
    """
    Edit properties of an audio file, such as volume, bitrate, or sampling rate.

    Args:
        input_path (str): Path to the input audio file.
        output_path (str): Path to save the edited audio file.
        volume_change_db (float): Increase/decrease volume in decibels (default: 0).
        bitrate (str): Desired bitrate of the output file (e.g., '192k').
        sample_rate (int): Desired sampling rate in Hz (optional).
        encoding (str): Desired audio encoding (e.g., 'pcm_s16le').
    """
    audio = AudioSegment.from_file(input_path)

    # Adjust volume
    if volume_change_db:
        audio = audio + volume_change_db

    # Export with optional encoding and sample rate
    export_params = {'format': output_path.split('.')[-1]}
    if bitrate:
        export_params['bitrate'] = bitrate
    if sample_rate:
        export_params['parameters'] = ['-ar', str(sample_rate)]
    if encoding:
        if 'parameters' not in export_params:
            export_params['parameters'] = []
        export_params['parameters'].extend(['-acodec', encoding])

    audio.export(output_path, **export_params)
    print(f"Edited audio saved at {output_path}")


if __name__ == "__main__":
    # Example usage
    # Convert audio format
    # convert_audio_format("input.wav", "output.mp3", "mp3")

    # Edit audio properties
    edit_audio_properties("input.mp3", "output_edited.wav", encoding="pcm_u8", sample_rate=48000)
