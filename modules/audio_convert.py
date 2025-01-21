import subprocess

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

def convert_audio_format(input_path: str, output_path: str, output_format: str):
    """
    Convert an audio file to another format using subprocess and FFmpeg.
    Args:
        input_path (str): Path to the input audio file.
        output_path (str): Path to the output audio file.
        output_format (str): Desired output format (e.g., 'mp3', 'wav').
    """
    try:
        # Construct the ffmpeg command
        command = f"ffmpeg -i \"{input_path}\" \"{output_path}\""
        subprocess.run(command, shell=True, check=True)
        print(f"Audio file converted to {output_format} format and saved at {output_path}")
    except subprocess.CalledProcessError as e:
        raise


def edit_audio_properties(input_path: str, output_path: str, volume_change_db: float = 0, bitrate: str = None,
                          sample_rate: int = None, encoding: str = None):
    """
    Edit properties of an audio file, such as volume, bitrate, or sampling rate using subprocess and FFmpeg.
    Args:
        input_path (str): Path to the input audio file.
        output_path (str): Path to save the edited audio file.
        volume_change_db (float): Increase/decrease volume in decibels (default: 0).
        bitrate (str): Desired bitrate of the output file (e.g., '192k').
        sample_rate (int): Desired sampling rate in Hz (optional).
        encoding (str): Desired audio encoding (e.g., 'pcm_s16le').
    """
    try:
        # Base ffmpeg command
        command = f"ffmpeg -y -i \"{input_path}\""

        # Apply volume change if specified
        if volume_change_db:
            command += f" -filter:a \"volume={volume_change_db}dB\""

        # Apply sample rate if specified
        if sample_rate:
            command += f" -ar {sample_rate}"

        # Apply encoding if specified
        if encoding:
            command += f" -c:a {encoding}"

        # Apply bitrate if specified
        if bitrate:
            command += f" -b:a {bitrate}"

        # Specify the output path
        command += f" \"{output_path}\""

        # Run the command
        subprocess.run(command, shell=True, check=True)
        print(f"Edited audio saved at {output_path}")
    except subprocess.CalledProcessError as e:
        raise
